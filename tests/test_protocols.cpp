/*
 * Copyright (c) 2026 Craig McLean
 * Host Unit Test Suite for HLK-LD2410S UART Protocol & BTHome v2 BLE Encoder
 */

#include "../src/ld2410s_proto.h"
#include "../src/bthome_proto.h"
#include "../src/ha_mqtt_proto.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int sTestsRun    = 0;
static int sTestsFailed = 0;

#define EXPECT_TRUE(cond, msg)                                                        \
    do {                                                                              \
        ++sTestsRun;                                                                  \
        if (!(cond)) {                                                                \
            fprintf(stderr, "FAIL [%s:%d]: %s\n", __FILE__, __LINE__, (msg));         \
            ++sTestsFailed;                                                           \
        }                                                                             \
    } while (0)

#define EXPECT_EQ(actual, expected, msg)                                              \
    do {                                                                              \
        ++sTestsRun;                                                                  \
        const auto _a = (actual);                                                     \
        const auto _e = (expected);                                                   \
        if (_a != _e) {                                                               \
            fprintf(stderr, "FAIL [%s:%d]: %s (got %lld, expected %lld)\n",           \
                    __FILE__, __LINE__, (msg),                                        \
                    static_cast<long long>(_a), static_cast<long long>(_e));          \
            ++sTestsFailed;                                                           \
        }                                                                             \
    } while (0)

static void TestLd2410sCommandBuilders()
{
    uint8_t buf[64] = {};

    // 1. Bounds check on undersized buffers
    EXPECT_EQ(Ld2410sProto::BuildEnterConfigCmd(nullptr, sizeof(buf)), 0u, "EnterConfig null buffer");
    EXPECT_EQ(Ld2410sProto::BuildEnterConfigCmd(buf, 13u), 0u, "EnterConfig short buffer");
    EXPECT_EQ(Ld2410sProto::BuildExitConfigCmd(buf, 11u), 0u, "ExitConfig short buffer");
    EXPECT_EQ(Ld2410sProto::BuildSwitchOutputModeCmd(0u, buf, 17u), 0u, "SwitchOutputMode short buffer");

    // 2. Enter Config (0x00FF, value 0x0001) -> 14 bytes
    const uint8_t expectedEnter[14] = {
        0xFD, 0xFC, 0xFB, 0xFA,
        0x04, 0x00,
        0xFF, 0x00,
        0x01, 0x00,
        0x04, 0x03, 0x02, 0x01
    };
    const size_t enterLen = Ld2410sProto::BuildEnterConfigCmd(buf, sizeof(buf));
    EXPECT_EQ(enterLen, sizeof(expectedEnter), "EnterConfig length");
    EXPECT_EQ(memcmp(buf, expectedEnter, sizeof(expectedEnter)), 0, "EnterConfig wire bytes");

    // 3. Exit Config (0x00FE) -> 12 bytes
    const uint8_t expectedExit[12] = {
        0xFD, 0xFC, 0xFB, 0xFA,
        0x02, 0x00,
        0xFE, 0x00,
        0x04, 0x03, 0x02, 0x01
    };
    const size_t exitLen = Ld2410sProto::BuildExitConfigCmd(buf, sizeof(buf));
    EXPECT_EQ(exitLen, sizeof(expectedExit), "ExitConfig length");
    EXPECT_EQ(memcmp(buf, expectedExit, sizeof(expectedExit)), 0, "ExitConfig wire bytes");

    // 4. Write Common Parameters (0x0070) for 3 m^3 bathroom -> 48 bytes
    EXPECT_EQ(Ld2410sProto::kDefaultReportFreqTenthsHz, 80u, "Default report frequency is 8.0 Hz (80 * 0.1 Hz)");
    EXPECT_EQ(Ld2410sProto::kDefaultResponseSpeedFast, 10u, "Fast response speed preset is 10");
    const Ld2410sConfigParams params = {
        .farthestGate           = Ld2410sProto::kDefaultBathroomMaxGate,   // 3 (2.10 m)
        .nearestGate            = Ld2410sProto::kDefaultBathroomMinGate,   // 0 (0.00 m)
        .unoccupiedHoldSec      = Ld2410sProto::kDefaultBathroomHoldSec,   // 30 s
        .statusReportFreqHz10   = Ld2410sProto::kDefaultReportFreqTenthsHz, // 80 (8.0 Hz)
        .distanceReportFreqHz10 = Ld2410sProto::kDefaultReportFreqTenthsHz, // 80 (8.0 Hz)
        .responseSpeed          = Ld2410sProto::kDefaultResponseSpeedFast, // 10 (Fast)
    };
    EXPECT_EQ(Ld2410sProto::BuildWriteCommonParamsCmd(params, buf, 47u), 0u, "WriteCommonParams short buffer");
    const size_t writeLen = Ld2410sProto::BuildWriteCommonParamsCmd(params, buf, sizeof(buf));
    EXPECT_EQ(writeLen, Ld2410sProto::kWriteCommonParamsFrameSize, "WriteCommonParams length");
    EXPECT_EQ(memcmp(&buf[0], Ld2410sProto::kCmdHeader, 4), 0, "WriteCommonParams header");
    EXPECT_EQ(buf[4], 0x26u, "WriteCommonParams payload length lo (38B)");
    EXPECT_EQ(buf[5], 0x00u, "WriteCommonParams payload length hi");
    EXPECT_EQ(buf[6], 0x70u, "WriteCommonParams cmd lo");
    EXPECT_EQ(buf[7], 0x00u, "WriteCommonParams cmd hi");
    // Gate 0x0005 = 3
    EXPECT_EQ(buf[8], 0x05u, "Param 0 ID lo (farthest gate)");
    EXPECT_EQ(buf[10], 0x03u, "Param 0 value (gate 3 = 2.1m)");
    // Hold 0x0006 = 30 (0x1E)
    EXPECT_EQ(buf[20], 0x06u, "Param 2 ID lo (hold time)");
    EXPECT_EQ(buf[22], 30u, "Param 2 value (30 s)");
    // Status report freq 0x0002 = 80 (0x50 = 8.0 Hz)
    EXPECT_EQ(buf[26], 0x02u, "Param 3 ID lo (status report freq)");
    EXPECT_EQ(buf[28], 80u, "Param 3 value (80 = 8.0 Hz)");
    // Distance report freq 0x000C = 80 (0x50 = 8.0 Hz)
    EXPECT_EQ(buf[32], 0x0Cu, "Param 4 ID lo (distance report freq)");
    EXPECT_EQ(buf[34], 80u, "Param 4 value (80 = 8.0 Hz)");
    // Response speed 0x000B = 10 (Fast)
    EXPECT_EQ(buf[38], 0x0Bu, "Param 5 ID lo (response speed)");
    EXPECT_EQ(buf[40], 10u, "Param 5 value (10 = Fast)");
    EXPECT_EQ(memcmp(&buf[44], Ld2410sProto::kCmdFooter, 4), 0, "WriteCommonParams footer");

    // 5. Switch Output Mode (0x007A -> minimal 0x00000000) -> 18 bytes
    const uint8_t expectedMode[18] = {
        0xFD, 0xFC, 0xFB, 0xFA,
        0x08, 0x00,
        0x7A, 0x00,
        0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x04, 0x03, 0x02, 0x01
    };
    const size_t modeLen = Ld2410sProto::BuildSwitchOutputModeCmd(
        Ld2410sProto::kOutputModeMinimal, buf, sizeof(buf));
    EXPECT_EQ(modeLen, sizeof(expectedMode), "SwitchOutputMode length");
    EXPECT_EQ(memcmp(buf, expectedMode, sizeof(expectedMode)), 0, "SwitchOutputMode wire bytes");

    // 6. HLK-LD2410C Write Max Gate & Hold (0x0060) -> 30 bytes (Gate 3 = 2.25 m, Hold = 30 s)
    const Ld2410cConfigParams cParams = {
        .maxMovingGate     = 3u,
        .maxStationaryGate = 3u,
        .unoccupiedHoldSec = 30u,
    };
    const uint8_t expectedLd2410cWrite[30] = {
        0xFD, 0xFC, 0xFB, 0xFA,
        0x14, 0x00,                         // 20 bytes payload
        0x60, 0x00,                         // Command 0x0060
        0x00, 0x00, 0x03, 0x00, 0x00, 0x00, // Word 0x0000 (max moving gate) = 3
        0x01, 0x00, 0x03, 0x00, 0x00, 0x00, // Word 0x0001 (max stationary gate) = 3
        0x02, 0x00, 0x1E, 0x00, 0x00, 0x00, // Word 0x0002 (unoccupied hold sec) = 30
        0x04, 0x03, 0x02, 0x01
    };
    EXPECT_EQ(Ld2410sProto::BuildLd2410cWriteMaxGateAndHoldCmd(cParams, buf, 29u), 0u,
              "BuildLd2410cWriteMaxGateAndHoldCmd rejects short buffer");
    EXPECT_EQ(Ld2410sProto::BuildLd2410cWriteMaxGateAndHoldCmd(cParams, buf, sizeof(buf)),
              sizeof(expectedLd2410cWrite), "BuildLd2410cWriteMaxGateAndHoldCmd length == 30");
    EXPECT_EQ(memcmp(buf, expectedLd2410cWrite, sizeof(expectedLd2410cWrite)), 0,
              "BuildLd2410cWriteMaxGateAndHoldCmd byte-exact match");

    // Verify HLK-LD2410C gate clamping (2..8) and hold clamping (0..65535)
    const Ld2410cConfigParams cUnclamped = {
        .maxMovingGate     = 1u,     // Clamped to 2
        .maxStationaryGate = 16u,    // Clamped to 8
        .unoccupiedHoldSec = 99999u, // Clamped to 65535 (0xFFFF)
    };
    EXPECT_EQ(Ld2410sProto::BuildLd2410cWriteMaxGateAndHoldCmd(cUnclamped, buf, sizeof(buf)),
              30u, "BuildLd2410cWriteMaxGateAndHoldCmd clamped length == 30");
    EXPECT_EQ(buf[10], 2u, "HLK-LD2410C maxMovingGate clamped to 2");
    EXPECT_EQ(buf[16], 8u, "HLK-LD2410C maxStationaryGate clamped to 8");
    EXPECT_EQ(buf[22], 0xFFu, "HLK-LD2410C unoccupiedHoldSec clamped low byte == 0xFF");
    EXPECT_EQ(buf[23], 0xFFu, "HLK-LD2410C unoccupiedHoldSec clamped high byte == 0xFF");
}

