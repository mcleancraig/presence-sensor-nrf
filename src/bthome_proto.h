/*
 * Copyright (c) 2026 Craig McLean
 * BTHome v2 (UUID 0xFCD2) BLE Service Data Encoder (Host-Testable)
 */

#pragma once

#include <stddef.h>
#include <stdint.h>

struct BthomeMeasurement {
    uint8_t  packetId;      // 0..255 rolling counter (Object 0x00)
    uint8_t  batteryPct;    // 0..100 % (Object 0x01)
    uint16_t voltageMv;     // Millivolts, factor 0.001 V (Object 0x0C)
    bool     motion;        // 1 = moving target, 0 = clear (Object 0x21)
    bool     occupancy;     // 1 = occupied, 0 = clear (Object 0x23)
    uint16_t distanceMm;    // Millimeters, factor 0.001 m (Object 0x40)
};

namespace BthomeProto {

// BTHome v2 Constants (https://bthome.io/format/)
static constexpr uint16_t kServiceUuid16             = 0xFCD2u;
static constexpr uint8_t  kServiceUuidLo             = 0xD2u;
static constexpr uint8_t  kServiceUuidHi             = 0xFCu;
static constexpr uint8_t  kDeviceInfoV2Unencrypted   = 0x40u; // v2 (bits 5..7 = 010), unencrypted (bit 0 = 0)

// BTHome v2 Object IDs (MUST be encoded in strictly ascending numerical order)
static constexpr uint8_t  kObjPacketId               = 0x00u; // uint8 (1 byte)
static constexpr uint8_t  kObjBatteryPct             = 0x01u; // uint8 (1 byte, %)
static constexpr uint8_t  kObjVoltageMv              = 0x0Cu; // uint16 LE (2 bytes, 0.001 V)
static constexpr uint8_t  kObjMotion                 = 0x21u; // uint8 (1 byte, bool: 0=Clear, 1=Detected)
static constexpr uint8_t  kObjOccupancy              = 0x23u; // uint8 (1 byte, bool: 0=Clear, 1=Detected)
static constexpr uint8_t  kObjDistanceMm             = 0x40u; // uint16 LE (2 bytes, 0.001 m = mm)

// Standard BLE Advertising Data types
static constexpr uint8_t  kBleAdTypeFlags            = 0x01u;
static constexpr uint8_t  kBleAdTypeNameComplete     = 0x09u;
static constexpr uint8_t  kBleAdTypeSvcData16        = 0x16u;
static constexpr uint8_t  kBleFlagsGeneralNoBredr    = 0x06u;

// Exact byte sizes
static constexpr size_t   kServiceDataPayloadSize    = 17u;
static constexpr size_t   kPrimaryAdvPduSize         = 22u; // 3B Flags + 19B Service Data AD
static constexpr size_t   kBleLegacyAdvMaxBytes      = 31u;
static constexpr size_t   kDeviceNameLen             = 13u; // "Presence-XXXX"

/**
 * @brief Encode the 17-byte BTHome v2 Service Data payload (starting with UUID D2 FC).
 * @return 17 on success, or 0 if outBuf is null or maxLen < 17.
 */
size_t EncodeServiceData(const BthomeMeasurement &m, uint8_t *outBuf, size_t maxLen);

/**
 * @brief Encode the complete 22-byte primary BLE legacy advertising PDU
 *        (Flags AD element + BTHome v2 Service Data AD element).
 * @return 22 on success, or 0 if outPdu is null or maxLen < 22.
 */
size_t EncodePrimaryAdvPdu(const BthomeMeasurement &m, uint8_t *outPdu, size_t maxLen);

/**
 * @brief Validate a BTHome v2 Service Data buffer for spec compliance:
 *        correct UUID (0xFCD2), v2 header (0x40), strictly ascending Object IDs,
 *        and exact length fit within the 31-byte BLE Legacy Advertising limit.
 */
bool VerifyServiceData(const uint8_t *svcData, size_t len);

/**
 * @brief Derive a deterministic 16-bit identifier from the hardware FICR device ID
 *        using FNV-1a and format "Presence-XXXX" (13 chars + NUL).
 */
uint16_t DeriveShortIdFromDeviceId(const uint8_t *deviceId, size_t len);
size_t FormatDeviceName(const uint8_t *deviceId, size_t deviceIdLen, char *outName, size_t maxNameLen);

} // namespace BthomeProto
