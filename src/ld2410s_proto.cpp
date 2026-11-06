/*
 * Copyright (c) 2026 Craig McLean
 * HLK-LD2410S / HLK-LD2410C 24 GHz mmWave Radar Protocol Codec (Host-Testable)
 */

#include "ld2410s_proto.h"
#include <string.h>

namespace Ld2410sProto {

static void WriteU16Le(uint8_t *dst, uint16_t val)
{
    dst[0] = static_cast<uint8_t>(val & 0xFFu);
    dst[1] = static_cast<uint8_t>((val >> 8) & 0xFFu);
}

static void WriteU32Le(uint8_t *dst, uint32_t val)
{
    dst[0] = static_cast<uint8_t>(val & 0xFFu);
    dst[1] = static_cast<uint8_t>((val >> 8) & 0xFFu);
    dst[2] = static_cast<uint8_t>((val >> 16) & 0xFFu);
    dst[3] = static_cast<uint8_t>((val >> 24) & 0xFFu);
}

static uint16_t ReadU16Le(const uint8_t *src)
{
    return static_cast<uint16_t>(src[0]) |
           (static_cast<uint16_t>(src[1]) << 8);
}

static uint32_t ClampU32(uint32_t val, uint32_t minVal, uint32_t maxVal)
{
    if (val < minVal) {
        return minVal;
    }
    return (val > maxVal) ? maxVal : val;
}

static uint16_t CmToMmClamped(uint16_t distanceCm, bool occupied)
{
    if (!occupied) {
        return 0u;
    }
    uint32_t mm = static_cast<uint32_t>(distanceCm) * 10u;
    return mm > 65535u ? static_cast<uint16_t>(65535u) : static_cast<uint16_t>(mm);
}

static void PopulateReportFromRaw(uint8_t rawState,
                                  uint16_t distCm,
                                  bool isMinimalFrame,
                                  Ld2410sParsedFrame *outFrame)
{
    Ld2410sTargetState state = Ld2410sTargetState::NoTarget;
    bool occupied            = false;
    bool motion              = false;

    if (rawState == 0x00u) {
        state    = Ld2410sTargetState::NoTarget;
        occupied = false;
        motion   = false;
    } else if (rawState == 0x01u) {
        state    = Ld2410sTargetState::Unoccupied;
        occupied = false;
        motion   = false;
    } else if (rawState == 0x02u) {
        state    = Ld2410sTargetState::Stationary;
        occupied = true;
        motion   = false;
    } else {
        state    = Ld2410sTargetState::Moving;
        occupied = true;
        motion   = true;
    }

    outFrame->type                  = Ld2410sFrameType::Report;
    outFrame->report.state          = state;
    outFrame->report.occupied       = occupied;
    outFrame->report.motion         = motion;
    outFrame->report.distanceCm     = distCm;
    outFrame->report.distanceMm     = CmToMmClamped(distCm, occupied);
    outFrame->report.isMinimalFrame = isMinimalFrame;
}

static void PopulateLd2410cReportFromRaw(uint8_t rawState,
                                         uint16_t movingDistCm,
                                         uint16_t stationaryDistCm,
                                         uint16_t detectionDistCm,
                                         Ld2410sParsedFrame *outFrame)
{
    Ld2410sTargetState state = Ld2410sTargetState::NoTarget;
    bool occupied            = false;
    bool motion              = false;
    uint16_t distCm          = 0u;

    if (rawState == 0x01u) {
        // HLK-LD2410C 0x01 = Moving target (unlike HLK-LD2410S where 0x01 = Unoccupied)
        state    = Ld2410sTargetState::Moving;
        occupied = true;
        motion   = true;
        distCm   = (detectionDistCm > 0u)
                       ? detectionDistCm
                       : ((movingDistCm > 0u) ? movingDistCm : stationaryDistCm);
    } else if (rawState == 0x02u) {
        // HLK-LD2410C 0x02 = Stationary target
        state    = Ld2410sTargetState::Stationary;
        occupied = true;
        motion   = false;
        distCm   = (detectionDistCm > 0u)
                       ? detectionDistCm
                       : ((stationaryDistCm > 0u) ? stationaryDistCm : movingDistCm);
    } else if (rawState >= 0x03u) {
        // HLK-LD2410C 0x03 = Moving + Stationary target: use smoothed detectionDistCm first
        // (with fallback to movingDistCm/stationaryDistCm) so raw gate hopping does not jitter.
        state    = Ld2410sTargetState::Moving;
        occupied = true;
        motion   = true;
        distCm   = (detectionDistCm > 0u)
                       ? detectionDistCm
                       : ((movingDistCm > 0u) ? movingDistCm : stationaryDistCm);
    }

    // On HLK-LD2410C, targets in Gate 0 (< 75 cm, right in front of the radar) can report
    // 0 cm in the gate-indexed distance fields; map Gate 0 occupied targets to 35 cm (350 mm)
    // so downstream distance > 0 checks never discard close-range detections.
    if (occupied && distCm == 0u) {
        distCm = 35u;
    }

    outFrame->type                  = Ld2410sFrameType::Report;
    outFrame->report.state          = state;
    outFrame->report.occupied       = occupied;
    outFrame->report.motion         = motion;
    outFrame->report.distanceCm     = distCm;
    outFrame->report.distanceMm     = CmToMmClamped(distCm, occupied);
    outFrame->report.isMinimalFrame = false;
}

size_t BuildEnterConfigCmd(uint8_t *outBuf, size_t maxLen)
{
    if (!outBuf || maxLen < kEnterConfigFrameSize) {
        return 0;
    }

    memcpy(&outBuf[0], kCmdHeader, 4);
    WriteU16Le(&outBuf[4], 4u); // 2B cmd + 2B value
    WriteU16Le(&outBuf[6], kCmdEnterConfig);
    WriteU16Le(&outBuf[8], 0x0001u);
    memcpy(&outBuf[10], kCmdFooter, 4);
    return kEnterConfigFrameSize;
}

size_t BuildExitConfigCmd(uint8_t *outBuf, size_t maxLen)
{
    if (!outBuf || maxLen < kExitConfigFrameSize) {
        return 0;
    }

    memcpy(&outBuf[0], kCmdHeader, 4);
    WriteU16Le(&outBuf[4], 2u); // 2B cmd only
    WriteU16Le(&outBuf[6], kCmdExitConfig);
    memcpy(&outBuf[8], kCmdFooter, 4);
    return kExitConfigFrameSize;
}

size_t BuildLd2410cWriteMaxGateAndHoldCmd(const Ld2410cConfigParams &params, uint8_t *outBuf, size_t maxLen)
{
    if (!outBuf || maxLen < kLd2410cWriteMaxGateFrameSize) {
        return 0;
    }

    struct ParamEntry {
        uint16_t id;
        uint32_t val;
    };

    const ParamEntry entries[3] = {
        {kLd2410cParamMaxMovingGate,     ClampU32(params.maxMovingGate, kLd2410cMinGate, kLd2410cMaxGate)},
        {kLd2410cParamMaxStationaryGate, ClampU32(params.maxStationaryGate, kLd2410cMinGate, kLd2410cMaxGate)},
        {kLd2410cParamUnoccupiedHoldSec, ClampU32(params.unoccupiedHoldSec, 0u, 65535u)},
    };

    memcpy(&outBuf[0], kCmdHeader, 4);
    WriteU16Le(&outBuf[4], 2u + 3u * 6u); // 20 bytes (0x0014)
    WriteU16Le(&outBuf[6], kCmdWriteMaxGateAndHold);

    size_t offset = 8;
    for (size_t i = 0; i < 3; ++i) {
        WriteU16Le(&outBuf[offset], entries[i].id);
        WriteU32Le(&outBuf[offset + 2], entries[i].val);
        offset += 6;
    }

    memcpy(&outBuf[offset], kCmdFooter, 4);
    return kLd2410cWriteMaxGateFrameSize;
}

size_t BuildWriteCommonParamsCmd(const Ld2410sConfigParams &params, uint8_t *outBuf, size_t maxLen)
{
    if (!outBuf || maxLen < kWriteCommonParamsFrameSize) {
        return 0;
    }

    struct ParamEntry {
        uint16_t id;
        uint32_t val;
    };

    const ParamEntry entries[6] = {
        {kParamFarthestGate,       params.farthestGate},
        {kParamNearestGate,        params.nearestGate},
        {kParamUnoccupiedHoldSec,  params.unoccupiedHoldSec},
        {kParamStatusReportFreq,   params.statusReportFreqHz10},
        {kParamDistanceReportFreq, params.distanceReportFreqHz10},
        {kParamResponseSpeed,      params.responseSpeed},
    };

    memcpy(&outBuf[0], kCmdHeader, 4);
    WriteU16Le(&outBuf[4], 2u + 6u * 6u); // 38 bytes (0x0026)
    WriteU16Le(&outBuf[6], kCmdWriteCommonParams);

    size_t offset = 8;
    for (size_t i = 0; i < 6; ++i) {
        WriteU16Le(&outBuf[offset], entries[i].id);
        WriteU32Le(&outBuf[offset + 2], entries[i].val);
        offset += 6;
    }

    memcpy(&outBuf[offset], kCmdFooter, 4);
    return kWriteCommonParamsFrameSize;
}

size_t BuildSwitchOutputModeCmd(uint32_t outputMode, uint8_t *outBuf, size_t maxLen)
{
    if (!outBuf || maxLen < kSwitchOutputModeFrameSize) {
        return 0;
    }

    memcpy(&outBuf[0], kCmdHeader, 4);
    WriteU16Le(&outBuf[4], 8u); // 2B cmd + 2B reserved (0x0000) + 4B mode
    WriteU16Le(&outBuf[6], kCmdSwitchOutputMode);
    WriteU16Le(&outBuf[8], 0x0000u);
    WriteU32Le(&outBuf[10], outputMode);
    memcpy(&outBuf[14], kCmdFooter, 4);
    return kSwitchOutputModeFrameSize;
}

} // namespace Ld2410sProto