static void TestLd2410sParserMinimalAndEdgeCases()
{
    Ld2410sFrameParser parser;
    Ld2410sParsedFrame frame{};

    // 1. Moving target (state 0x03 on HLK-LD2410S) at 145 cm (1450 mm): 6E 03 91 00 62
    const uint8_t moving145[5] = {0x6E, 0x03, 0x91, 0x00, 0x62};
    for (size_t i = 0; i < 4; ++i) {
        EXPECT_TRUE(!parser.PushByte(moving145[i], &frame), "Partial minimal frame must not emit early");
    }
    EXPECT_TRUE(parser.PushByte(moving145[4], &frame), "Complete minimal moving frame emitted");
    EXPECT_EQ(static_cast<int>(frame.type), static_cast<int>(Ld2410sFrameType::Report), "Frame type Report");
    EXPECT_TRUE(frame.report.isMinimalFrame, "Minimal frame flag");
    EXPECT_EQ(static_cast<int>(frame.report.state), static_cast<int>(Ld2410sTargetState::Moving), "State 0x03 == Moving");
    EXPECT_TRUE(frame.report.occupied, "Moving target (0x03) sets occupied=true");
    EXPECT_TRUE(frame.report.motion, "Moving target (0x03) sets motion=true");
    EXPECT_EQ(frame.report.distanceCm, 145u, "Distance 145 cm");
    EXPECT_EQ(frame.report.distanceMm, 1450u, "Distance 1450 mm");

    // 2. Stationary target (state 0x02 on HLK-LD2410S) at 110 cm (0x006E — payload byte equals header byte 0x6E!)
    //    and 98 cm (0x0062 — payload byte equals footer byte 0x62!)
    const uint8_t still110[5] = {0x6E, 0x02, 0x6E, 0x00, 0x62};
    for (size_t i = 0; i < 4; ++i) {
        EXPECT_TRUE(!parser.PushByte(still110[i], &frame), "Payload byte 0x6E must not reset frame");
    }
    EXPECT_TRUE(parser.PushByte(still110[4], &frame), "Complete 110 cm stationary frame emitted");
    EXPECT_EQ(static_cast<int>(frame.report.state), static_cast<int>(Ld2410sTargetState::Stationary), "State 0x02 == Stationary");
    EXPECT_TRUE(frame.report.occupied, "Stationary target (0x02) sets occupied=true");
    EXPECT_TRUE(!frame.report.motion, "Stationary target (0x02) sets motion=false");
    EXPECT_EQ(frame.report.distanceCm, 110u, "Distance 110 cm (0x6E)");
    EXPECT_EQ(frame.report.distanceMm, 1100u, "Distance 1100 mm");

    const uint8_t still98[5] = {0x6E, 0x02, 0x62, 0x00, 0x62};
    for (size_t i = 0; i < 4; ++i) {
        EXPECT_TRUE(!parser.PushByte(still98[i], &frame), "Payload byte 0x62 at index 2 must not close frame");
    }
    EXPECT_TRUE(parser.PushByte(still98[4], &frame), "Complete 98 cm stationary frame emitted");
    EXPECT_EQ(frame.report.distanceCm, 98u, "Distance 98 cm (0x62)");
    EXPECT_EQ(frame.report.distanceMm, 980u, "Distance 980 mm");

    // 3. Unoccupied frame (0x00): 6E 00 50 00 62 -> occupied=false, motion=false, distanceMm=0
    const uint8_t clearFrame[5] = {0x6E, 0x00, 0x50, 0x00, 0x62};
    bool gotClear = false;
    for (uint8_t b : clearFrame) {
        if (parser.PushByte(b, &frame)) {
            gotClear = true;
        }
    }
    EXPECT_TRUE(gotClear, "Unoccupied minimal frame decoded");
    EXPECT_TRUE(!frame.report.occupied, "Unoccupied sets occupied=false");
    EXPECT_TRUE(!frame.report.motion, "Unoccupied sets motion=false");
    EXPECT_EQ(frame.report.distanceMm, 0u, "Unoccupied clamps distanceMm to 0");

    // 4. HLK-LD2410S state=0x01 -> Unoccupied ("no body"), clamps distanceMm to 0 even if stale distanceCm is present
    const uint8_t clear01Frame[5] = {0x6E, 0x01, 0x00, 0x00, 0x62};
    bool gotClear01 = false;
    for (uint8_t b : clear01Frame) {
        if (parser.PushByte(b, &frame)) {
            gotClear01 = true;
        }
    }
    EXPECT_TRUE(gotClear01, "State 0x01 with 0 cm decoded");
    EXPECT_TRUE(!frame.report.occupied, "State 0x01 with 0 cm sets occupied=false");
    EXPECT_TRUE(!frame.report.motion, "State 0x01 with 0 cm sets motion=false");
    EXPECT_EQ(frame.report.distanceMm, 0u, "State 0x01 with 0 cm clamps distanceMm to 0");

    const uint8_t clear01StaleDistFrame[5] = {0x6E, 0x01, 0x78, 0x00, 0x62};
    bool gotClear01Stale = false;
    for (uint8_t b : clear01StaleDistFrame) {
        if (parser.PushByte(b, &frame)) {
            gotClear01Stale = true;
        }
    }
    EXPECT_TRUE(gotClear01Stale, "State 0x01 with stale distance decoded");
    EXPECT_TRUE(!frame.report.occupied, "State 0x01 always sets occupied=false");
    EXPECT_TRUE(!frame.report.motion, "State 0x01 always sets motion=false");
    EXPECT_EQ(frame.report.distanceMm, 0u, "State 0x01 always clamps distanceMm=0");
}

