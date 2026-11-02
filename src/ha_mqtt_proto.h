/*
 * Copyright (c) 2026 Craig McLean
 * Home Assistant MQTT Auto-Discovery & State JSON Codec + RFC 6052 NAT64 Helper (Host-Testable)
 */

#pragma once

#include "bthome_proto.h"
#include <stddef.h>
#include <stdint.h>

enum class HaEntityId : uint8_t {
    Occupancy = 0,
    Motion    = 1,
    Distance  = 2,
    Battery   = 3,
    Voltage   = 4,
    Count     = 5
};

namespace HaMqttProto {

static constexpr size_t kNodeSlugLen          = 13u;  // "presence_xxxx"
static constexpr size_t kMaxTopicLen          = 96u;
static constexpr size_t kMaxStatePayloadLen   = 160u;
static constexpr size_t kMaxDiscoveryJsonLen  = 512u;

static constexpr const char *kAvailabilityOnline  = "online";
static constexpr const char *kAvailabilityOffline = "offline";

/**
 * @brief Derive deterministic lowercase node slug "presence_xxxx" from hardware FICR device ID.
 * @return 13 on success, or 0 if outSlug is null or maxSlugLen < 14.
 */
size_t FormatNodeSlug(const uint8_t *deviceId, size_t deviceIdLen, char *outSlug, size_t maxSlugLen);

/**
 * @brief Format state topic: "presence_sensor/<nodeSlug>/state".
 * @return String length (excluding NUL) on success, or 0 on error/truncation.
 */
size_t FormatStateTopic(const char *nodeSlug, char *outTopic, size_t maxLen);

/**
 * @brief Format availability topic: "presence_sensor/<nodeSlug>/status".
 * @return String length (excluding NUL) on success, or 0 on error/truncation.
 */
size_t FormatAvailabilityTopic(const char *nodeSlug, char *outTopic, size_t maxLen);

/**
 * @brief Format Home Assistant MQTT Discovery config topic:
 *        "homeassistant/<component>/<nodeSlug>/<object_id>/config".
 * @return String length (excluding NUL) on success, or 0 on error/truncation.
 */
size_t FormatDiscoveryTopic(const char *nodeSlug, HaEntityId entity, char *outTopic, size_t maxLen);

/**
 * @brief Format JSON state payload published to "presence_sensor/<nodeSlug>/state":
 *        {"occupancy":"ON","motion":"ON","distance_mm":1340,"battery_pct":87,"voltage_mv":3985,"packet_id":42}
 * @return String length (excluding NUL) on success, or 0 on error/truncation.
 */
size_t FormatStatePayload(const BthomeMeasurement &m, char *outJson, size_t maxLen);

/**
 * @brief Format Home Assistant MQTT Auto-Discovery JSON payload for one of the 5 entities.
 * @return String length (excluding NUL) on success, or 0 on error/truncation.
 */
size_t FormatDiscoveryPayload(const char *nodeSlug,
                              const char *deviceName,
                              const char *swVersion,
                              HaEntityId entity,
                              char *outJson,
                              size_t maxLen);

/**
 * @brief Parse dotted-quad IPv4 literal (e.g., "192.168.41.250") into 4 bytes in network byte order.
 */
bool ParseIpv4Literal(const char *ipv4Str, uint8_t outIpv4[4]);

/**
 * @brief Synthesize a 128-bit IPv6 address from a 96-bit (12-byte) NAT64 prefix and 32-bit (4-byte) IPv4 address
 *        per RFC 6052 Section 2.2.
 */
bool SynthesizeNat64Ipv6(const uint8_t nat64Prefix12[12], const uint8_t ipv4Bytes[4], uint8_t outIpv6[16]);

} // namespace HaMqttProto
