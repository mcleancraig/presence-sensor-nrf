/*
 * Copyright (c) 2026 Craig McLean
 * Wireless MQTT FOTA (Firmware Over-The-Air) Updater & UF2 Bootloader Trigger
 */

#include "ota_updater.h"
#include "version.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace OtaProto {

static uint32_t ReadU32Le(const uint8_t *p)
{
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

uint32_t Crc32(const uint8_t *data, size_t len, uint32_t initialCrc)
{
    if (!data && len > 0u) {
        return initialCrc;
    }

    uint32_t crc = ~initialCrc;
    for (size_t i = 0; i < len; ++i) {
        crc ^= static_cast<uint32_t>(data[i]);
        for (uint8_t bit = 0; bit < 8u; ++bit) {
            const uint32_t mask = -(crc & 1u);
            crc = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return ~crc;
}

bool ValidateCortexM4VectorTable(const uint8_t *firstBytes, size_t len)
{
    if (!firstBytes || len < 8u) {
        return false;
    }

    const uint32_t initialMsp = ReadU32Le(&firstBytes[0]);
    const uint32_t resetPc    = ReadU32Le(&firstBytes[4]);

    const bool mspValid = (initialMsp >= (kNrf52840SramBase + 256u)) &&
                          (initialMsp <= kNrf52840SramEnd) &&
                          ((initialMsp & 0x3u) == 0u);
    const bool pcValid  = ((resetPc & 0x1u) == 1u) &&
                          (resetPc >= kSlot0BaseAddress) &&
                          (resetPc < (kSlot0BaseAddress + kMaxFirmwareSize));
    return mspValid && pcValid;
}

static size_t FormatTopicWithSuffix(const char *nodeSlug,
                                    const char *suffix,
                                    char *outBuf,
                                    size_t maxLen)
{
    if (!nodeSlug || !suffix || !outBuf || maxLen == 0u || nodeSlug[0] == '\0') {
        return 0u;
    }
    const int n = snprintf(outBuf, maxLen, "presence_sensor/%s/ota/%s", nodeSlug, suffix);
    if (n < 0 || static_cast<size_t>(n) >= maxLen) {
        outBuf[0] = '\0';
        return 0u;
    }
    return static_cast<size_t>(n);
}

size_t FormatCmdTopic(const char *nodeSlug, char *outBuf, size_t maxLen)
{
    return FormatTopicWithSuffix(nodeSlug, "cmd", outBuf, maxLen);
}

size_t FormatChunkTopic(const char *nodeSlug, char *outBuf, size_t maxLen)
{
    return FormatTopicWithSuffix(nodeSlug, "chunk", outBuf, maxLen);
}

size_t FormatStatusTopic(const char *nodeSlug, char *outBuf, size_t maxLen)
{
    return FormatTopicWithSuffix(nodeSlug, "status", outBuf, maxLen);
}

static bool ExtractUintField(const char *json, const char *key, uint32_t *outVal)
{
    if (!json || !key || !outVal) {
        return false;
    }
    const char *pos = strstr(json, key);
    if (!pos) {
        return false;
    }
    pos += strlen(key);
    while (*pos == ' ' || *pos == '\t' || *pos == ':') {
        ++pos;
    }
    if (*pos < '0' || *pos > '9') {
        return false;
    }
    char *endPtr = nullptr;
    const unsigned long parsed = strtoul(pos, &endPtr, 10);
    if (endPtr == pos) {
        return false;
    }
    *outVal = static_cast<uint32_t>(parsed);
    return true;
}

bool ParseCommandJson(const char *json, size_t len, OtaCommand *outCmd)
{
    if (!json || len == 0u || !outCmd) {
        return false;
    }

    char buf[192];
    const size_t copyLen = (len < (sizeof(buf) - 1u)) ? len : (sizeof(buf) - 1u);
    memcpy(buf, json, copyLen);
    buf[copyLen] = '\0';

    *outCmd = {OtaCommandAction::None, 0u, 0u};

    if (strstr(buf, "\"ping\"") != nullptr) {
        outCmd->action = OtaCommandAction::Ping;
        return true;
    }
    if (strstr(buf, "\"bootloader\"") != nullptr) {
        outCmd->action = OtaCommandAction::Bootloader;
        return true;
    }
    if (strstr(buf, "\"apply\"") != nullptr) {
        outCmd->action = OtaCommandAction::Apply;
        return true;
    }
    if (strstr(buf, "\"abort\"") != nullptr) {
        outCmd->action = OtaCommandAction::Abort;
        return true;
    }
    if (strstr(buf, "\"begin\"") != nullptr) {
        uint32_t size  = 0u;
        uint32_t crc32 = 0u;
        if (!ExtractUintField(buf, "\"size\"", &size) ||
            !ExtractUintField(buf, "\"crc32\"", &crc32)) {
            return false;
        }
        outCmd->action = OtaCommandAction::Begin;
        outCmd->size   = size;
        outCmd->crc32  = crc32;
        return true;
    }
    return false;
}

bool ParseChunkHeader(const uint8_t *buf,
                      size_t len,
                      uint32_t *outOffset,
                      const uint8_t **outData,
                      size_t *outDataLen)
{
    if (!buf || len <= kChunkHeaderSize || !outOffset || !outData || !outDataLen) {
        return false;
    }
    const size_t dataLen = len - kChunkHeaderSize;
    if (dataLen > kMaxChunkDataSize) {
        return false;
    }
    *outOffset  = ReadU32Le(buf);
    *outData    = &buf[kChunkHeaderSize];
    *outDataLen = dataLen;
    return true;
}

} // namespace OtaProto

#ifdef __ZEPHYR__

#include <hal/nrf_nvmc.h>
#include <hal/nrf_power.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/reboot.h>

LOG_MODULE_REGISTER(ota_updater, LOG_LEVEL_INF);

namespace {

/**
 * @brief Self-contained SRAM-resident flash installer.
 *        Runs with all interrupts masked, erases Slot 0 (0x00001000), copies the
 *        verified image from Slot 1 (0x00076000) into Slot 0 via NRF_NVMC, and
 *        triggers an immediate Cortex-M4 system reset.
 */
__ramfunc __attribute__((noinline)) void ApplyStagedImageFromRamAndReset(uint32_t dstAddr,
                                                                         uint32_t srcAddr,
                                                                         uint32_t byteLen)
{
    __disable_irq();

    volatile uint32_t *const nvmcReady     = reinterpret_cast<volatile uint32_t *>(0x4001E400UL);
    volatile uint32_t *const nvmcConfig    = reinterpret_cast<volatile uint32_t *>(0x4001E504UL);
    volatile uint32_t *const nvmcErasePage = reinterpret_cast<volatile uint32_t *>(0x4001E508UL);
    volatile uint32_t *const wdtRunStatus  = reinterpret_cast<volatile uint32_t *>(0x40010418UL);
    volatile uint32_t *const wdtRr0        = reinterpret_cast<volatile uint32_t *>(0x40010600UL);
    volatile uint32_t *const scbAircr      = reinterpret_cast<volatile uint32_t *>(0xE000ED0CUL);

    const uint32_t alignedBytes =
        (byteLen + (OtaProto::kFlashPageSize - 1u)) & ~(OtaProto::kFlashPageSize - 1u);

    // 1. Erase target Slot 0 pages (4096 bytes per page)
    *nvmcConfig = 2UL; // NVMC_CONFIG_WEN_Een (Erase enabled)
    while ((*nvmcReady & 1UL) == 0UL) {
    }

    for (uint32_t offset = 0u; offset < alignedBytes; offset += OtaProto::kFlashPageSize) {
        if ((*wdtRunStatus & 1UL) != 0UL) {
            *wdtRr0 = 0x6E524635UL;
        }
        *nvmcErasePage = dstAddr + offset;
        while ((*nvmcReady & 1UL) == 0UL) {
        }
    }

    // 2. Copy 32-bit words from Slot 1 staging into Slot 0
    *nvmcConfig = 1UL; // NVMC_CONFIG_WEN_Wen (Write enabled)
    while ((*nvmcReady & 1UL) == 0UL) {
    }

    const uint32_t wordCount = (byteLen + 3u) / 4u;
    volatile uint32_t *dstWords = reinterpret_cast<volatile uint32_t *>(dstAddr);
    const volatile uint32_t *srcWords = reinterpret_cast<const volatile uint32_t *>(srcAddr);

    for (uint32_t i = 0u; i < wordCount; ++i) {
        if ((i & 0x3FFu) == 0u && (*wdtRunStatus & 1UL) != 0UL) {
            *wdtRr0 = 0x6E524635UL;
        }
        dstWords[i] = srcWords[i];
        while ((*nvmcReady & 1UL) == 0UL) {
        }
    }

    // 3. Return NVMC to read-only mode and reboot into new firmware
    *nvmcConfig = 0UL; // NVMC_CONFIG_WEN_Ren
    while ((*nvmcReady & 1UL) == 0UL) {
    }

    __DSB();
    __ISB();
    *scbAircr = (0x5FAUL << 16) | (1UL << 2); // VECTKEY | SYSRESETREQ
    while (true) {
    }
}

} // namespace

OtaUpdater::OtaUpdater()
    : mFlashDev(DEVICE_DT_GET_OR_NULL(DT_CHOSEN(zephyr_flash_controller))),
      mCmdTopic{},
      mChunkTopic{},
      mStatusTopic{},
      mExpectedSize(0u),
      mExpectedCrc32(0u),
      mReceivedBytes(0u),
      mErasedEndOffset(0u),
      mDiag{},
      mActive(false)
{
}

int OtaUpdater::Init(const char *nodeSlug)
{
    if (!nodeSlug || nodeSlug[0] == '\0') {
        return -EINVAL;
    }
    OtaProto::FormatCmdTopic(nodeSlug, mCmdTopic, sizeof(mCmdTopic));
    OtaProto::FormatChunkTopic(nodeSlug, mChunkTopic, sizeof(mChunkTopic));
    OtaProto::FormatStatusTopic(nodeSlug, mStatusTopic, sizeof(mStatusTopic));

    if (!mFlashDev || !device_is_ready(mFlashDev)) {
        LOG_WRN("Flash controller not ready for FOTA");
        return -ENODEV;
    }

    LOG_INF("Wireless MQTT FOTA ready: cmd=%s, chunk=%s, status=%s (slot1=0x%08X, max=%u KB)",
            mCmdTopic,
            mChunkTopic,
            mStatusTopic,
            OtaProto::kSlot1StagingAddress,
            static_cast<unsigned>(OtaProto::kMaxFirmwareSize / 1024u));
    return 0;
}

int OtaUpdater::EnsureStagingErasedUpTo(uint32_t endOffset)
{
    if (!mFlashDev || !device_is_ready(mFlashDev)) {
        return -ENODEV;
    }
    while (mErasedEndOffset < endOffset) {
        const off_t pageAddr =
            static_cast<off_t>(OtaProto::kSlot1StagingAddress + mErasedEndOffset);
        int ret = flash_erase(mFlashDev, pageAddr, OtaProto::kFlashPageSize);
        if (ret != 0) {
            LOG_ERR("flash_erase failed at 0x%08X (err=%d)",
                    static_cast<unsigned>(pageAddr),
                    ret);
            return ret;
        }
        mErasedEndOffset += OtaProto::kFlashPageSize;
    }
    return 0;
}

bool OtaUpdater::VerifyStagedImage(uint32_t *outCalculatedCrc32) const
{
    if (mExpectedSize < OtaProto::kMinFirmwareSize ||
        mExpectedSize > OtaProto::kMaxFirmwareSize) {
        return false;
    }

    const auto *stagedPtr =
        reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(OtaProto::kSlot1StagingAddress));
    if (!OtaProto::ValidateCortexM4VectorTable(stagedPtr, 16u)) {
        LOG_ERR("Staged image vector table invalid");
        return false;
    }

    const uint32_t calcCrc = OtaProto::Crc32(stagedPtr, mExpectedSize);
    if (outCalculatedCrc32) {
        *outCalculatedCrc32 = calcCrc;
    }
    return calcCrc == mExpectedCrc32;
}

void OtaUpdater::HandleCmdMessage(const char *json,
                                  size_t len,
                                  StatusPublishFn publishFn,
                                  void *publishCtx)
{
    OtaCommand cmd{};
    char statusBuf[256] = {};

    if (!OtaProto::ParseCommandJson(json, len, &cmd)) {
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"invalid_cmd\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    switch (cmd.action) {
    case OtaCommandAction::Ping:
        snprintf(statusBuf,
                 sizeof(statusBuf),
                 "{\"state\":\"%s\",\"version\":\"%s\",\"build\":%d,\"offset\":%u,\"slot_max\":%u,"
                 "\"up_s\":%u,\"cfg\":%u,\"raw\":%u,\"mov_cm\":%u,\"mov_e\":%u,"
                 "\"stat_cm\":%u,\"stat_e\":%u,\"det_cm\":%u,\"rx_b\":%u}",
                 mActive ? "staging" : "idle",
                 APP_VERSION_STRING,
                 APP_BUILD_NUMBER,
                 static_cast<unsigned>(mReceivedBytes),
                 static_cast<unsigned>(OtaProto::kMaxFirmwareSize),
                 static_cast<unsigned>(k_uptime_get() / 1000),
                 mDiag.configured ? 1u : 0u,
                 static_cast<unsigned>(mDiag.rawState),
                 static_cast<unsigned>(mDiag.movingDistCm),
                 static_cast<unsigned>(mDiag.movingEnergy),
                 static_cast<unsigned>(mDiag.stationaryDistCm),
                 static_cast<unsigned>(mDiag.stationaryEnergy),
                 static_cast<unsigned>(mDiag.detectionDistCm),
                 static_cast<unsigned>(mDiag.rxBytes));
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        break;

    case OtaCommandAction::Bootloader:
        LOG_INF("Remote UF2 bootloader command received; setting GPREGRET=0x%02X and rebooting",
                OtaProto::kUf2BootloaderMagic);
        snprintf(statusBuf,
                 sizeof(statusBuf),
                 "{\"state\":\"entering_uf2_bootloader\",\"version\":\"%s\"}",
                 APP_VERSION_STRING);
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        k_msleep(150);
        nrf_power_gpregret_set(NRF_POWER, 0u, OtaProto::kUf2BootloaderMagic);
        sys_reboot(SYS_REBOOT_COLD);
        break;

    case OtaCommandAction::Abort:
        mActive          = false;
        mExpectedSize    = 0u;
        mExpectedCrc32   = 0u;
        mReceivedBytes   = 0u;
        mErasedEndOffset = 0u;
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"aborted\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        break;

    case OtaCommandAction::Begin:
        if (cmd.size < OtaProto::kMinFirmwareSize || cmd.size > OtaProto::kMaxFirmwareSize) {
            snprintf(statusBuf,
                     sizeof(statusBuf),
                     "{\"state\":\"error\",\"reason\":\"invalid_size\",\"size\":%u,\"max\":%u}",
                     static_cast<unsigned>(cmd.size),
                     static_cast<unsigned>(OtaProto::kMaxFirmwareSize));
            if (publishFn) {
                (void)publishFn(publishCtx, mStatusTopic, statusBuf);
            }
            return;
        }
        mExpectedSize    = cmd.size;
        mExpectedCrc32   = cmd.crc32;
        mReceivedBytes   = 0u;
        mErasedEndOffset = 0u;
        mActive          = true;

        if (EnsureStagingErasedUpTo(OtaProto::kFlashPageSize) != 0) {
            mActive = false;
            snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"erase_failed\"}");
            if (publishFn) {
                (void)publishFn(publishCtx, mStatusTopic, statusBuf);
            }
            return;
        }

        LOG_INF("FOTA session started: size=%u bytes, expected_crc32=0x%08X",
                static_cast<unsigned>(mExpectedSize),
                static_cast<unsigned>(mExpectedCrc32));
        snprintf(statusBuf,
                 sizeof(statusBuf),
                 "{\"state\":\"ready\",\"offset\":0,\"size\":%u,\"crc32\":%u}",
                 static_cast<unsigned>(mExpectedSize),
                 static_cast<unsigned>(mExpectedCrc32));
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        break;

    case OtaCommandAction::Apply: {
        if (!mActive || mReceivedBytes != mExpectedSize) {
            snprintf(statusBuf,
                     sizeof(statusBuf),
                     "{\"state\":\"error\",\"reason\":\"incomplete\",\"offset\":%u,\"expected\":%u}",
                     static_cast<unsigned>(mReceivedBytes),
                     static_cast<unsigned>(mExpectedSize));
            if (publishFn) {
                (void)publishFn(publishCtx, mStatusTopic, statusBuf);
            }
            return;
        }

        uint32_t calcCrc = 0u;
        if (!VerifyStagedImage(&calcCrc)) {
            LOG_ERR("FOTA image verification failed (calc_crc=0x%08X, expected_crc=0x%08X)",
                    static_cast<unsigned>(calcCrc),
                    static_cast<unsigned>(mExpectedCrc32));
            snprintf(statusBuf,
                     sizeof(statusBuf),
                     "{\"state\":\"error\",\"reason\":\"crc_mismatch\",\"calc\":%u,\"expected\":%u}",
                     static_cast<unsigned>(calcCrc),
                     static_cast<unsigned>(mExpectedCrc32));
            if (publishFn) {
                (void)publishFn(publishCtx, mStatusTopic, statusBuf);
            }
            return;
        }

        LOG_INF("FOTA image verified (%u bytes, crc32=0x%08X); applying from SRAM and rebooting",
                static_cast<unsigned>(mExpectedSize),
                static_cast<unsigned>(calcCrc));
        snprintf(statusBuf,
                 sizeof(statusBuf),
                 "{\"state\":\"applying\",\"size\":%u,\"crc32\":%u}",
                 static_cast<unsigned>(mExpectedSize),
                 static_cast<unsigned>(calcCrc));
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        k_msleep(200);
        ApplyStagedImageFromRamAndReset(
            OtaProto::kSlot0BaseAddress, OtaProto::kSlot1StagingAddress, mExpectedSize);
        break;
    }

    default:
        break;
    }
}