static void TestLd2410sParserStandardAndAckWithNoise()
{
    Ld2410sFrameParser parser;
    Ld2410sParsedFrame frame{};

    // Stream containing leading line noise, a false 0x6E, a Command ACK (0x01FF success),
    // more noise, and a Standard Report frame (moving target at 185 cm = 0x00B9).
    const uint8_t stream[] = {
        0xFF, 0x00, 0x6E, 0x99, 0xAA, // Noise + invalid 0x6E state
        // Command ACK for EnterConfig (0x01FF, status 0x0000):
        0xFD, 0xFC, 0xFB, 0xFA,
        0x04, 0x00,
        0xFF, 0x01,
        0x00, 0x00,
        0x04, 0x03, 0x02, 0x01,
        // Inter-frame noise:
        0xF4, 0x00, 0x42,
        // Standard Report Frame (payload len = 8: type=0x01, state=0x03 Moving, dist=185 cm, + 4 energy bytes):
        0xF4, 0xF3, 0xF2, 0xF1,
        0x08, 0x00,
        0x01, 0x03, 0xB9, 0x00, 0x10, 0x20, 0x30, 0x40,
        0xF8, 0xF7, 0xF6, 0xF5
    };

    int ackCount    = 0;
    int reportCount = 0;

    for (uint8_t b : stream) {
        if (parser.PushByte(b, &frame)) {
            if (frame.type == Ld2410sFrameType::Ack) {
                ++ackCount;
                EXPECT_EQ(frame.ack.ackCommandWord, 0x01FFu, "ACK command word 0x01FF");
                EXPECT_EQ(frame.ack.status, 0x0000u, "ACK status success");
            } else if (frame.type == Ld2410sFrameType::Report) {
                ++reportCount;
                EXPECT_TRUE(!frame.report.isMinimalFrame, "Standard report frame flag");
                EXPECT_TRUE(frame.report.occupied, "Standard report occupied");
                EXPECT_TRUE(frame.report.motion, "Standard report motion (0x03)");
                EXPECT_EQ(frame.report.distanceCm, 185u, "Standard report 185 cm");
                EXPECT_EQ(frame.report.distanceMm, 1850u, "Standard report 1850 mm");
            }
        }
    }

    EXPECT_EQ(ackCount, 1, "Decoded exactly 1 ACK frame across noisy stream");
    EXPECT_EQ(reportCount, 1, "Decoded exactly 1 Standard Report frame across noisy stream");

    // Full 80-byte HLK-LD2410S Standard Output Frame (payloadLen = 70: 1B type + 1B state=0x03 Moving + 2B dist + 2B res + 64B gates)
    uint8_t fullStdFrame[80] = {};
    fullStdFrame[0] = 0xF4;
    fullStdFrame[1] = 0xF3;
    fullStdFrame[2] = 0xF2;
    fullStdFrame[3] = 0xF1;
    fullStdFrame[4] = 70u; // 0x46 payload length
    fullStdFrame[5] = 0x00;
    fullStdFrame[6] = 0x01; // Target report type
    fullStdFrame[7] = 0x03; // Moving (0x03)
    fullStdFrame[8] = 135u; // 135 cm (1350 mm)
    fullStdFrame[9] = 0x00;
    fullStdFrame[76] = 0xF8;
    fullStdFrame[77] = 0xF7;
    fullStdFrame[78] = 0xF6;
    fullStdFrame[79] = 0xF5;

    bool gotFullStd = false;
    for (uint8_t b : fullStdFrame) {
        if (parser.PushByte(b, &frame)) {
            gotFullStd = true;
        }
    }
    EXPECT_TRUE(gotFullStd, "Decoded full 80-byte (70B payload) HLK-LD2410S standard frame");
    EXPECT_TRUE(frame.report.occupied, "80-byte standard frame occupied=true");
    EXPECT_TRUE(frame.report.motion, "80-byte standard frame motion=true (state 0x03)");
    EXPECT_EQ(frame.report.distanceMm, 1350u, "80-byte standard frame distanceMm=1350");
}

