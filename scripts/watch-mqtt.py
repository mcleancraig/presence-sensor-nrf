#!/usr/bin/env python3
"""
Live MQTT stream viewer for presence-sensor-nrf.
Reads broker host/port/credentials from gitignored local.conf (zero hardcoded secrets)
and streams timestamped messages for presence_sensor/<node_id>/# (default: presence_70ed).
"""

import datetime
import json
import os
import re
import socket
import struct
import sys
import time


def load_local_conf(path: str) -> dict:
    conf = {}
    if not os.path.exists(path):
        return conf
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            m_str = re.match(r'^(CONFIG_\w+)="(.*)"$', line)
            if m_str:
                conf[m_str.group(1)] = m_str.group(2)
                continue
            m_int = re.match(r"^(CONFIG_\w+)=(\d+)$", line)
            if m_int:
                conf[m_int.group(1)] = int(m_int.group(2))
    return conf


def enc_str(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("!H", len(b)) + b


def enc_len(length: int) -> bytes:
    out = bytearray()
    while True:
        eb = length % 128
        length //= 128
        if length > 0:
            eb |= 0x80
        out.append(eb)
        if length == 0:
            break
    return bytes(out)


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conf = load_local_conf(os.path.join(repo_root, "local.conf"))

    host = str(conf.get("CONFIG_APP_MQTT_BROKER_IPV4", "192.168.41.250"))
    port = int(conf.get("CONFIG_APP_MQTT_BROKER_PORT", 1883))
    user = str(conf.get("CONFIG_APP_MQTT_USERNAME", ""))
    pw = str(conf.get("CONFIG_APP_MQTT_PASSWORD", ""))

    node_filter = sys.argv[1] if len(sys.argv) > 1 else "presence_70ed"
    topic_filter = (
        f"presence_sensor/{node_filter}/#"
        if "/" not in node_filter and node_filter != "all"
        else ("presence_sensor/#" if node_filter == "all" else node_filter)
    )

    keepalive_s = 30
    client_id = f"watch_mqtt_{os.getpid()}"

    print(f"Connecting to MQTT broker {host}:{port} ...", flush=True)
    s = socket.create_connection((host, port), timeout=10.0)

    flags = 0x02  # Clean session
    payload = enc_str(client_id)
    if user:
        flags |= 0x80
        payload += enc_str(user)
    if pw:
        flags |= 0x40
        payload += enc_str(pw)

    vh = enc_str("MQTT") + bytes([4, flags]) + struct.pack("!H", keepalive_s)
    s.sendall(bytes([0x10]) + enc_len(len(vh) + len(payload)) + vh + payload)

    connack = s.recv(4)
    if len(connack) < 4 or connack[0] != 0x20 or connack[3] != 0x00:
        print(f"MQTT CONNACK failed: {list(connack)}", file=sys.stderr, flush=True)
        return 1

    sub_payload = enc_str(topic_filter) + b"\x00"
    sub_vh = struct.pack("!H", 1)
    s.sendall(bytes([0x82]) + enc_len(len(sub_vh) + len(sub_payload)) + sub_vh + sub_payload)

    print(f"Subscribed to '{topic_filter}' (Ctrl+C to stop)", flush=True)
    print("-" * 88, flush=True)

    s.settimeout(1.0)
    buf = bytearray()
    last_ping = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            if now - last_ping >= keepalive_s * 0.5:
                s.sendall(b"\xc0\x00")  # PINGREQ
                last_ping = now

            try:
                chunk = s.recv(4096)
                if not chunk:
                    print("Broker closed connection.", flush=True)
                    break
                buf.extend(chunk)
            except socket.timeout:
                pass

            # Parse complete packets in buf
            while len(buf) >= 2:
                ptype = buf[0]
                idx = 1
                mult = 1
                rlen = 0
                incomplete_len = False
                while True:
                    if idx >= len(buf):
                        incomplete_len = True
                        break
                    eb = buf[idx]
                    idx += 1
                    rlen += (eb & 0x7F) * mult
                    mult *= 128
                    if not (eb & 0x80):
                        break
                if incomplete_len or len(buf) < idx + rlen:
                    break

                body = bytes(buf[idx : idx + rlen])
                del buf[: idx + rlen]

                if (ptype & 0xF0) == 0x30:
                    tlen = struct.unpack("!H", body[:2])[0]
                    topic = body[2 : 2 + tlen].decode("utf-8", errors="replace")
                    pos = 2 + tlen
                    if ((ptype >> 1) & 0x03) > 0:
                        pos += 2
                    msg = body[pos:].decode("utf-8", errors="replace")
                    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

                    if topic.endswith("/state"):
                        try:
                            d = json.loads(msg)
                            occ = d.get("occupancy", "?")
                            mot = d.get("motion", "?")
                            dist = d.get("distance_mm", 0)
                            v_mv = d.get("voltage_mv", 0)
                            bat = d.get("battery_pct", 0)
                            pkt = d.get("packet_id", 0)
                            print(
                                f"[{ts}] {topic:<38} | occ={occ:<3} motion={mot:<3} "
                                f"dist={dist:>4} mm ({dist/1000.0:.2f} m) | "
                                f"{v_mv} mV ({bat}%) | pkt #{pkt}",
                                flush=True,
                            )
                            continue
                        except Exception:
                            pass
                    print(f"[{ts}] {topic:<38} | {msg}", flush=True)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        try:
            s.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
