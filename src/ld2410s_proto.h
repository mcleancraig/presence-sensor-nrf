/*
 * Copyright (c) 2026 Craig McLean
 * HLK-LD2410S / HLK-LD2410C 24 GHz mmWave Radar Protocol Codec (Host-Testable)
 */

#pragma once

#include <stddef.h>
#include <stdint.h>

enum class Ld2410sTargetState : uint8_t {
    NoTarget   = 0x00,
    Unoccupied = 0x01,
    Stationary = 0x02,
    Moving     = 0x03,
};

struct Ld2410sConfigParams {
    uint32_t farthestGate;       // 1..16 (0.70 m per gate; 3 = 2.10 m for 3 m^3 bathroom)
    uint32_t nearestGate;        // 0..15 (0 = 0.00 m)
    uint32_t unoccupiedHoldSec;  // 10..120 seconds (default 30 s)
    uint32_t statusReportFreqHz10;   // 5..80 in 0.1 Hz units (80 = 8.0 Hz / 125 ms)
    uint32_t distanceReportFreqHz10; // 5..80 in 0.1 Hz units (80 = 8.0 Hz / 125 ms)
    uint32_t responseSpeed;      // 5 = Normal, 10 = Fast
};

struct Ld2410cConfigParams {
    uint32_t maxMovingGate;      // 2..8 (0.75 m per gate; 3 = 2.25 m for 3 m^3 bathroom)
    uint32_t maxStationaryGate;  // 2..8 (0.75 m per gate; 3 = 2.25 m for 3 m^3 bathroom)
    uint32_t unoccupiedHoldSec;  // 0..65535 seconds (default 30 s)
};

struct Ld2410sReport {
    Ld2410sTargetState state;
    bool               occupied;
    bool               motion;
    uint16_t           distanceCm;
    uint16_t           distanceMm;
    bool               isMinimalFrame;
    bool               isLd2410cFrame;
    uint8_t            rawState;
    uint8_t            movingEnergy;
    uint8_t            stationaryEnergy;
    uint16_t           movingDistanceCm;
    uint16_t           stationaryDistanceCm;
    uint16_t           detectionDistanceCm;
};

struct Ld2410sAck {
    uint16_t ackCommandWord; // Sent command word | 0x0100 (e.g. 0x01FF)
    uint16_t status;         // 0x0000 = success
};

enum class Ld2410sFrameType : uint8_t {
    None   = 0,
    Report = 1,
    Ack    = 2,
};

struct Ld2410sParsedFrame {
    Ld2410sFrameType type;
    Ld2410sReport    report;
    Ld2410sAck       ack;
};