static void TestBthomeV2EncodingAndSpecCompliance()
{
    const BthomeMeasurement m = {
        .packetId   = 42u,
        .batteryPct = 87u,
        .voltageMv  = 3985u, // 0x0F91
        .motion     = true,
        .occupancy  = true,
        .distanceMm = 1340u, // 0x053C
    };

    uint8_t svcData[32] = {};
    const size_t svcLen = BthomeProto::EncodeServiceData(m, svcData, sizeof(svcData));
    EXPECT_EQ(svcLen, BthomeProto::kServiceDataPayloadSize, "BTHome service data size == 17 bytes");
    EXPECT_TRUE(BthomeProto::VerifyServiceData(svcData, svcLen), "BTHome service data passes spec verifier");

    const uint8_t expectedSvcData[17] = {
        0xD2, 0xFC,             // UUID 0xFCD2 (LE)
        0x40,                   // BTHome v2, unencrypted, regular update
        0x00, 42u,              // Object 0x00: packet_id
        0x01, 87u,              // Object 0x01: battery %
        0x0C, 0x91, 0x0F,       // Object 0x0C: voltage 3985 mV (LE)
        0x21, 0x01,             // Object 0x21: motion = 1
        0x23, 0x01,             // Object 0x23: occupancy = 1
        0x40, 0x3C, 0x05        // Object 0x40: distance_mm 1340 mm (LE)
    };
    EXPECT_EQ(memcmp(svcData, expectedSvcData, sizeof(expectedSvcData)), 0, "BTHome exact byte layout");

    // Verify full BLE Legacy Advertising PDU fits well within 31-byte limit (22 bytes)
    uint8_t pdu[32] = {};
    const size_t pduLen = BthomeProto::EncodePrimaryAdvPdu(m, pdu, sizeof(pdu));
    EXPECT_EQ(pduLen, BthomeProto::kPrimaryAdvPduSize, "Primary BLE ADV PDU size == 22 bytes");
    EXPECT_TRUE(pduLen <= BthomeProto::kBleLegacyAdvMaxBytes, "Primary BLE ADV PDU <= 31 bytes");

    // Verify negative tests: non-ascending Object IDs must be rejected by VerifyServiceData
    uint8_t badOrder[17];
    memcpy(badOrder, svcData, sizeof(badOrder));
    badOrder[10] = 0x23u; // Swap 0x21 and 0x23 so 0x23 comes before 0x21
    badOrder[12] = 0x21u;
    EXPECT_TRUE(!BthomeProto::VerifyServiceData(badOrder, sizeof(badOrder)),
                "Out-of-order Object IDs rejected");

    // Verify deterministic FICR device name formatting
    const uint8_t ficrA[8] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0};
    const uint8_t ficrB[8] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF1};
    char nameA[16] = {};
    char nameB[16] = {};
    EXPECT_EQ(BthomeProto::FormatDeviceName(ficrA, sizeof(ficrA), nameA, sizeof(nameA)), 13u, "Name A length");
    EXPECT_EQ(BthomeProto::FormatDeviceName(ficrB, sizeof(ficrB), nameB, sizeof(nameB)), 13u, "Name B length");
    EXPECT_EQ( strncmp(nameA, "Presence-", 9), 0, "Name A prefix");
    EXPECT_TRUE(strcmp(nameA, nameB) != 0, "Distinct FICR IDs produce distinct BLE names");
}

