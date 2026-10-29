/*
 * Copyright (c) 2026 Craig McLean
 * HLK-LD2410S 24 GHz Ultra-Low-Power mmWave Radar Protocol Codec (Host-Testable)
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
        // Across HLK-LD2410S firmware revisions:
        //   - 0x01 with distanceCm == 0 means Unoccupied ("no body")
        //   - 0x01 with distanceCm > 0 means Moving target
        if (distCm == 0u) {
            state    = Ld2410sTargetState::Unoccupied;
            occupied = false;
            motion   = false;
        } else {
            state    = Ld2410sTargetState::Moving;
            occupied = true;
            motion   = true;
        }
    } else if (rawState == 0x02u) {
        state    = Ld2410sTargetState::Moving;
        occupied = true;
        motion   = true;
    } else {
        state    = Ld2410sTargetState::Stationary;
        occupied = true;
        motion   = false;
    }

    outFrame->type                  = Ld2410sFrameType::Report;
    outFrame->report.state          = state;
    outFrame->report.occupied       = occupied;
    outFrame->report.motion         = motion;
    outFrame->report.distanceCm     = distCm;
    outFrame->report.distanceMm     = CmToMmClamped(distCm, occupied);
    outFrame->report.isMinimalFrame = isMinimalFrame;
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

bool Ld2410sFrameParser::TryParseBuffer(Ld2410sParsedFrame *outFrame)
{
    using namespace Ld2410sProto;

    while (mLen > 0) {
        const uint8_t first = mBuf[0];

        // 1. Minimal 5-Byte Report Frame: 6E [state] [dist_lo] [dist_hi] 62
        if (first == kMinimalHeader) {
            if (mLen >= 2 && mBuf[1] > static_cast<uint8_t>(Ld2410sTargetState::Stationary)) {
                DiscardPrefix(1);
                continue;
            }
            if (mLen < kMinimalFrameSize) {
                return false; // Wait for remaining bytes
            }
            if (mBuf[4] == kMinimalFooter &&
                mBuf[1] <= static_cast<uint8_t>(Ld2410sTargetState::Stationary)) {
                const uint8_t rawState = mBuf[1];
                const uint16_t distCm  = ReadU16Le(&mBuf[2]);

                PopulateReportFromRaw(rawState, distCm, true, outFrame);
                DiscardPrefix(kMinimalFrameSize);
                return true;
            }

            // False 0x6E byte from line noise; advance window by 1 byte
            DiscardPrefix(1);
            continue;
        }

        // 2. Standard Report Frame: F4 F3 F2 F1 [len_lo] [len_hi] ... F8 F7 F6 F5
        if (first == kStdReportHeader[0]) {
            const size_t prefixCheck = mLen < 4 ? mLen : 4;
            bool headerMatch = true;
            for (size_t i = 1; i < prefixCheck; ++i) {
                if (mBuf[i] != kStdReportHeader[i]) {
                    headerMatch = false;
                    break;
                }
            }
            if (!headerMatch) {
                DiscardPrefix(1);
                continue;
            }
            if (mLen < 6) {
                return false;
            }
            const uint16_t payloadLen = ReadU16Le(&mBuf[4]);
            if (payloadLen < 3u || payloadLen > kMaxPayloadSize) {
                DiscardPrefix(1);
                continue;
            }
            const size_t totalFrameLen = static_cast<size_t>(payloadLen) + 10u;
            if (mLen < totalFrameLen) {
                return false;
            }
            if (memcmp(&mBuf[totalFrameLen - 4], kStdReportFooter, 4) == 0) {
                // Layout A: [type=0x01/0x02] [state] [dist_lo] [dist_hi] ... (e.g. 70-byte or 8-byte payload)
                if (payloadLen >= 4u &&
                    payloadLen != 3u &&
                    payloadLen != 69u &&
                    (mBuf[6] == 0x01u || mBuf[6] == 0x02u) &&
                    mBuf[7] <= static_cast<uint8_t>(Ld2410sTargetState::Stationary)) {
                    const uint8_t rawState = mBuf[7];
                    const uint16_t distCm  = ReadU16Le(&mBuf[8]);

                    PopulateReportFromRaw(rawState, distCm, false, outFrame);
                    DiscardPrefix(totalFrameLen);
                    return true;
                }
                // Layout B: [state] [dist_lo] [dist_hi] ... (e.g. 3-byte or 69-byte payload without type prefix)
                if (mBuf[6] <= static_cast<uint8_t>(Ld2410sTargetState::Stationary)) {
                    const uint8_t rawState = mBuf[6];
                    const uint16_t distCm  = ReadU16Le(&mBuf[7]);

                    PopulateReportFromRaw(rawState, distCm, false, outFrame);
                    DiscardPrefix(totalFrameLen);
                    return true;
                }
            }

            DiscardPrefix(1);
            continue;
        }

        // 3. Command ACK Frame: FD FC FB FA [len_lo] [len_hi] [ack_cmd_lo] [ack_cmd_hi] [status_lo] [status_hi] ... 04 03 02 01
        if (first == kCmdHeader[0]) {
            const size_t prefixCheck = mLen < 4 ? mLen : 4;
            bool headerMatch = true;
            for (size_t i = 1; i < prefixCheck; ++i) {
                if (mBuf[i] != kCmdHeader[i]) {
                    headerMatch = false;
                    break;
                }
            }
            if (!headerMatch) {
                DiscardPrefix(1);
                continue;
            }
            if (mLen < 6) {
                return false;
            }
            const uint16_t payloadLen = ReadU16Le(&mBuf[4]);
            if (payloadLen < 4u || payloadLen > kMaxPayloadSize) {
                DiscardPrefix(1);
                continue;
            }
            const size_t totalFrameLen = static_cast<size_t>(payloadLen) + 10u;
            if (mLen < totalFrameLen) {
                return false;
            }
            if (memcmp(&mBuf[totalFrameLen - 4], kCmdFooter, 4) == 0) {
                outFrame->type               = Ld2410sFrameType::Ack;
                outFrame->ack.ackCommandWord = ReadU16Le(&mBuf[6]);
                outFrame->ack.status         = ReadU16Le(&mBuf[8]);

                DiscardPrefix(totalFrameLen);
                return true;
            }

            DiscardPrefix(1);
            continue;
        }

        // Unrecognized start byte: advance sliding window by 1
        DiscardPrefix(1);
    }

    return false;
}
