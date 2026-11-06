/*
 * Copyright (c) 2026 Craig McLean
 * Home Assistant MQTT Auto-Discovery & State JSON Codec + RFC 6052 NAT64 Helper (Host-Testable)
 */

#include "ha_mqtt_proto.h"
#include <stdio.h>
#include <string.h>

namespace HaMqttProto {

namespace {

struct EntityMeta {
    const char *component;
    const char *objectId;
    const char *displayName;
    const char *deviceClass;
    const char *unitOfMeasurement; // nullptr for binary_sensor
    const char *stateClass;        // nullptr for binary_sensor
    const char *valueTemplate;
    bool        isBinarySensor;
};

static constexpr EntityMeta kEntityTable[static_cast<size_t>(HaEntityId::Count)] = {
    // HaEntityId::Occupancy
    {
        "binary_sensor",
        "occupancy",
        "Occupancy",
        "occupancy",
        nullptr,
        nullptr,
        "{{ value_json.occupancy }}",
        true,
    },
    // HaEntityId::Motion
    {
        "binary_sensor",
        "motion",
        "Motion",
        "motion",
        nullptr,
        nullptr,
        "{{ value_json.motion }}",
        true,
    },
    // HaEntityId::Distance
    {
        "sensor",
        "distance",
        "Distance",
        "distance",
        "mm",
        "measurement",
        "{{ value_json.distance_mm }}",
        false,
    },
    // HaEntityId::Battery
    {
        "sensor",
        "battery",
        "Battery",
        "battery",
        "%",
        "measurement",
        "{{ value_json.battery_pct }}",
        false,
    },
    // HaEntityId::Voltage
    {
        "sensor",
        "voltage",
        "Voltage",
        "voltage",
        "mV",
        "measurement",
        "{{ value_json.voltage_mv }}",
        false,
    },
};

} // namespace

size_t FormatNodeSlug(const uint8_t *deviceId, size_t deviceIdLen, char *outSlug, size_t maxSlugLen)
{
    if (!outSlug || maxSlugLen < (kNodeSlugLen + 1u)) {
        return 0u;
    }

    static constexpr char kPrefix[] = "presence_";
    static constexpr char kHex[]    = "0123456789abcdef";
    const uint16_t shortId = BthomeProto::DeriveShortIdFromDeviceId(deviceId, deviceIdLen);

    for (size_t i = 0; i < 9u; ++i) {
        outSlug[i] = kPrefix[i];
    }
    outSlug[9]  = kHex[(shortId >> 12) & 0x0Fu];
    outSlug[10] = kHex[(shortId >> 8) & 0x0Fu];
    outSlug[11] = kHex[(shortId >> 4) & 0x0Fu];
    outSlug[12] = kHex[shortId & 0x0Fu];
    outSlug[13] = '\0';

    return kNodeSlugLen;
}

size_t FormatStateTopic(const char *nodeSlug, char *outTopic, size_t maxLen)
{
    if (!nodeSlug || !nodeSlug[0] || !outTopic || maxLen == 0u) {
        return 0u;
    }

    const int n = snprintf(outTopic, maxLen, "presence_sensor/%s/state", nodeSlug);
    if (n <= 0 || static_cast<size_t>(n) >= maxLen) {
        return 0u;
    }
    return static_cast<size_t>(n);
}

size_t FormatAvailabilityTopic(const char *nodeSlug, char *outTopic, size_t maxLen)
{
    if (!nodeSlug || !nodeSlug[0] || !outTopic || maxLen == 0u) {
        return 0u;
    }

    const int n = snprintf(outTopic, maxLen, "presence_sensor/%s/status", nodeSlug);
    if (n <= 0 || static_cast<size_t>(n) >= maxLen) {
        return 0u;
    }
    return static_cast<size_t>(n);
}

size_t FormatDiscoveryTopic(const char *nodeSlug, HaEntityId entity, char *outTopic, size_t maxLen)
{
    const size_t idx = static_cast<size_t>(entity);
    if (!nodeSlug || !nodeSlug[0] || !outTopic || maxLen == 0u ||
        idx >= static_cast<size_t>(HaEntityId::Count)) {
        return 0u;
    }

    const EntityMeta &meta = kEntityTable[idx];
    const int n = snprintf(outTopic, maxLen, "homeassistant/%s/%s/%s/config",
                           meta.component, nodeSlug, meta.objectId);
    if (n <= 0 || static_cast<size_t>(n) >= maxLen) {
        return 0u;
    }
    return static_cast<size_t>(n);
}

size_t FormatStatePayload(const BthomeMeasurement &m, char *outJson, size_t maxLen)
{
    if (!outJson || maxLen == 0u) {
        return 0u;
    }

    const uint8_t clampedPct = (m.batteryPct > 100u) ? 100u : m.batteryPct;
    const int n = snprintf(
        outJson,
        maxLen,
        "{\"occupancy\":\"%s\",\"motion\":\"%s\",\"distance_mm\":%u,\"battery_pct\":%u,\"voltage_mv\":%u,\"packet_id\":%u}",
        m.occupancy ? "ON" : "OFF",
        m.motion ? "ON" : "OFF",
        static_cast<unsigned>(m.distanceMm),
        static_cast<unsigned>(clampedPct),
        static_cast<unsigned>(m.voltageMv),
        static_cast<unsigned>(m.packetId));
    if (n <= 0 || static_cast<size_t>(n) >= maxLen) {
        return 0u;
    }
    return static_cast<size_t>(n);
}

size_t FormatDiscoveryPayload(const char *nodeSlug,
                              const char *deviceName,
                              const char *swVersion,
                              HaEntityId entity,
                              char *outJson,
                              size_t maxLen)
{
    const size_t idx = static_cast<size_t>(entity);
    if (!nodeSlug || !nodeSlug[0] || !deviceName || !deviceName[0] ||
        !swVersion || !swVersion[0] || !outJson || maxLen == 0u ||
        idx >= static_cast<size_t>(HaEntityId::Count)) {
        return 0u;
    }

    const EntityMeta &meta = kEntityTable[idx];
    int n = 0;

    if (meta.isBinarySensor) {
        n = snprintf(
            outJson,
            maxLen,
            "{\"name\":\"%s\","
            "\"uniq_id\":\"%s_%s\","
            "\"stat_t\":\"presence_sensor/%s/state\","
            "\"avty_t\":\"presence_sensor/%s/status\","
            "\"device_class\":\"%s\","
            "\"val_tpl\":\"%s\","
            "\"pl_on\":\"ON\","
            "\"pl_off\":\"OFF\","
            "\"dev\":{\"ids\":[\"%s\"],\"name\":\"%s\",\"mdl\":\"%s\",\"mf\":\"OpenThread nRF52840\",\"sw\":\"%s\"}}",
            meta.displayName,
            nodeSlug, meta.objectId,
            nodeSlug,
            nodeSlug,
            meta.deviceClass,
            meta.valueTemplate,
            nodeSlug,
            deviceName,
            kActiveRadarModelName,
            swVersion);
    } else {
        n = snprintf(
            outJson,
            maxLen,
            "{\"name\":\"%s\","
            "\"uniq_id\":\"%s_%s\","
            "\"stat_t\":\"presence_sensor/%s/state\","
            "\"avty_t\":\"presence_sensor/%s/status\","
            "\"device_class\":\"%s\","
            "\"unit_of_meas\":\"%s\","
            "\"stat_cla\":\"%s\","
            "\"val_tpl\":\"%s\","
            "\"dev\":{\"ids\":[\"%s\"],\"name\":\"%s\",\"mdl\":\"%s\",\"mf\":\"OpenThread nRF52840\",\"sw\":\"%s\"}}",
            meta.displayName,
            nodeSlug, meta.objectId,
            nodeSlug,
            nodeSlug,
            meta.deviceClass,
            meta.unitOfMeasurement,
            meta.stateClass,
            meta.valueTemplate,
            nodeSlug,
            deviceName,
            kActiveRadarModelName,
            swVersion);
    }

    if (n <= 0 || static_cast<size_t>(n) >= maxLen) {
        return 0u;
    }
    return static_cast<size_t>(n);
}

bool ParseIpv4Literal(const char *ipv4Str, uint8_t outIpv4[4])
{
    if (!ipv4Str || !outIpv4) {
        return false;
    }

    uint32_t accum = 0u;
    size_t octetIdx = 0u;
    size_t digitsInOctet = 0u;

    for (const char *p = ipv4Str;; ++p) {
        const char c = *p;
        if (c >= '0' && c <= '9') {
            accum = (accum * 10u) + static_cast<uint32_t>(c - '0');
            if (accum > 255u || ++digitsInOctet > 3u) {
                return false;
            }
        } else if (c == '.' || c == '\0') {
            if (digitsInOctet == 0u || octetIdx >= 4u) {
                return false;
            }
            outIpv4[octetIdx++] = static_cast<uint8_t>(accum);
            accum = 0u;
            digitsInOctet = 0u;
            if (c == '\0') {
                return octetIdx == 4u;
            }
        } else {
            return false;
        }
    }
}

bool SynthesizeNat64Ipv6(const uint8_t nat64Prefix12[12], const uint8_t ipv4Bytes[4], uint8_t outIpv6[16])
{
    if (!nat64Prefix12 || !ipv4Bytes || !outIpv6) {
        return false;
    }
    memcpy(&outIpv6[0], nat64Prefix12, 12u);
    memcpy(&outIpv6[12], ipv4Bytes, 4u);
    return true;
}

} // namespace HaMqttProto
