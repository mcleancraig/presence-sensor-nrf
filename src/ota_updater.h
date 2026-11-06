/*
 * Copyright (c) 2026 Craig McLean
 * Wireless MQTT FOTA (Firmware Over-The-Air) Updater & UF2 Bootloader Trigger
 */

#pragma once

#include <stddef.h>
#include <stdint.h>

enum class OtaCommandAction : uint8_t {
    None       = 0,
    Ping       = 1,
    Bootloader = 2,
    Begin      = 3,
    Apply      = 4,
    Abort      = 5,
};

struct OtaCommand {
    OtaCommandAction action;
    uint32_t         size;
    uint32_t         crc32;
};

namespace OtaProto {

static constexpr uint32_t kFlashPageSize        = 4096u;
static constexpr uint32_t kSlot0BaseAddress     = 0x00001000u;
static constexpr uint32_t kSlot1StagingAddress  = 0x00076000u;
static constexpr uint32_t kMaxFirmwareSize      = 0x00075000u; // 468 KB per slot
static constexpr uint32_t kMinFirmwareSize      = 4096u;
static constexpr uint32_t kNrf52840SramBase     = 0x20000000u;
static constexpr uint32_t kNrf52840SramEnd      = 0x20040000u;
static constexpr uint8_t  kUf2BootloaderMagic   = 0x57u;       // Adafruit nRF52 UF2 GPREGRET magic
static constexpr size_t   kChunkHeaderSize      = 4u;          // 4-byte little-endian offset prefix
static constexpr size_t   kMaxChunkDataSize     = 256u;
static constexpr size_t   kMaxOtaTopicLen       = 96u;

/**
 * @brief Compute standard IEEE 802.3 CRC-32 over a byte buffer.
 */
uint32_t Crc32(const uint8_t *data, size_t len, uint32_t initialCrc = 0u);

/**
 * @brief Validate that the first >= 8 bytes of a firmware image contain a valid
 *        nRF52840 Cortex-M4 vector table (MSP in SRAM 0x20000000..0x20040000 and
 *        Thumb Reset_Handler address inside Slot 0 0x00001000..0x00076000).
 */
bool ValidateCortexM4VectorTable(const uint8_t *firstBytes, size_t len);

/**
 * @brief Format OTA MQTT topics for a given node slug (e.g. "presence_70ed").
 */
size_t FormatCmdTopic(const char *nodeSlug, char *outBuf, size_t maxLen);
size_t FormatChunkTopic(const char *nodeSlug, char *outBuf, size_t maxLen);
size_t FormatStatusTopic(const char *nodeSlug, char *outBuf, size_t maxLen);

/**
 * @brief Parse a JSON command payload sent to `presence_sensor/<slug>/ota/cmd`.
 *        Supported actions: "ping", "bootloader", "begin" (with "size" and "crc32"),
 *        "apply", and "abort".
 */
bool ParseCommandJson(const char *json, size_t len, OtaCommand *outCmd);

/**
 * @brief Parse a binary chunk header `[offset_u32_le : 4B][payload : 1..256B]`.
 */
bool ParseChunkHeader(const uint8_t *buf,
                      size_t len,
                      uint32_t *outOffset,
                      const uint8_t **outData,
                      size_t *outDataLen);

} // namespace OtaProto

#ifdef __ZEPHYR__
#include <zephyr/device.h>

class OtaUpdater {
public:
    using StatusPublishFn = int (*)(void *ctx, const char *topic, const char *jsonPayload);

    OtaUpdater();

    int Init(const char *nodeSlug);

    const char *GetCmdTopic() const { return mCmdTopic; }
    const char *GetChunkTopic() const { return mChunkTopic; }
    const char *GetStatusTopic() const { return mStatusTopic; }
    bool IsActive() const { return mActive; }

    void HandleMqttMessage(const char *topic,
                           const uint8_t *payload,
                           size_t payloadLen,
                           StatusPublishFn publishFn,
                           void *publishCtx);

private:
    void HandleCmdMessage(const char *json,
                          size_t len,
                          StatusPublishFn publishFn,
                          void *publishCtx);
    void HandleChunkMessage(const uint8_t *payload,
                            size_t len,
                            StatusPublishFn publishFn,
                            void *publishCtx);
    int EnsureStagingErasedUpTo(uint32_t endOffset);
    bool VerifyStagedImage(uint32_t *outCalculatedCrc32) const;

    const struct device *mFlashDev;
    char                 mCmdTopic[OtaProto::kMaxOtaTopicLen];
    char                 mChunkTopic[OtaProto::kMaxOtaTopicLen];
    char                 mStatusTopic[OtaProto::kMaxOtaTopicLen];
    uint32_t             mExpectedSize;
    uint32_t             mExpectedCrc32;
    uint32_t             mReceivedBytes;
    uint32_t             mErasedEndOffset;
    bool                 mActive;
};
#endif // __ZEPHYR__