Ld2410sFrameParser::Ld2410sFrameParser() : mLen(0)
{
    memset(mBuf, 0, sizeof(mBuf));
}

void Ld2410sFrameParser::Reset()
{
    mLen = 0;
}

void Ld2410sFrameParser::DiscardPrefix(size_t count)
{
    if (count >= mLen) {
        mLen = 0;
        return;
    }
    memmove(&mBuf[0], &mBuf[count], mLen - count);
    mLen -= count;
}

bool Ld2410sFrameParser::PushByte(uint8_t byte, Ld2410sParsedFrame *outFrame)
{
    if (!outFrame) {
        return false;
    }

    if (mLen >= kMaxFrameBufferSize) {
        DiscardPrefix(1);
    }
    mBuf[mLen++] = byte;

    return TryParseBuffer(outFrame);
}

int Ld2410sFrameParser::TryParseMinimalFrame(Ld2410sParsedFrame *outFrame)
{
    using namespace Ld2410sProto;

    if (mLen >= 2 && mBuf[1] > static_cast<uint8_t>(Ld2410sTargetState::Moving)) {
        DiscardPrefix(1);
        return -1;
    }
    if (mLen < kMinimalFrameSize) {
        return 0; // Wait for remaining bytes
    }
    if (mBuf[4] == kMinimalFooter &&
        mBuf[1] <= static_cast<uint8_t>(Ld2410sTargetState::Moving)) {
        const uint8_t rawState = mBuf[1];
        const uint16_t distCm  = ReadU16Le(&mBuf[2]);

        PopulateReportFromRaw(rawState, distCm, true, outFrame);
        DiscardPrefix(kMinimalFrameSize);
        return 1;
    }

    DiscardPrefix(1);
    return -1;
}