namespace Ld2410sProto {

// Frame headers & footers
static constexpr uint8_t kCmdHeader[4]       = {0xFD, 0xFC, 0xFB, 0xFA};
static constexpr uint8_t kCmdFooter[4]       = {0x04, 0x03, 0x02, 0x01};
static constexpr uint8_t kStdReportHeader[4] = {0xF4, 0xF3, 0xF2, 0xF1};
static constexpr uint8_t kStdReportFooter[4] = {0xF8, 0xF7, 0xF6, 0xF5};
static constexpr uint8_t kMinimalHeader      = 0x6E;
static constexpr uint8_t kMinimalFooter      = 0x62;
static constexpr size_t  kMinimalFrameSize   = 5;

// Command words
static constexpr uint16_t kCmdEnterConfig           = 0x00FF;
static constexpr uint16_t kCmdExitConfig            = 0x00FE;
static constexpr uint16_t kCmdWriteMaxGateAndHold   = 0x0060; // HLK-LD2410C max distance gate & hold
static constexpr uint16_t kCmdWriteGateSensitivity  = 0x0064; // HLK-LD2410C distance gate motion/static sensitivity
static constexpr uint16_t kCmdWriteCommonParams     = 0x0070; // HLK-LD2410S common parameters
static constexpr uint16_t kCmdReadCommonParams      = 0x0071;
static constexpr uint16_t kCmdSwitchOutputMode      = 0x007A;
static constexpr uint16_t kAckBitMask               = 0x0100;

// Parameter words for HLK-LD2410C commands 0x0060 & 0x0064
static constexpr uint16_t kLd2410cParamMaxMovingGate     = 0x0000;
static constexpr uint16_t kLd2410cParamMaxStationaryGate = 0x0001;
static constexpr uint16_t kLd2410cParamUnoccupiedHoldSec = 0x0002;
static constexpr uint16_t kLd2410cParamGateIndex         = 0x0000;
static constexpr uint16_t kLd2410cParamMotionSens        = 0x0001;
static constexpr uint16_t kLd2410cParamStationarySens    = 0x0002;
static constexpr uint16_t kLd2410cAllGates               = 0xFFFF;
static constexpr uint8_t  kLd2410cReportHead             = 0xAA;
static constexpr uint8_t  kLd2410cReportTail             = 0x55;
static constexpr uint8_t  kLd2410cReportCheck            = 0x00;
static constexpr uint32_t kLd2410cMinGate                = 2u;
static constexpr uint32_t kLd2410cMaxGate                = 8u;

// Common parameter IDs for command 0x0070
static constexpr uint16_t kParamStatusReportFreq   = 0x0002;
static constexpr uint16_t kParamFarthestGate       = 0x0005;
static constexpr uint16_t kParamUnoccupiedHoldSec  = 0x0006;
static constexpr uint16_t kParamNearestGate        = 0x000A;
static constexpr uint16_t kParamResponseSpeed      = 0x000B;
static constexpr uint16_t kParamDistanceReportFreq = 0x000C;

// Output mode values for command 0x007A
static constexpr uint32_t kOutputModeMinimal  = 0x00000000u;
static constexpr uint32_t kOutputModeStandard = 0x00000001u;

// Default parameter presets for a 3 m^3 bathroom (~1.5 x 1.5 x 2.2 m)
static constexpr uint32_t kDefaultBathroomMaxGate         = 3u;   // 2.10 m (LD2410S) / 2.25 m (LD2410C)
static constexpr uint32_t kDefaultBathroomMinGate         = 0u;   // 0.00 m
static constexpr uint32_t kDefaultBathroomHoldSec         = 30u;  // 30 s
static constexpr uint32_t kDefaultReportFreqTenthsHz      = 80u;  // 8.0 Hz (125 ms frame interval)
static constexpr uint32_t kDefaultResponseSpeedNormal     = 5u;   // Normal
static constexpr uint32_t kDefaultResponseSpeedFast       = 10u;  // Fast (instant light-switch response)
static constexpr uint16_t kGateWidthMm                    = 700u; // 0.70 m per HLK-LD2410S range gate
static constexpr uint16_t kLd2410cGateWidthMm             = 750u; // 0.75 m per HLK-LD2410C range gate
#if defined(CONFIG_APP_RADAR_LD2410C)
static constexpr uint16_t kActiveGateWidthMm              = kLd2410cGateWidthMm;
#else
static constexpr uint16_t kActiveGateWidthMm              = kGateWidthMm;
#endif
static constexpr uint16_t kDefaultMaxBathroomDistanceMm   =
    static_cast<uint16_t>(kDefaultBathroomMaxGate * kGateWidthMm); // 2100 mm (Gate 3 boundary)

// Exact serialized command frame sizes
static constexpr size_t kEnterConfigFrameSize             = 14;
static constexpr size_t kExitConfigFrameSize              = 12;
static constexpr size_t kLd2410cWriteMaxGateFrameSize     = 30;
static constexpr size_t kLd2410cWriteGateSensFrameSize    = 30;
static constexpr size_t kWriteCommonParamsFrameSize       = 48;
static constexpr size_t kSwitchOutputModeFrameSize        = 18;

/**
 * @brief Build 0x00FF Enter Configuration Mode command frame (14 bytes).
 * @return Frame length in bytes, or 0 if maxLen < 14.
 */
size_t BuildEnterConfigCmd(uint8_t *outBuf, size_t maxLen);

/**
 * @brief Build 0x00FE Exit Configuration Mode command frame (12 bytes).
 * @return Frame length in bytes, or 0 if maxLen < 12.
 */
size_t BuildExitConfigCmd(uint8_t *outBuf, size_t maxLen);

/**
 * @brief Build HLK-LD2410C 0x0060 Write Max Distance Gate & Unoccupied Duration command frame (30 bytes).
 * @return Frame length in bytes, or 0 if maxLen < 30.
 */
size_t BuildLd2410cWriteMaxGateAndHoldCmd(const Ld2410cConfigParams &params, uint8_t *outBuf, size_t maxLen);

/**
 * @brief Build HLK-LD2410C 0x0064 Write Distance Gate Sensitivity command frame (30 bytes).
 * @param gate Gate index 0..8, or kLd2410cAllGates (0xFFFF) to set all gates simultaneously.
 * @param motionSensitivity Motion trigger threshold (0..100).
 * @param stationarySensitivity Stationary hold threshold (0..100).
 * @return Frame length in bytes, or 0 if maxLen < 30.
 */
size_t BuildLd2410cWriteGateSensitivityCmd(uint16_t gate,
                                           uint32_t motionSensitivity,
                                           uint32_t stationarySensitivity,
                                           uint8_t *outBuf,
                                           size_t maxLen);

/**
 * @brief Build 0x0070 Write Common Parameters command frame (48 bytes).
 * @return Frame length in bytes, or 0 if maxLen < 48.
 */
size_t BuildWriteCommonParamsCmd(const Ld2410sConfigParams &params, uint8_t *outBuf, size_t maxLen);

/**
 * @brief Build 0x007A Switch Output Mode command frame (18 bytes).
 * @param outputMode kOutputModeMinimal (0) for 5-byte low-power frames, kOutputModeStandard (1) for full frames.
 * @return Frame length in bytes, or 0 if maxLen < 18.
 */
size_t BuildSwitchOutputModeCmd(uint32_t outputMode, uint8_t *outBuf, size_t maxLen);

} // namespace Ld2410sProto