static void TestLd2410sMotionTrackerKinematics()
{
    Ld2410sMotionTracker tracker;

    // 1. Entry with Minimal 5-Byte 0x02 frame at t = 1000 ms (700 mm):
    // Entering an unoccupied room always synthesizes motion = true and state = Moving.
    Ld2410sReport r1 = {
        .state          = Ld2410sTargetState::Stationary,
        .occupied       = true,
        .motion         = false,
        .distanceCm     = 70u,
        .distanceMm     = 700u,
        .isMinimalFrame = true,
    };
    tracker.Update(&r1, 1000);
    EXPECT_TRUE(r1.occupied, "Entry frame occupied=true");
    EXPECT_TRUE(r1.motion, "Entry frame synthesizes motion=true");
    EXPECT_EQ(static_cast<uint8_t>(r1.state), static_cast<uint8_t>(Ld2410sTargetState::Moving),
              "Entry frame upgrades state to Moving");
    EXPECT_EQ(tracker.GetAnchorDistanceMm(), 700u, "Entry frame anchors at 700 mm");

    // 2. Sub-100 mm jitter within 5.0 s hold window (t = 4500 ms, elapsed = 3500 ms < 5000 ms, 740 mm -> +40 mm < 100 mm):
    Ld2410sReport r2 = r1;
    r2.state      = Ld2410sTargetState::Stationary;
    r2.motion     = false;
    r2.distanceCm = 74u;
    r2.distanceMm = 740u;
    tracker.Update(&r2, 4500);
    EXPECT_TRUE(r2.occupied, "Within 5s hold occupied=true");
    EXPECT_TRUE(r2.motion, "Within 5s hold motion stays true");
    EXPECT_EQ(tracker.GetAnchorDistanceMm(), 700u, "Sub-100mm jitter does not shift motion anchor");

    // 3. Radial walk at t = 4800 ms to 1200 mm (+500 mm >= 100 mm) extends motion window:
    Ld2410sReport r3 = r1;
    r3.state      = Ld2410sTargetState::Stationary;
    r3.motion     = false;
    r3.distanceCm = 120u;
    r3.distanceMm = 1200u;
    tracker.Update(&r3, 4800);
    EXPECT_TRUE(r3.motion, "Radial walk >= 100 mm keeps motion=true");
    EXPECT_EQ(tracker.GetAnchorDistanceMm(), 1200u, "Radial walk updates anchor to 1200 mm");
    EXPECT_EQ(tracker.GetLastMotionTimestampMs(), 4800, "Radial walk updates motion timestamp to 4800 ms");

    // 4. Stillness for >= 5000 ms after last movement (t = 9800 ms, elapsed = 5000 ms at 1150 mm -> -50 mm < 100 mm):
    // Must transition cleanly to motion = false (Stationary) for BOTH 0x02 and 0x03 raw states!
    Ld2410sReport r4 = r3;
    r4.state      = Ld2410sTargetState::Moving; // Even if raw state is 0x03, < 100 mm delta must decay!
    r4.motion     = true;
    r4.distanceCm = 115u;
    r4.distanceMm = 1150u;
    tracker.Update(&r4, 9800);
    EXPECT_TRUE(r4.occupied, "After 5s stillness occupied stays true");
    EXPECT_TRUE(!r4.motion, "After 5s stillness motion transitions to false (Clear) for both 0x02 and 0x03");
    EXPECT_EQ(static_cast<uint8_t>(r4.state), static_cast<uint8_t>(Ld2410sTargetState::Stationary),
              "After 5s stillness state downgrades to Stationary (0x02)");

    // 5. Subsequent movement while occupied (t = 12000 ms, 1150 mm -> 350 mm, delta = 850 mm >= 100 mm):
    // Must re-trigger motion = true!
    Ld2410sReport r5 = r4;
    r5.state      = Ld2410sTargetState::Stationary;
    r5.motion     = false;
    r5.distanceCm = 35u;
    r5.distanceMm = 350u;
    tracker.Update(&r5, 12000);
    EXPECT_TRUE(r5.occupied, "Re-triggered movement occupied=true");
    EXPECT_TRUE(r5.motion, "Re-triggered movement >= 100 mm sets motion=true");
    EXPECT_EQ(tracker.GetAnchorDistanceMm(), 350u, "Re-triggered movement updates anchor to 350 mm");

    // 6. Out-of-bounds reflection beyond 3 m^3 bathroom max distance (3450 mm > 2100 mm at t = 13000 ms):
    // Must clamp to Unoccupied (occupied = false, motion = false, distanceMm = 0) and reset tracker!
    Ld2410sReport rFar = {
        .state          = Ld2410sTargetState::Moving,
        .occupied       = true,
        .motion         = true,
        .distanceCm     = 345u,
        .distanceMm     = 3450u,
        .isMinimalFrame = true,
    };
    tracker.Update(&rFar, 13000);
    EXPECT_TRUE(!rFar.occupied, "Out-of-bounds (>2100 mm) clamps occupied=false");
    EXPECT_TRUE(!rFar.motion, "Out-of-bounds (>2100 mm) clamps motion=false");
    EXPECT_EQ(rFar.distanceMm, 0u, "Out-of-bounds (>2100 mm) clamps distanceMm=0");
    EXPECT_EQ(tracker.GetAnchorDistanceMm(), 0u, "Out-of-bounds (>2100 mm) resets motion anchor to 0");

    // 7. 5-wire OT2 rising-edge fast-path followed 62 ms later by Minimal 0x02 sample:
    tracker.NotifyEntryEdge(20000);
    Ld2410sReport r7 = {
        .state          = Ld2410sTargetState::Stationary,
        .occupied       = true,
        .motion         = false,
        .distanceCm     = 140u,
        .distanceMm     = 1400u,
        .isMinimalFrame = true,
    };
    tracker.Update(&r7, 20062);
    EXPECT_TRUE(r7.occupied, "Post-OT2 Minimal 0x02 sample occupied=true");
    EXPECT_TRUE(r7.motion, "Post-OT2 Minimal 0x02 sample preserves 5s entry motion=true");
    EXPECT_EQ(tracker.GetAnchorDistanceMm(), 1400u, "Post-OT2 sample anchors at 1400 mm");

    // 8. HLK-LD2410C static clutter occupancy decay after 30.0 s (kDefaultOccupancyHoldWindowMs) without movement:
    // At t = 35000 ms (elapsed = 15000 ms < 30000 ms), even if a Stationary (0x02, isMinimalFrame=false) frame
    // hops between static gates (1400 mm -> 840 mm, delta = 560 mm), it must NOT re-trigger motion or reset the timer!
    Ld2410sReport r8GateHop = {
        .state          = Ld2410sTargetState::Stationary,
        .occupied       = true,
        .motion         = false,
        .distanceCm     = 84u,
        .distanceMm     = 840u,
        .isMinimalFrame = false,
    };
    tracker.Update(&r8GateHop, 35000);
    EXPECT_TRUE(r8GateHop.occupied, "Stationary 0x02 gate hop at 15s keeps occupied=true");
    EXPECT_TRUE(!r8GateHop.motion, "Stationary 0x02 gate hop (1400->840 mm) on LD2410C does NOT re-trigger motion");
    EXPECT_EQ(tracker.GetLastMotionTimestampMs(), 20000, "Stationary 0x02 gate hop does NOT reset motion timestamp");

    // At t = 49999 ms (elapsed = 29999 ms < 30000 ms), occupancy remains true while motion is false.
    Ld2410sReport r8Hold = {
        .state          = Ld2410sTargetState::Stationary,
        .occupied       = true,
        .motion         = false,
        .distanceCm     = 140u,
        .distanceMm     = 1400u,
        .isMinimalFrame = false,
    };
    tracker.Update(&r8Hold, 49999);
    EXPECT_TRUE(r8Hold.occupied, "Before 30s occupancy hold expires (29999 ms), occupied stays true");
    EXPECT_TRUE(!r8Hold.motion, "Before 30s occupancy hold expires (29999 ms), motion is false");

    // At t = 50000 ms (elapsed = 30000 ms >= 30000 ms), occupancy expires to Unoccupied (occupied = false, dist = 0).
    Ld2410sReport r8Expire = {
        .state          = Ld2410sTargetState::Stationary,
        .occupied       = true,
        .motion         = false,
        .distanceCm     = 140u,
        .distanceMm     = 1400u,
        .isMinimalFrame = false,
    };
    tracker.Update(&r8Expire, 50000);
    EXPECT_TRUE(!r8Expire.occupied, "At 30s without movement, latched 0x02 occupancy expires to false");
    EXPECT_TRUE(!r8Expire.motion, "At 30s without movement, motion is false");
    EXPECT_EQ(static_cast<uint8_t>(r8Expire.state), static_cast<uint8_t>(Ld2410sTargetState::Unoccupied),
              "At 30s without movement, state clamps to Unoccupied");
    EXPECT_EQ(r8Expire.distanceMm, 0u, "At 30s without movement, distanceMm clamps to 0");

    // Subsequent HLK-LD2410C Stationary (0x02, isMinimalFrame=false) clutter shift (1400 -> 1270 mm) must NOT re-trigger occupancy:
    Ld2410sReport r8StaticShift = {
        .state          = Ld2410sTargetState::Stationary,
        .occupied       = true,
        .motion         = false,
        .distanceCm     = 127u,
        .distanceMm     = 1270u,
        .isMinimalFrame = false,
    };
    tracker.Update(&r8StaticShift, 55000);
    EXPECT_TRUE(!r8StaticShift.occupied, "Latched LD2410C Stationary (0x02) frame does not re-trigger occupancy");
    EXPECT_EQ(r8StaticShift.distanceMm, 0u, "Latched LD2410C Stationary (0x02) frame keeps distanceMm=0");

    // Genuine HLK-LD2410C Moving (0x01/0x03, isMinimalFrame=false) frame with >= 100 mm radial shift immediately re-triggers occupancy:
    Ld2410sReport r8Reenter = {
        .state          = Ld2410sTargetState::Moving,
        .occupied       = true,
        .motion         = true,
        .distanceCm     = 85u,
        .distanceMm     = 850u,
        .isMinimalFrame = false,
    };
    tracker.Update(&r8Reenter, 56000);
    EXPECT_TRUE(r8Reenter.occupied, "Genuine LD2410C Moving frame >= 100 mm re-triggers occupied=true");
    EXPECT_TRUE(r8Reenter.motion, "Genuine LD2410C Moving frame >= 100 mm re-triggers motion=true");
    EXPECT_EQ(r8Reenter.distanceMm, 850u, "Genuine LD2410C Moving frame reports 850 mm");
}