int Ld2410sFrameParser::TryParseStdReportFrame(Ld2410sParsedFrame *outFrame)
{
    using namespace Ld2410sProto;

    const size_t prefixCheck = mLen < 4 ? mLen : 4;
    for (size_t i = 1; i < prefixCheck; ++i) {
        if (mBuf[i] != kStdReportHeader[i]) {
            DiscardPrefix(1);
            return -1;
        }
    }
    if (mLen < 6) {
        return 0;
    }
    const uint16_t payloadLen = ReadU16Le(&mBuf[4]);
    if (payloadLen < 3u || payloadLen > kMaxPayloadSize) {
        DiscardPrefix(1);
        return -1;
    }
    if (mLen >= 7 && mBuf[6] > static_cast<uint8_t>(Ld2410sTargetState::Moving)) {
        DiscardPrefix(1);
        return -1;
    }
    if (mLen >= 8 &&
        mBuf[7] > static_cast<uint8_t>(Ld2410sTargetState::Moving) &&
        mBuf[7] != kLd2410cReportHead) {
        DiscardPrefix(1);
        return -1;
    }
    if (mLen >= 9 &&
        mBuf[7] == kLd2410cReportHead &&
        mBuf[8] > static_cast<uint8_t>(Ld2410sTargetState::Moving)) {
        DiscardPrefix(1);
        return -1;
    }
    const size_t totalFrameLen = static_cast<size_t>(payloadLen) + 10u;
    if (mLen < totalFrameLen) {
        return 0;
    }
    if (memcmp(&mBuf[totalFrameLen - 4], kStdReportFooter, 4) == 0) {
        // Layout C (HLK-LD2410C): [type=0x01/0x02] [0xAA] [state] [mov_cm:2] [mov_e] [stat_cm:2] [stat_e] [det_cm:2] ... [0x55] [0x00]
        if (payloadLen >= 13u &&
            (mBuf[6] == 0x01u || mBuf[6] == 0x02u) &&
            mBuf[7] == kLd2410cReportHead &&
            mBuf[8] <= static_cast<uint8_t>(Ld2410sTargetState::Moving) &&
            mBuf[totalFrameLen - 6] == kLd2410cReportTail) {
            PopulateLd2410cReportFromRaw(mBuf[8],
                                         ReadU16Le(&mBuf[9]),
                                         ReadU16Le(&mBuf[12]),
                                         ReadU16Le(&mBuf[15]),
                                         outFrame);
            DiscardPrefix(totalFrameLen);
            return 1;
        }
        // Layout A (HLK-LD2410S): [type=0x01/0x02] [state] [dist_lo] [dist_hi] ...
        if (payloadLen >= 4u &&
            payloadLen != 3u &&
            payloadLen != 69u &&
            (mBuf[6] == 0x01u || mBuf[6] == 0x02u) &&
            mBuf[7] <= static_cast<uint8_t>(Ld2410sTargetState::Moving)) {
            PopulateReportFromRaw(mBuf[7], ReadU16Le(&mBuf[8]), false, outFrame);
            DiscardPrefix(totalFrameLen);
            return 1;
        }
        // Layout B (HLK-LD2410S): [state] [dist_lo] [dist_hi] ...
        if (mBuf[6] <= static_cast<uint8_t>(Ld2410sTargetState::Moving)) {
            PopulateReportFromRaw(mBuf[6], ReadU16Le(&mBuf[7]), false, outFrame);
            DiscardPrefix(totalFrameLen);
            return 1;
        }
    }

    DiscardPrefix(1);
    return -1;
}

