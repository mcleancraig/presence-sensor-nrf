/*
 * Copyright (c) 2026 Craig McLean
 * OpenThread Sleepy End Device (SED) + NAT64 + Home Assistant MQTT Publisher
 */

#pragma once

#include "bthome_proto.h"
#include "ha_mqtt_proto.h"
#include "ota_updater.h"
#include <zephyr/kernel.h>
#include <zephyr/net/mqtt.h>
#include <zephyr/net/socket.h>

class ThreadMqttPublisher {
public:
    static constexpr uint32_t kFastPollPeriodMs     = 80u;   // 80 ms child data poll during TCP/MQTT active exchange
    static constexpr uint32_t kIdlePollPeriodMs     = 5000u; // 5000 ms sleepy end device idle poll period
    static constexpr int64_t  kFastPollHoldMs       = 1500;  // Keep 80 ms poll for 1.5 s after publish for TCP ACK
    static constexpr uint8_t  kDiscoveryTotalSteps  = 6u;    // Step 0: online status, Steps 1..5: 5 HA entities
    static constexpr int64_t  kDiscoveryPaceMs      = 250;   // Pace discovery packets >= 250 ms apart for 6LoWPAN TCP ACKs

    ThreadMqttPublisher();

    /**
     * @brief Initialize OpenThread Sleepy End Device (SED), load Active Operational Dataset,
     *        enable +8 dBm IEEE 802.15.4 TX power, and start Thread attachment.
     */
    int Init();

    /**
     * @brief Queue and publish a sensor measurement over MQTT (via NAT64).
     *        If Thread is still attaching at boot, the measurement is cached and
     *        flushed automatically by ProcessBackground() as soon as Thread attaches.
     */
    int Publish(const BthomeMeasurement &m, bool burst);

    /**
     * @brief Periodic background maintenance called from AppTask event loop:
     *        flushes pending boot/reconnect publishes once Thread attaches, services
     *        MQTT keepalive/input, and restores 5000 ms SED idle poll after fast-poll bursts.
     */
    void ProcessBackground();

    const char *GetDeviceName() const { return mDeviceName; }
    const char *GetNodeSlug() const { return mNodeSlug; }
    uint8_t GetLastPacketId() const { return mPacketId; }
    bool IsConnected() const { return mConnected; }

private:
    static void OnMqttEventStatic(struct mqtt_client *client, const struct mqtt_evt *evt);
    static int PublishOtaStatusStatic(void *ctx, const char *topic, const char *jsonPayload);
    void OnMqttEvent(const struct mqtt_evt *evt);

    bool ResolveBrokerNat64Address(struct in6_addr *outAddr6);
    void SetFastPoll(bool fast);
    void PumpSocket(int32_t timeoutMs);
    int ConnectToBroker();
    void DisconnectBroker();
    int SubscribeOtaTopics();
    int PublishRaw(const char *topic, const void *payload, size_t payloadLen, bool retain);
    int PublishNextDiscoveryStep();
    int TryFlushPending();

    struct mqtt_client   mClient;
    struct sockaddr_in6  mBrokerAddr;
    struct mqtt_utf8     mUserUtf8;
    struct mqtt_utf8     mPassUtf8;
    struct mqtt_topic    mWillTopic;
    struct mqtt_utf8     mWillMsg;
    uint8_t              mRxBuf[768];
    uint8_t              mTxBuf[1024];

    char                 mDeviceName[BthomeProto::kDeviceNameLen + 1];
    char                 mNodeSlug[HaMqttProto::kNodeSlugLen + 1];
    char                 mStateTopic[HaMqttProto::kMaxTopicLen];
    char                 mAvailabilityTopic[HaMqttProto::kMaxTopicLen];

    OtaUpdater           mOtaUpdater;
    BthomeMeasurement    mPendingMeasurement;
    int64_t              mFastPollDeadlineMs;
    int64_t              mLastConnectAttemptMs;
    int64_t              mLastDiscoveryStepMs;
    int64_t              mLastPingSentMs;
    uint16_t             mNextMsgId;
    uint8_t              mPacketId;
    uint8_t              mDiscoveryStep;
    bool                 mConnected;
    bool                 mConnackReceived;
    bool                 mHasPendingPublish;
    bool                 mFastPollActive;
};