static void TestHaMqttDiscoveryAndNat64()
{
    const uint8_t ficr[8] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0};
    char slug[20] = {};
    char devName[20] = {};
    EXPECT_EQ(HaMqttProto::FormatNodeSlug(ficr, sizeof(ficr), slug, sizeof(slug)),
              HaMqttProto::kNodeSlugLen, "Node slug length == 13");
    EXPECT_EQ(strncmp(slug, "presence_", 9), 0, "Node slug starts with presence_");
    EXPECT_EQ(BthomeProto::FormatDeviceName(ficr, sizeof(ficr), devName, sizeof(devName)),
              BthomeProto::kDeviceNameLen, "Device name length == 13");

    // Verify lowercase hex in slug matches uppercase hex in device name
    for (size_t i = 9; i < 13; ++i) {
        const char upper = devName[i];
        const char expectedLower = (upper >= 'A' && upper <= 'F') ? static_cast<char>(upper - 'A' + 'a') : upper;
        EXPECT_EQ(slug[i], expectedLower, "Slug hex char matches lowercase of device name");
    }

    // State and availability topics
    char stateTopic[HaMqttProto::kMaxTopicLen] = {};
    char availTopic[HaMqttProto::kMaxTopicLen] = {};
    EXPECT_TRUE(HaMqttProto::FormatStateTopic(slug, stateTopic, sizeof(stateTopic)) > 0u,
                "FormatStateTopic succeeds");
    EXPECT_TRUE(HaMqttProto::FormatAvailabilityTopic(slug, availTopic, sizeof(availTopic)) > 0u,
                "FormatAvailabilityTopic succeeds");
    EXPECT_TRUE(strstr(stateTopic, "/state") != nullptr, "State topic ends with /state");
    EXPECT_TRUE(strstr(availTopic, "/status") != nullptr, "Availability topic ends with /status");

    // State JSON payload formatting
    const BthomeMeasurement mOn = {
        .packetId   = 42u,
        .batteryPct = 87u,
        .voltageMv  = 3985u,
        .motion     = true,
        .occupancy  = true,
        .distanceMm = 1340u,
    };
    char stateJson[HaMqttProto::kMaxStatePayloadLen] = {};
    const size_t stateLen = HaMqttProto::FormatStatePayload(mOn, stateJson, sizeof(stateJson));
    EXPECT_TRUE(stateLen > 0u, "FormatStatePayload ON succeeds");
    EXPECT_EQ(strcmp(stateJson,
                     "{\"occupancy\":\"ON\",\"motion\":\"ON\",\"distance_mm\":1340,\"battery_pct\":87,\"voltage_mv\":3985,\"packet_id\":42}"),
              0, "FormatStatePayload exact JSON match (ON)");

    const BthomeMeasurement mOff = {
        .packetId   = 43u,
        .batteryPct = 105u, // Clamped to 100
        .voltageMv  = 3300u,
        .motion     = false,
        .occupancy  = false,
        .distanceMm = 0u,
    };
    EXPECT_TRUE(HaMqttProto::FormatStatePayload(mOff, stateJson, sizeof(stateJson)) > 0u,
                "FormatStatePayload OFF succeeds");
    EXPECT_EQ(strcmp(stateJson,
                     "{\"occupancy\":\"OFF\",\"motion\":\"OFF\",\"distance_mm\":0,\"battery_pct\":100,\"voltage_mv\":3300,\"packet_id\":43}"),
              0, "FormatStatePayload exact JSON match (OFF + clamped battery_pct)");

    // Discovery topics & payloads for all 5 entities
    static constexpr HaEntityId kAllEntities[5] = {
        HaEntityId::Occupancy,
        HaEntityId::Motion,
        HaEntityId::Distance,
        HaEntityId::Battery,
        HaEntityId::Voltage,
    };
    for (HaEntityId entity : kAllEntities) {
        char discTopic[HaMqttProto::kMaxTopicLen] = {};
        char discJson[HaMqttProto::kMaxDiscoveryJsonLen] = {};
        const size_t tLen = HaMqttProto::FormatDiscoveryTopic(slug, entity, discTopic, sizeof(discTopic));
        const size_t pLen = HaMqttProto::FormatDiscoveryPayload(
            slug, devName, "1.1.0", entity, discJson, sizeof(discJson));
        EXPECT_TRUE(tLen > 0u && tLen < sizeof(discTopic), "Discovery topic fits in buffer");
        EXPECT_TRUE(pLen > 0u && pLen < sizeof(discJson), "Discovery payload fits in <512B buffer");
        EXPECT_TRUE(strstr(discTopic, "homeassistant/") == discTopic, "Discovery topic prefix");
        EXPECT_TRUE(strstr(discTopic, "/config") != nullptr, "Discovery topic suffix");
        EXPECT_TRUE(strstr(discJson, "\"stat_t\":\"presence_sensor/") != nullptr, "Discovery payload has stat_t");
        EXPECT_TRUE(strstr(discJson, "\"avty_t\":\"presence_sensor/") != nullptr, "Discovery payload has avty_t");
        EXPECT_TRUE(strstr(discJson, "\"mdl\":\"HLK-LD2410S Thread SED\"") != nullptr, "Discovery payload has model");
    }

    // RFC 6052 /96 NAT64 synthesis & IPv4 literal parser
    uint8_t ipv4[4] = {};
    EXPECT_TRUE(HaMqttProto::ParseIpv4Literal("192.168.41.250", ipv4), "Parse valid IPv4 192.168.41.250");
    EXPECT_EQ(ipv4[0], 192u, "IPv4 octet 0");
    EXPECT_EQ(ipv4[1], 168u, "IPv4 octet 1");
    EXPECT_EQ(ipv4[2], 41u,  "IPv4 octet 2");
    EXPECT_EQ(ipv4[3], 250u, "IPv4 octet 3");
    EXPECT_TRUE(!HaMqttProto::ParseIpv4Literal("192.168.41.999", ipv4), "Reject out-of-range IPv4 octet");
    EXPECT_TRUE(!HaMqttProto::ParseIpv4Literal("192.168.41", ipv4), "Reject short IPv4 literal");

    const uint8_t nat64Prefix[12] = {
        0xfd, 0x11, 0x22, 0x33, 0x44, 0x55, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00
    };
    uint8_t synthIpv6[16] = {};
    EXPECT_TRUE(HaMqttProto::SynthesizeNat64Ipv6(nat64Prefix, ipv4, synthIpv6), "SynthesizeNat64Ipv6 succeeds");
    EXPECT_EQ(memcmp(&synthIpv6[0], nat64Prefix, 12u), 0, "NAT64 upper 96 bits match prefix");
    EXPECT_EQ(synthIpv6[12], 192u, "NAT64 byte 12 == 192");
    EXPECT_EQ(synthIpv6[13], 168u, "NAT64 byte 13 == 168");
    EXPECT_EQ(synthIpv6[14], 41u,  "NAT64 byte 14 == 41");
    EXPECT_EQ(synthIpv6[15], 250u, "NAT64 byte 15 == 250");
}