int Ld2410sFrameParser::TryParseAckFrame(Ld2410sParsedFrame *outFrame)
{
    using namespace Ld2410sProto;

    const size_t prefixCheck = mLen < 4 ? mLen : 4;
    for (size_t i = 1; i < prefixCheck; ++i) {
        if (mBuf[i] != kCmdHeader[i]) {
            DiscardPrefix(1);
            return -1;
        }
    }
    if (mLen < 6) {
        return 0;
    }
    const uint16_t payloadLen = ReadU16Le(&mBuf[4]);
    if (payloadLen < 4u || payloadLen > kMaxPayloadSize) {
        DiscardPrefix(1);
        return -1;
    }
    const size_t totalFrameLen = static_cast<size_t>(payloadLen) + 10u;
    if (mLen < totalFrameLen) {
        return 0;
    }
    if (memcmp(&mBuf[totalFrameLen - 4], kCmdFooter, 4) == 0) {
        outFrame->type               = Ld2410sFrameType::Ack;
        outFrame->ack.ackCommandWord = ReadU16Le(&mBuf[6]);
        outFrame->ack.status         = ReadU16Le(&mBuf[8]);

        DiscardPrefix(totalFrameLen);
        return 1;
    }

    DiscardPrefix(1);
    return -1;
}

bool Ld2410sFrameParser::TryParseBuffer(Ld2410sParsedFrame *outFrame)
{
    using namespace Ld2410sProto;

    while (mLen > 0) {
        const uint8_t first = mBuf[0];
        int res = -1;

        if (first == kMinimalHeader) {
            res = TryParseMinimalFrame(outFrame);
        } else if (first == kStdReportHeader[0]) {
            res = TryParseStdReportFrame(outFrame);
        } else if (first == kCmdHeader[0]) {
            res = TryParseAckFrame(outFrame);
        } else {
            DiscardPrefix(1);
            continue;
        }

        if (res > 0) {
            return true;
        }
        if (res == 0) {
            return false;
        }
    }

    return false;
}

Ld2410sMotionTracker::Ld2410sMotionTracker()
    : mLastMotionDetectedMs(0),
      mLastMotionAnchorDistMm(0u),
      mWasOccupied(false),
      mHasMotionTimestamp(false)
{
}

void Ld2410sMotionTracker::Reset()
{
    mLastMotionDetectedMs   = 0;
    mLastMotionAnchorDistMm = 0u;
    mWasOccupied            = false;
    mHasMotionTimestamp     = false;
}

void Ld2410sMotionTracker::NotifyEntryEdge(int64_t nowMs)
{
    mWasOccupied        = true;
    mHasMotionTimestamp = true;
    mLastMotionDetectedMs = nowMs;
}

