#!/usr/bin/env python3
"""
Wireless MQTT FOTA (Firmware Over-The-Air) & Remote UF2 Bootloader Tool
for presence-sensor-nrf (nRF52840 + OpenThread + Home Assistant MQTT).

Reads MQTT broker IP, port, username, and password automatically from `local.conf`
(or CLI flags / environment variables) with zero hardcoded credentials.

Examples:
  # Push compiled firmware (build/zephyr/zephyr.bin or build/zephyr/zephyr.uf2) over Thread/MQTT:
  ./scripts/push-ota.py presence_70ed

  # Check running firmware version & FOTA readiness over MQTT:
  ./scripts/push-ota.py presence_70ed --ping

  # Remotely reboot an USB-connected sensor into the NICENANO UF2 mass-storage bootloader
  # without opening the enclosure or double-tapping reset:
  ./scripts/push-ota.py presence_70ed --bootloader
"""

import argparse
import json
import os
import pathlib
import re
import select
import socket
import struct
import sys
import time
import zlib
from typing import Dict, Optional, Tuple

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
SLOT0_BASE_ADDR = 0x00001000
CHUNK_SIZE = 256


def parse_local_conf(conf_path: pathlib.Path) -> Dict[str, str]:
    """Parse Kconfig key=value settings from local.conf."""
    settings: Dict[str, str] = {}
    if not conf_path.is_file():
        return settings
    for raw_line in conf_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.strip()
        if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        settings[key.strip()] = val
    return settings


def extract_firmware_bytes(fw_path: pathlib.Path) -> bytes:
    """Load raw Slot 0 binary from either zephyr.bin or zephyr.uf2."""
    raw = fw_path.read_bytes()
    if fw_path.suffix.lower() != ".uf2":
        return raw

    if len(raw) % 512 != 0:
        raise ValueError(f"Invalid UF2 file length ({len(raw)} bytes)")

    blocks: Dict[int, bytes] = {}
    for offset in range(0, len(raw), 512):
        block = raw[offset : offset + 512]
        magic0, magic1, flags, target_addr, payload_size = struct.unpack_from("<IIIII", block, 0)
        (magic_end,) = struct.unpack_from("<I", block, 508)
        if magic0 != UF2_MAGIC_START0 or magic1 != UF2_MAGIC_START1 or magic_end != UF2_MAGIC_END:
            continue
        if (flags & 0x00001000) != 0 or payload_size == 0 or payload_size > 476:
            continue
        if target_addr >= SLOT0_BASE_ADDR:
            blocks[target_addr] = block[32 : 32 + payload_size]

    if not blocks:
        raise ValueError(f"No valid Slot 0 blocks found in {fw_path}")

    min_addr = min(blocks.keys())
    max_addr = max(addr + len(data) for addr, data in blocks.items())
    out = bytearray(b"\xFF" * (max_addr - min_addr))
    for addr, data in blocks.items():
        rel = addr - min_addr
        out[rel : rel + len(data)] = data
    return bytes(out)


