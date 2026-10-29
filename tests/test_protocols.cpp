/*
 * Copyright (c) 2026 Craig McLean
 * Host Unit Test Suite for HLK-LD2410S UART Protocol & BTHome v2 BLE Encoder
 */

#include "../src/ld2410s_proto.h"
#include "../src/bthome_proto.h"

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
    const Ld2410sConfigParams params = {
        .farthestGate           = Ld2410sProto::kDefaultBathroomMaxGate,     // 3 (2.10 m)
        .nearestGate            = Ld2410sProto::kDefaultBathroomMinGate,     // 0 (0.00 m)
        .unoccupiedHoldSec      = Ld2410sProto::kDefaultBathroomHoldSec,     // 30 s
        .statusReportFreqHz10   = Ld2410sProto::kDefaultReportFreqTenthsHz,  // 10 (1.0 Hz)
        .distanceReportFreqHz10 = Ld2410sProto::kDefaultReportFreqTenthsHz,  // 10 (1.0 Hz)
        .responseSpeed          = Ld2410sProto::kDefaultResponseSpeedNormal, // 5 (Normal)
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
}

static void TestLd2410sParserMinimalAndEdgeCases()
{
    Ld2410sFrameParser parser;
    Ld2410sParsedFrame frame{};

    // 1. Moving target at 145 cm (1450 mm): 6E 02 91 00 62
    const uint8_t moving145[5] = {0x6E, 0x02, 0x91, 0x00, 0x62};
    for (size_t i = 0; i < 4; ++i) {
        EXPECT_TRUE(!parser.PushByte(moving145[i], &frame), "Partial minimal frame must not emit early");
    }
    EXPECT_TRUE(parser.PushByte(moving145[4], &frame), "Complete minimal moving frame emitted");
    EXPECT_EQ(static_cast<int>(frame.type), static_cast<int>(Ld2410sFrameType::Report), "Frame type Report");
    EXPECT_TRUE(frame.report.isMinimalFrame, "Minimal frame flag");
    EXPECT_TRUE(frame.report.occupied, "Moving target sets occupied=true");
    EXPECT_TRUE(frame.report.motion, "Moving target sets motion=true");
    EXPECT_EQ(frame.report.distanceCm, 145u, "Distance 145 cm");
    EXPECT_EQ(frame.report.distanceMm, 1450u, "Distance 1450 mm");

    // 2. Stationary target at 110 cm (0x006E — payload byte equals header byte 0x6E!)
    //    and 98 cm (0x0062 — payload byte equals footer byte 0x62!)
    const uint8_t still110[5] = {0x6E, 0x03, 0x6E, 0x00, 0x62};
    for (size_t i = 0; i < 4; ++i) {
        EXPECT_TRUE(!parser.PushByte(still110[i], &frame), "Payload byte 0x6E must not reset frame");
    }
    EXPECT_TRUE(parser.PushByte(still110[4], &frame), "Complete 110 cm stationary frame emitted");
    EXPECT_TRUE(frame.report.occupied, "Stationary target sets occupied=true");
    EXPECT_TRUE(!frame.report.motion, "Stationary target sets motion=false");
    EXPECT_EQ(frame.report.distanceCm, 110u, "Distance 110 cm (0x6E)");
    EXPECT_EQ(frame.report.distanceMm, 1100u, "Distance 1100 mm");

    const uint8_t still98[5] = {0x6E, 0x03, 0x62, 0x00, 0x62};
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

    // 4. HLK-LD2410S state=0x01 with distance=0 cm -> Unoccupied; with distance=120 cm -> Moving
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

    const uint8_t moving01Frame[5] = {0x6E, 0x01, 0x78, 0x00, 0x62};
    bool gotMoving01 = false;
    for (uint8_t b : moving01Frame) {
        if (parser.PushByte(b, &frame)) {
            gotMoving01 = true;
        }
    }
    EXPECT_TRUE(gotMoving01, "State 0x01 with 120 cm decoded");
    EXPECT_TRUE(frame.report.occupied, "State 0x01 with 120 cm sets occupied=true");
    EXPECT_TRUE(frame.report.motion, "State 0x01 with 120 cm sets motion=true");
    EXPECT_EQ(frame.report.distanceMm, 1200u, "State 0x01 with 120 cm sets distanceMm=1200");
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
        // Standard Report Frame (payload len = 8: type=0x01, state=0x02, dist=185 cm, + 4 energy bytes):
        0xF4, 0xF3, 0xF2, 0xF1,
        0x08, 0x00,
        0x01, 0x02, 0xB9, 0x00, 0x10, 0x20, 0x30, 0x40,
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
                EXPECT_TRUE(frame.report.motion, "Standard report motion");
                EXPECT_EQ(frame.report.distanceCm, 185u, "Standard report 185 cm");
                EXPECT_EQ(frame.report.distanceMm, 1850u, "Standard report 1850 mm");
            }
        }
    }

    EXPECT_EQ(ackCount, 1, "Decoded exactly 1 ACK frame across noisy stream");
    EXPECT_EQ(reportCount, 1, "Decoded exactly 1 Standard Report frame across noisy stream");

    // Full 80-byte HLK-LD2410S Standard Output Frame (payloadLen = 70: 1B type + 1B state + 2B dist + 2B res + 64B gates)
    uint8_t fullStdFrame[80] = {};
    fullStdFrame[0] = 0xF4;
    fullStdFrame[1] = 0xF3;
    fullStdFrame[2] = 0xF2;
    fullStdFrame[3] = 0xF1;
    fullStdFrame[4] = 70u; // 0x46 payload length
    fullStdFrame[5] = 0x00;
    fullStdFrame[6] = 0x01; // Target report type
    fullStdFrame[7] = 0x02; // Moving
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
    EXPECT_TRUE(frame.report.motion, "80-byte standard frame motion=true");
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

int main()
{
    TestLd2410sCommandBuilders();
    TestLd2410sParserMinimalAndEdgeCases();
    TestLd2410sParserStandardAndAckWithNoise();
    TestBthomeV2EncodingAndSpecCompliance();

    if (sTestsFailed > 0) {
        fprintf(stderr, "FAILED: %d/%d assertions failed\n", sTestsFailed, sTestsRun);
        return EXIT_FAILURE;
    }

    printf("PASSED: All %d protocol assertions succeeded (HLK-LD2410S + BTHome v2)\n", sTestsRun);
    return EXIT_SUCCESS;
}