/**
 * @brief Streaming byte-by-byte parser for HLK-LD2410S and HLK-LD2410C UART frames.
 *        Safely handles Minimal 5-Byte frames (6E .. 62), Standard Report
 *        frames (F4 F3 F2 F1 .. F8 F7 F6 F5, including HLK-LD2410C 0xAA..0x55 frames),
 *        Command ACK frames (FD FC FB FA .. 04 03 02 01), and arbitrary line noise.
 */
class Ld2410sFrameParser {
public:
    static constexpr size_t kMaxFrameBufferSize = 160;
    static constexpr size_t kMaxPayloadSize     = 128;

    Ld2410sFrameParser();

    void Reset();

    /**
     * @brief Feed one received UART byte into the sliding-window parser.
     * @param byte Incoming byte from UART RX.
     * @param outFrame Populated when a valid frame is completed.
     * @return true if a complete valid frame was decoded into *outFrame.
     */
    bool PushByte(uint8_t byte, Ld2410sParsedFrame *outFrame);

private:
    void DiscardPrefix(size_t count);
    int TryParseMinimalFrame(Ld2410sParsedFrame *outFrame);
    int TryParseStdReportFrame(Ld2410sParsedFrame *outFrame);
    int TryParseAckFrame(Ld2410sParsedFrame *outFrame);
    bool TryParseBuffer(Ld2410sParsedFrame *outFrame);

    uint8_t mBuf[kMaxFrameBufferSize];
    size_t  mLen;
};

/**
 * @brief Deterministic Radial-Kinematic Motion Classifier & Boundary Gate for HLK-LD2410S.
 *
 * Synthesizes accurate BTHome Motion (0x21) alongside Occupancy (0x23) across both
 * Minimal 5-Byte (0x02) and Standard (0x02/0x03) HLK-LD2410S report frames:
 *   1. Clamps targets beyond maxValidDistanceMm (2100 mm for a 3 m^3 bathroom) to Unoccupied.
 *   2. Triggers motion=true on unoccupied -> occupied entry or >= 100 mm radial movement
 *      across all occupied frames (0x02 and 0x03).
 *   3. Never allows raw state bytes (0x02 or 0x03) to bypass the 5000 ms stillness decay
 *      timer when radial distance change is < 100 mm.
 *   4. Holds motion=true for 5000 ms after the last >= 100 mm movement, then transitions
 *      cleanly to motion=false (Clear / Stationary) while occupied stays true.
 *   5. Expires occupancy (occupied=false, distanceMm=0) after occupancyHoldWindowMs
 *      (default 30000 ms) of zero >= 100 mm radial movement so HLK-LD2410C stationary
 *      background reflections (state 0x02) never latch occupancy ON indefinitely.
 */
class Ld2410sMotionTracker {
public:
    static constexpr uint16_t kMotionDeltaThresholdMm       = 100u;  // 10 cm radial movement threshold
    static constexpr int64_t  kMotionHoldWindowMs           = 5000;  // 5.0 s active motion hold window
    static constexpr int64_t  kDefaultOccupancyHoldWindowMs = 30000; // 30.0 s stationary occupancy hold window
    static constexpr uint8_t  kLd2410cMinMovingEnergy       = 35u;   // Reject low-energy (<35) Doppler noise spikes
    static constexpr uint8_t  kMinConsecutiveMovingForHold  = 2u;    // Require >=2 moving frames when delta < 100 mm
    static constexpr uint8_t  kMinConsecutiveMovingToWake   = 3u;    // Require >=3 moving frames to wake if delta < 100 mm

    Ld2410sMotionTracker();

    void Reset();

    /**
     * @brief Record an immediate hardware OT2 rising-edge entry event at nowMs.
     */
    void NotifyEntryEdge(int64_t nowMs);

    /**
     * @brief Update report->motion, report->occupied, and report->state in-place.
     */
    void Update(Ld2410sReport *inoutReport,
                int64_t nowMs,
                uint16_t maxValidDistanceMm = Ld2410sProto::kDefaultMaxBathroomDistanceMm,
                int64_t occupancyHoldWindowMs = kDefaultOccupancyHoldWindowMs);

    uint16_t GetAnchorDistanceMm() const { return mLastMotionAnchorDistMm; }
    int64_t GetLastMotionTimestampMs() const { return mLastMotionDetectedMs; }

private:
    int64_t  mLastMotionDetectedMs;
    uint16_t mLastMotionAnchorDistMm;
    uint8_t  mConsecutiveMovingFrames;
    bool     mWasOccupied;
    bool     mHasMotionTimestamp;
};