class MiniMqttClient:
    """Zero-dependency MQTT v3.1.1 TCP client using Python standard library sockets."""

    def __init__(self, host: str, port: int, username: str = "", password: str = "") -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sock: Optional[socket.socket] = None
        self.rx_buf = bytearray()
        self.next_pkt_id = 1

    @staticmethod
    def _encode_varlen(length: int) -> bytes:
        out = bytearray()
        while True:
            digit = length % 128
            length //= 128
            if length > 0:
                digit |= 0x80
            out.append(digit)
            if length == 0:
                break
        return bytes(out)

    @staticmethod
    def _encode_utf8(s: str) -> bytes:
        b = s.encode("utf-8")
        return struct.pack("!H", len(b)) + b

    def connect(self, client_id: str, keepalive: int = 30) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=5.0)
        flags = 0x02  # Clean Session
        payload = self._encode_utf8(client_id)
        if self.username:
            flags |= 0x80
            payload += self._encode_utf8(self.username)
        if self.password:
            flags |= 0x40
            payload += self._encode_utf8(self.password)

        var_hdr = self._encode_utf8("MQTT") + struct.pack("!BBH", 4, flags, keepalive)
        rem = var_hdr + payload
        pkt = bytes([0x10]) + self._encode_varlen(len(rem)) + rem
        self.sock.sendall(pkt)

        pkt_type, body = self._read_packet(timeout=5.0)
        if pkt_type != 0x20 or len(body) < 2 or body[1] != 0:
            code = body[1] if len(body) >= 2 else -1
            raise RuntimeError(f"MQTT CONNACK failed (code={code})")

    def subscribe(self, topic: str) -> None:
        assert self.sock is not None
        pkt_id = self.next_pkt_id
        self.next_pkt_id = (self.next_pkt_id % 65535) + 1
        rem = struct.pack("!H", pkt_id) + self._encode_utf8(topic) + bytes([0x00])
        pkt = bytes([0x82]) + self._encode_varlen(len(rem)) + rem
        self.sock.sendall(pkt)

    def publish(self, topic: str, payload: bytes) -> None:
        assert self.sock is not None
        rem = self._encode_utf8(topic) + payload
        pkt = bytes([0x30]) + self._encode_varlen(len(rem)) + rem
        self.sock.sendall(pkt)

    def _read_packet(self, timeout: float) -> Tuple[int, bytes]:
        assert self.sock is not None
        deadline = time.monotonic() + timeout
        while True:
            if len(self.rx_buf) >= 2:
                mult = 1
                rem_len = 0
                idx = 1
                complete_len = False
                while idx < len(self.rx_buf):
                    encoded = self.rx_buf[idx]
                    rem_len += (encoded & 0x7F) * mult
                    idx += 1
                    if (encoded & 0x80) == 0:
                        complete_len = True
                        break
                    mult *= 128
                if complete_len and len(self.rx_buf) >= idx + rem_len:
                    pkt_type = self.rx_buf[0] & 0xF0
                    body = bytes(self.rx_buf[idx : idx + rem_len])
                    del self.rx_buf[: idx + rem_len]
                    return pkt_type, body

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for MQTT packet")
            rlist, _, _ = select.select([self.sock], [], [], min(remaining, 0.25))
            if rlist:
                chunk = self.sock.recv(4096)
                if not chunk:
                    raise ConnectionError("MQTT socket closed by broker")
                self.rx_buf.extend(chunk)

    def wait_for_publish(self, expected_topic: str, timeout: float) -> Optional[bytes]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rem = max(0.05, deadline - time.monotonic())
            try:
                pkt_type, body = self._read_packet(timeout=rem)
            except TimeoutError:
                return None
            if pkt_type == 0x30 and len(body) >= 2:
                (tlen,) = struct.unpack_from("!H", body, 0)
                if len(body) >= 2 + tlen:
                    topic = body[2 : 2 + tlen].decode("utf-8", errors="replace")
                    payload = body[2 + tlen :]
                    if topic == expected_topic:
                        return payload
        return None

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.sendall(bytes([0xE0, 0x00]))
            except OSError:
                pass
            self.sock.close()
            self.sock = None