void Ld2410sMotionTracker::Update(Ld2410sReport *inoutReport,
                                  int64_t nowMs,
                                  uint16_t maxValidDistanceMm,
                                  int64_t occupancyHoldWindowMs)
{
    if (!inoutReport) {
        return;
    }

    // Clamp far-field reflections beyond the configured bathroom boundary (e.g. > 2100 mm)
    if (inoutReport->occupied && maxValidDistanceMm > 0u && inoutReport->distanceMm > maxValidDistanceMm) {
        inoutReport->state      = Ld2410sTargetState::Unoccupied;
        inoutReport->occupied   = false;
        inoutReport->motion     = false;
        inoutReport->distanceCm = 0u;
        inoutReport->distanceMm = 0u;
        Reset();
        return;
    }

    if (!inoutReport->occupied) {
        inoutReport->motion     = false;
        inoutReport->distanceCm = 0u;
        inoutReport->distanceMm = 0u;
        if (inoutReport->state != Ld2410sTargetState::NoTarget) {
            inoutReport->state = Ld2410sTargetState::Unoccupied;
        }
        Reset();
        return;
    }

    if (!mWasOccupied) {
        // Unoccupied -> Occupied entry always represents active motion
        mWasOccupied            = true;
        mHasMotionTimestamp     = true;
        mLastMotionDetectedMs   = nowMs;
        mLastMotionAnchorDistMm = inoutReport->distanceMm;
    } else {
        // Evaluate radial distance kinematics (>= 100 mm).
        // On Minimal 5-Byte HLK-LD2410S frames (isMinimalFrame == true), state 0x02 is emitted for
        // both moving and stationary targets, so any >= 100 mm shift triggers motion.
        // On full standard/HLK-LD2410C frames (!isMinimalFrame), the radar explicitly reports Doppler
        // movement via state == Moving (0x01/0x03 on LD2410C, 0x03 on LD2410S), so Stationary-only
        // (0x02) multipath gate hops must never reset the motion or occupancy hold timers.
        const bool wasExpired = mHasMotionTimestamp &&
                                (occupancyHoldWindowMs > 0) &&
                                ((nowMs - mLastMotionDetectedMs) >= occupancyHoldWindowMs);
        const bool canTriggerMotion =
            inoutReport->isMinimalFrame ||
            inoutReport->motion ||
            (inoutReport->state == Ld2410sTargetState::Moving);

        if (mLastMotionAnchorDistMm == 0u && inoutReport->distanceMm > 0u) {
            if (!wasExpired || canTriggerMotion) {
                mLastMotionAnchorDistMm = inoutReport->distanceMm;
                if (!mHasMotionTimestamp || wasExpired) {
                    mHasMotionTimestamp   = true;
                    mLastMotionDetectedMs = nowMs;
                }
            }
        } else {
            const uint16_t distDeltaMm =
                (inoutReport->distanceMm > mLastMotionAnchorDistMm)
                    ? static_cast<uint16_t>(inoutReport->distanceMm - mLastMotionAnchorDistMm)
                    : static_cast<uint16_t>(mLastMotionAnchorDistMm - inoutReport->distanceMm);

            if (distDeltaMm >= kMotionDeltaThresholdMm && canTriggerMotion) {
                mLastMotionAnchorDistMm = inoutReport->distanceMm;
                mHasMotionTimestamp     = true;
                mLastMotionDetectedMs   = nowMs;
            }
        }
    }

    const int64_t elapsedMs = nowMs - mLastMotionDetectedMs;

    // Expire stuck stationary occupancy (e.g. HLK-LD2410C state 0x02 latched on static clutter)
    // after occupancyHoldWindowMs (default 30 s) without >= 100 mm radial movement, while keeping
    // mWasOccupied and mLastMotionAnchorDistMm latched so the same static reflection stays ignored.
    if (occupancyHoldWindowMs > 0 && mHasMotionTimestamp && elapsedMs >= occupancyHoldWindowMs) {
        inoutReport->state      = Ld2410sTargetState::Unoccupied;
        inoutReport->occupied   = false;
        inoutReport->motion     = false;
        inoutReport->distanceCm = 0u;
        inoutReport->distanceMm = 0u;
        return;
    }

    const bool activeMotion = mHasMotionTimestamp &&
                              (elapsedMs >= 0) &&
                              (elapsedMs < kMotionHoldWindowMs);

    inoutReport->motion = activeMotion;
    inoutReport->state  = activeMotion ? Ld2410sTargetState::Moving
                                       : Ld2410sTargetState::Stationary;
}