static size_t FeedStream(Ld2410sFrameParser &parser,
                         const uint8_t *bytes,
                         size_t len,
                         Ld2410sParsedFrame *outLastFrame)
{
    size_t count = 0;
    for (size_t i = 0; i < len; ++i) {
        Ld2410sParsedFrame tmp{};
        if (parser.PushByte(bytes[i], &tmp)) {
            *outLastFrame = tmp;
            ++count;
        }
    }
    return count;
}

static void TestLd2410cParserStandardAndEngineeringFrames()
{
    Ld2410sFrameParser parser;
    Ld2410sParsedFrame out{};

    // 1. HLK-LD2410C Normal Report Frame (23 bytes, payloadLen = 13):
    //    State 0x01 = Moving target (must NOT be misparsed as Unoccupied or Layout B!)
    //    movingDistCm = 145 cm, movingEnergy = 80, stationaryDistCm = 0, stationaryEnergy = 0, detectionDistCm = 145 cm
    const uint8_t ld2410cMovingFrame[23] = {
        0xF4, 0xF3, 0xF2, 0xF1,
        0x0D, 0x00,             // payloadLen = 13
        0x02, 0xAA,             // normal mode (0x02) + head (0xAA)
        0x01,                   // targetState = 0x01 (Moving target on LD2410C!)
        0x91, 0x00,             // movingDistCm = 145 cm
        0x50,                   // movingEnergy = 80
        0x00, 0x00,             // stationaryDistCm = 0 cm
        0x00,                   // stationaryEnergy = 0
        0x91, 0x00,             // detectionDistCm = 145 cm
        0x55, 0x00,             // tail (0x55) + check (0x00)
        0xF8, 0xF7, 0xF6, 0xF5
    };
    EXPECT_EQ(FeedStream(parser, ld2410cMovingFrame, sizeof(ld2410cMovingFrame), &out), 1u,
              "Parse HLK-LD2410C normal Moving (0x01) frame");
    EXPECT_EQ(static_cast<uint8_t>(out.type), static_cast<uint8_t>(Ld2410sFrameType::Report),
              "LD2410C frame type == Report");
    EXPECT_EQ(static_cast<uint8_t>(out.report.state), static_cast<uint8_t>(Ld2410sTargetState::Moving),
              "LD2410C state 0x01 mapped to Moving");
    EXPECT_TRUE(out.report.occupied, "LD2410C state 0x01 occupied == true");
    EXPECT_TRUE(out.report.motion, "LD2410C state 0x01 motion == true");
    EXPECT_EQ(out.report.distanceCm, 145u, "LD2410C distanceCm == 145");
    EXPECT_EQ(out.report.distanceMm, 1450u, "LD2410C distanceMm == 1450");
    EXPECT_TRUE(!out.report.isMinimalFrame, "LD2410C isMinimalFrame == false");

    // 2. HLK-LD2410C Normal Report Frame: State 0x02 = Stationary target (fallback to stationaryDistCm when detectionDistCm == 0)
    const uint8_t ld2410cStationaryFrame[23] = {
        0xF4, 0xF3, 0xF2, 0xF1,
        0x0D, 0x00,
        0x02, 0xAA,
        0x02,                   // targetState = 0x02 (Stationary)
        0x00, 0x00, 0x00,       // moving = 0 cm
        0x78, 0x00, 0x45,       // stationary = 120 cm, energy = 69
        0x00, 0x00,             // detectionDistCm = 0 (tests fallback to stationaryDistCm = 120 cm)
        0x55, 0x00,
        0xF8, 0xF7, 0xF6, 0xF5
    };
    EXPECT_EQ(FeedStream(parser, ld2410cStationaryFrame, sizeof(ld2410cStationaryFrame), &out), 1u,
              "Parse HLK-LD2410C Stationary (0x02) frame");
    EXPECT_EQ(static_cast<uint8_t>(out.report.state), static_cast<uint8_t>(Ld2410sTargetState::Stationary),
              "LD2410C state 0x02 mapped to Stationary");
    EXPECT_TRUE(out.report.occupied, "LD2410C state 0x02 occupied == true");
    EXPECT_TRUE(!out.report.motion, "LD2410C state 0x02 motion == false");
    EXPECT_EQ(out.report.distanceMm, 1200u, "LD2410C fallback stationary distanceMm == 1200");

    // 3. HLK-LD2410C Engineering Mode Frame (type=0x01, payloadLen=35, total=45 bytes) + State 0x03 (Moving+Stationary) + State 0x00 (NoTarget) + 0x0160 ACK
    uint8_t engStream[82] = {};
    // Bytes 0..44: 45-byte Engineering Frame (state 0x03, detectionDistCm = 180 cm)
    const uint8_t engPrefix[17] = {
        0xF4, 0xF3, 0xF2, 0xF1,
        0x23, 0x00,             // payloadLen = 35
        0x01, 0xAA,             // engineering mode (0x01) + head (0xAA)
        0x03,                   // state = 0x03 (Moving + Stationary)
        0xB4, 0x00, 0x60,       // moving = 180 cm
        0xA0, 0x00, 0x55,       // stationary = 160 cm
        0xB4, 0x00              // detectionDistCm = 180 cm
    };
    memcpy(&engStream[0], engPrefix, sizeof(engPrefix));
    // Bytes 17..38: 22 bytes of engineering gate max + gate energy data
    for (size_t i = 17; i < 39; ++i) {
        engStream[i] = static_cast<uint8_t>(i);
    }
    engStream[39] = 0x55;
    engStream[40] = 0x00;
    memcpy(&engStream[41], Ld2410sProto::kStdReportFooter, 4);

    // Bytes 45..67: 23-byte Normal Frame with state 0x00 (NoTarget)
    const uint8_t ld2410cNoTarget[23] = {
        0xF4, 0xF3, 0xF2, 0xF1,
        0x0D, 0x00,
        0x02, 0xAA,
        0x00,                   // state = 0x00 (NoTarget)
        0x00, 0x00, 0x00,
        0x00, 0x00, 0x00,
        0x00, 0x00,
        0x55, 0x00,
        0xF8, 0xF7, 0xF6, 0xF5
    };
    memcpy(&engStream[45], ld2410cNoTarget, sizeof(ld2410cNoTarget));

    // Bytes 68..81: 14-byte Command 0x0060 ACK frame (0x0160, status 0x0000)
    const uint8_t ld2410cAck[14] = {
        0xFD, 0xFC, 0xFB, 0xFA,
        0x04, 0x00,
        0x60, 0x01,             // 0x0060 | 0x0100 = 0x0160
        0x00, 0x00,             // status = 0x0000
        0x04, 0x03, 0x02, 0x01
    };
    memcpy(&engStream[68], ld2410cAck, sizeof(ld2410cAck));

    Ld2410sParsedFrame decoded[3] = {};
    size_t decodedIdx = 0;
    for (size_t i = 0; i < sizeof(engStream); ++i) {
        Ld2410sParsedFrame tmp{};
        if (parser.PushByte(engStream[i], &tmp) && decodedIdx < 3) {
            decoded[decodedIdx++] = tmp;
        }
    }
    EXPECT_EQ(decodedIdx, 3u, "Decoded 3 frames from HLK-LD2410C engineering + normal + ACK stream");
    EXPECT_TRUE(decoded[0].report.occupied && decoded[0].report.motion, "Engineering 0x03 occupied & moving");
    EXPECT_EQ(decoded[0].report.distanceMm, 1800u, "Engineering 0x03 distanceMm == 1800");
    EXPECT_TRUE(!decoded[1].report.occupied && !decoded[1].report.motion, "Normal 0x00 unoccupied");
    EXPECT_EQ(decoded[1].report.distanceMm, 0u, "Normal 0x00 distanceMm == 0");
    EXPECT_EQ(static_cast<uint8_t>(decoded[2].type), static_cast<uint8_t>(Ld2410sFrameType::Ack), "Third frame is ACK");
    EXPECT_EQ(decoded[2].ack.ackCommandWord, 0x0160u, "ACK command word == 0x0160");
    EXPECT_EQ(decoded[2].ack.status, 0x0000u, "ACK status == 0x0000");
}

int main()
{
    TestLd2410sCommandBuilders();
    TestLd2410sParserMinimalAndEdgeCases();
    TestLd2410sParserStandardAndAckWithNoise();
    TestLd2410cParserStandardAndEngineeringFrames();
    TestBthomeV2EncodingAndSpecCompliance();
    TestLd2410sMotionTrackerKinematics();
    TestHaMqttDiscoveryAndNat64();

    if (sTestsFailed > 0) {
        fprintf(stderr, "FAILED: %d/%d assertions failed\n", sTestsFailed, sTestsRun);
        return EXIT_FAILURE;
    }

    printf("PASSED: All %d protocol assertions succeeded (HLK-LD2410S/C + BTHome v2 + HA MQTT/NAT64)\n", sTestsRun);
    return EXIT_SUCCESS;
}