void OtaUpdater::HandleChunkMessage(const uint8_t *payload,
                                    size_t len,
                                    StatusPublishFn publishFn,
                                    void *publishCtx)
{
    char statusBuf[160] = {};
    if (!mActive) {
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"not_active\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    uint32_t offset      = 0u;
    const uint8_t *data  = nullptr;
    size_t dataLen       = 0u;
    if (!OtaProto::ParseChunkHeader(payload, len, &offset, &data, &dataLen)) {
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"bad_chunk\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    // Idempotent offset synchronization: if sender retransmits an earlier or out-of-order chunk,
    // reply with the current committed offset so sender resumes cleanly at mReceivedBytes.
    if (offset != mReceivedBytes) {
        snprintf(statusBuf,
                 sizeof(statusBuf),
                 "{\"state\":\"ack\",\"offset\":%u}",
                 static_cast<unsigned>(mReceivedBytes));
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    if (offset == 0u && !OtaProto::ValidateCortexM4VectorTable(data, dataLen)) {
        mActive = false;
        snprintf(statusBuf,
                 sizeof(statusBuf),
                 "{\"state\":\"error\",\"reason\":\"bad_vector_table\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    if ((offset + static_cast<uint32_t>(dataLen)) > mExpectedSize) {
        mActive = false;
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"overflow\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    const uint32_t writeEndOffset =
        (offset + static_cast<uint32_t>(dataLen) + 3u) & ~3u;
    if (EnsureStagingErasedUpTo(writeEndOffset) != 0) {
        mActive = false;
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"erase_failed\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    // nRF52840 NVMC requires 4-byte aligned flash writes; pad tail chunk with 0xFF if needed
    uint8_t alignedBuf[OtaProto::kMaxChunkDataSize + 4u];
    const size_t alignedLen = (dataLen + 3u) & ~static_cast<size_t>(3u);
    memset(alignedBuf, 0xFF, alignedLen);
    memcpy(alignedBuf, data, dataLen);

    const off_t writeAddr = static_cast<off_t>(OtaProto::kSlot1StagingAddress + offset);
    int ret = flash_write(mFlashDev, writeAddr, alignedBuf, alignedLen);
    if (ret != 0) {
        LOG_ERR("flash_write failed at 0x%08X (err=%d)", static_cast<unsigned>(writeAddr), ret);
        mActive = false;
        snprintf(statusBuf, sizeof(statusBuf), "{\"state\":\"error\",\"reason\":\"write_failed\"}");
        if (publishFn) {
            (void)publishFn(publishCtx, mStatusTopic, statusBuf);
        }
        return;
    }

    mReceivedBytes += static_cast<uint32_t>(dataLen);
    snprintf(statusBuf,
             sizeof(statusBuf),
             "{\"state\":\"ack\",\"offset\":%u}",
             static_cast<unsigned>(mReceivedBytes));
    if (publishFn) {
        (void)publishFn(publishCtx, mStatusTopic, statusBuf);
    }
}

void OtaUpdater::HandleMqttMessage(const char *topic,
                                   const uint8_t *payload,
                                   size_t payloadLen,
                                   StatusPublishFn publishFn,
                                   void *publishCtx)
{
    if (!topic || !payload) {
        return;
    }
    if (strcmp(topic, mCmdTopic) == 0) {
        HandleCmdMessage(reinterpret_cast<const char *>(payload), payloadLen, publishFn, publishCtx);
    } else if (strcmp(topic, mChunkTopic) == 0) {
        HandleChunkMessage(payload, payloadLen, publishFn, publishCtx);
    }
}

#endif // __ZEPHYR__