def wait_status_json(client: MiniMqttClient, status_topic: str, timeout: float) -> Optional[ dict ]:
    raw = client.wait_for_publish(status_topic, timeout=timeout)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    local_conf = parse_local_conf(repo_root / "local.conf")

    parser = argparse.ArgumentParser(description="Push wireless MQTT FOTA update to presence-sensor-nrf")
    parser.add_argument("node_slug", help="Device node slug (e.g. presence_70ed)")
    parser.add_argument(
        "--firmware",
        default=str(repo_root / "build" / "zephyr" / "zephyr.bin"),
        help="Path to zephyr.bin or zephyr.uf2 (default: build/zephyr/zephyr.bin)",
    )
    parser.add_argument("--ping", action="store_true", help="Only query current firmware version & FOTA status")
    parser.add_argument(
        "--bootloader",
        action="store_true",
        help="Remotely reboot into the Adafruit UF2 bootloader (GPREGRET=0x57)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MQTT_HOST", local_conf.get("CONFIG_APP_MQTT_BROKER_IPV4", "")),
        help="MQTT broker host/IP (defaults to CONFIG_APP_MQTT_BROKER_IPV4 in local.conf)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MQTT_PORT", local_conf.get("CONFIG_APP_MQTT_BROKER_PORT", "1883"))),
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("MQTT_USERNAME", local_conf.get("CONFIG_APP_MQTT_USERNAME", "")),
        help="MQTT username (defaults to CONFIG_APP_MQTT_USERNAME in local.conf)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("MQTT_PASSWORD", local_conf.get("CONFIG_APP_MQTT_PASSWORD", "")),
        help="MQTT password (defaults to CONFIG_APP_MQTT_PASSWORD in local.conf)",
    )
    args = parser.parse_args()

    if not args.host:
        print("ERROR: MQTT broker host not specified and local.conf not found.", file=sys.stderr)
        return 1

    slug = args.node_slug.strip().lower().replace("-", "_")
    cmd_topic = f"presence_sensor/{slug}/ota/cmd"
    chunk_topic = f"presence_sensor/{slug}/ota/chunk"
    status_topic = f"presence_sensor/{slug}/ota/status"

    client = MiniMqttClient(args.host, args.port, args.username, args.password)
    client.connect(client_id=f"ota_pusher_{os.getpid() & 0xFFFF:04x}")
    client.subscribe(status_topic)

    try:
        if args.ping:
            client.publish(cmd_topic, b'{"action":"ping"}')
            resp = wait_status_json(client, status_topic, timeout=6.0)
            if not resp:
                print(f"ERROR: No response from {slug} on {status_topic}", file=sys.stderr)
                return 1
            print(f"[{slug}] {json.dumps(resp)}")
            return 0

        if args.bootloader:
            print(f"Triggering remote UF2 bootloader on {slug} via {cmd_topic}...")
            client.publish(cmd_topic, b'{"action":"bootloader"}')
            resp = wait_status_json(client, status_topic, timeout=6.0)
            if resp:
                print(f"[{slug}] {json.dumps(resp)}")
            print("Done! The NICENANO USB drive will mount in ~1-2 seconds.")
            return 0

        fw_path = pathlib.Path(args.firmware)
        if not fw_path.is_file():
            print(f"ERROR: Firmware file not found: {fw_path}", file=sys.stderr)
            return 1

        fw_bytes = extract_firmware_bytes(fw_path)
        fw_size = len(fw_bytes)
        fw_crc32 = zlib.crc32(fw_bytes) & 0xFFFFFFFF

        print(f"Target device : {slug}")
        print(f"Firmware image: {fw_path} ({fw_size} bytes, CRC32=0x{fw_crc32:08X})")

        # 1. Begin FOTA session
        begin_cmd = json.dumps({"action": "begin", "size": fw_size, "crc32": fw_crc32}).encode("utf-8")
        ready = False
        for attempt in range(4):
            client.publish(cmd_topic, begin_cmd)
            resp = wait_status_json(client, status_topic, timeout=4.0)
            if resp and resp.get("state") == "ready":
                ready = True
                break
            if resp and resp.get("state") == "error":
                print(f"ERROR from device on begin: {resp}", file=sys.stderr)
                return 1
        if not ready:
            print(f"ERROR: Device {slug} did not acknowledge FOTA begin command.", file=sys.stderr)
            return 1

        # 2. Stream binary chunks with per-chunk ACK + automatic retry
        offset = 0
        t_start = time.monotonic()
        while offset < fw_size:
            piece = fw_bytes[offset : offset + CHUNK_SIZE]
            pkt = struct.pack("<I", offset) + piece
            acked = False
            for retry in range(6):
                client.publish(chunk_topic, pkt)
                resp = wait_status_json(client, status_topic, timeout=2.5)
                if not resp:
                    continue
                if resp.get("state") == "error":
                    print(f"\nERROR from device at offset {offset}: {resp}", file=sys.stderr)
                    return 1
                if resp.get("state") == "ack":
                    dev_offset = int(resp.get("offset", 0))
                    if dev_offset == offset + len(piece):
                        offset = dev_offset
                        acked = True
                        break
                    elif dev_offset <= fw_size:
                        offset = dev_offset
                        acked = True
                        break
            if not acked:
                print(f"\nERROR: Timed out waiting for chunk ACK at offset {offset}", file=sys.stderr)
                return 1

            elapsed = max(0.001, time.monotonic() - t_start)
            rate_kbps = (offset / 1024.0) / elapsed
            pct = (offset * 100.0) / fw_size
            sys.stdout.write(f"\rStaging slot1: {offset}/{fw_size} bytes ({pct:5.1f}%) [{rate_kbps:4.1f} KB/s]")
            sys.stdout.flush()

        print("\nStaging complete! Verifying CRC-32 and applying update from SRAM...")

        # 3. Apply staged firmware
        client.publish(cmd_topic, b'{"action":"apply"}')
        resp = wait_status_json(client, status_topic, timeout=6.0)
        if resp:
            if resp.get("state") == "error":
                print(f"ERROR during apply: {resp}", file=sys.stderr)
                return 1
            print(f"[{slug}] {json.dumps(resp)}")

        print(f"FOTA update applied! Waiting for {slug} to reboot onto new firmware...")
        time.sleep(5.0)
        for _ in range(6):
            client.publish(cmd_topic, b'{"action":"ping"}')
            pong = wait_status_json(client, status_topic, timeout=3.0)
            if pong:
                print(f"[{slug}] Online after FOTA reboot: {json.dumps(pong)}")
                return 0
        print(f"FOTA apply succeeded ({slug} is reattaching to OpenThread).")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
