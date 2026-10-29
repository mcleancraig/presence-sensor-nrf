/*
 * Copyright (c) 2026 Craig McLean
 * BTHome v2 (UUID 0xFCD2) BLE Service Data Encoder (Host-Testable)
 */

#include "bthome_proto.h"

namespace BthomeProto {

size_t EncodeServiceData(const BthomeMeasurement &m, uint8_t *outBuf, size_t maxLen)
{
    if (!outBuf || maxLen < kServiceDataPayloadSize) {
        return 0;
    }

    const uint8_t clampedPct = m.batteryPct > 100u ? 100u : m.batteryPct;

    // 16-bit UUID 0xFCD2 (little-endian) + BTHome v2 unencrypted device info byte
    outBuf[0]  = kServiceUuidLo;
    outBuf[1]  = kServiceUuidHi;
    outBuf[2]  = kDeviceInfoV2Unencrypted;

    // Object 0x00: packet_id (uint8)
    outBuf[3]  = kObjPacketId;
    outBuf[4]  = m.packetId;

    // Object 0x01: battery percentage (uint8, %)
    outBuf[5]  = kObjBatteryPct;
    outBuf[6]  = clampedPct;

    // Object 0x0C: battery voltage (uint16 LE, 0.001 V = mV)
    outBuf[7]  = kObjVoltageMv;
    outBuf[8]  = static_cast<uint8_t>(m.voltageMv & 0xFFu);
    outBuf[9]  = static_cast<uint8_t>((m.voltageMv >> 8) & 0xFFu);

    // Object 0x21: motion (uint8, boolean 0/1)
    outBuf[10] = kObjMotion;
    outBuf[11] = m.motion ? 1u : 0u;

    // Object 0x23: occupancy (uint8, boolean 0/1)
    outBuf[12] = kObjOccupancy;
    outBuf[13] = m.occupancy ? 1u : 0u;

    // Object 0x40: distance in mm (uint16 LE, 0.001 m = mm)
    outBuf[14] = kObjDistanceMm;
    outBuf[15] = static_cast<uint8_t>(m.distanceMm & 0xFFu);
    outBuf[16] = static_cast<uint8_t>((m.distanceMm >> 8) & 0xFFu);

    return kServiceDataPayloadSize;
}

size_t EncodePrimaryAdvPdu(const BthomeMeasurement &m, uint8_t *outPdu, size_t maxLen)
{
    if (!outPdu || maxLen < kPrimaryAdvPduSize) {
        return 0;
    }

    // AD Element 1: Flags (3 bytes)
    outPdu[0] = 0x02u; // Length (type + 1B value)
    outPdu[1] = kBleAdTypeFlags;
    outPdu[2] = kBleFlagsGeneralNoBredr;

    // AD Element 2: Service Data 16-bit UUID (19 bytes)
    outPdu[3] = static_cast<uint8_t>(1u + kServiceDataPayloadSize); // 0x12 (18 bytes)
    outPdu[4] = kBleAdTypeSvcData16;
    EncodeServiceData(m, &outPdu[5], maxLen - 5u);

    return kPrimaryAdvPduSize;
}

static size_t GetObjectValueSize(uint8_t objId)
{
    switch (objId) {
    case kObjPacketId:
    case kObjBatteryPct:
    case kObjMotion:
    case kObjOccupancy:
        return 1u;
    case kObjVoltageMv:
    case kObjDistanceMm:
        return 2u;
    default:
        return 0u;
    }
}

bool VerifyServiceData(const uint8_t *svcData, size_t len)
{
    // Must fit inside a 31-byte BLE Legacy Advertising PDU alongside 3-byte Flags + 2-byte AD header
    if (!svcData || len < 3u || (len + 5u) > kBleLegacyAdvMaxBytes) {
        return false;
    }

    if (svcData[0] != kServiceUuidLo || svcData[1] != kServiceUuidHi) {
        return false;
    }
    if (svcData[2] != kDeviceInfoV2Unencrypted) {
        return false;
    }

    size_t offset = 3u;
    int prevObjId = -1;
    size_t objCount = 0;

    while (offset < len) {
        const uint8_t objId = svcData[offset++];
        if (static_cast<int>(objId) <= prevObjId) {
            return false; // BTHome v2 requires strictly ascending Object IDs
        }
        prevObjId = static_cast<int>(objId);

        const size_t valSize = GetObjectValueSize(objId);
        if (valSize == 0u || (offset + valSize) > len) {
            return false;
        }
        offset += valSize;
        ++objCount;
    }

    return offset == len && objCount == 6u;
}

uint16_t DeriveShortIdFromDeviceId(const uint8_t *deviceId, size_t len)
{
    uint32_t hash = 2166136261u;
    if (deviceId) {
        for (size_t i = 0; i < len; ++i) {
            hash = (hash ^ deviceId[i]) * 16777619u;
        }
    }
    // Fold 32-bit FNV-1a hash into 16 bits
    return static_cast<uint16_t>((hash >> 16) ^ (hash & 0xFFFFu));
}

size_t FormatDeviceName(const uint8_t *deviceId, size_t deviceIdLen, char *outName, size_t maxNameLen)
{
    if (!outName || maxNameLen < (kDeviceNameLen + 1u)) {
        return 0;
    }

    static constexpr char kPrefix[] = "Presence-";
    static constexpr char kHex[]    = "0123456789ABCDEF";
    const uint16_t shortId = DeriveShortIdFromDeviceId(deviceId, deviceIdLen);

    for (size_t i = 0; i < 9u; ++i) {
        outName[i] = kPrefix[i];
    }
    outName[9]  = kHex[(shortId >> 12) & 0x0Fu];
    outName[10] = kHex[(shortId >> 8) & 0x0Fu];
    outName[11] = kHex[(shortId >> 4) & 0x0Fu];
    outName[12] = kHex[shortId & 0x0Fu];
    outName[13] = '\0';

    return kDeviceNameLen;
}

} // namespace BthomeProto
