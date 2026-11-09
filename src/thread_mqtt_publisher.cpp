/*
 * Copyright (c) 2026 Craig McLean
 * OpenThread Sleepy End Device (SED) + NAT64 + Home Assistant MQTT Publisher
 */

#include "thread_mqtt_publisher.h"
#include "version.h"

#include <string.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/openthread.h>
#include <zephyr/sys/util.h>

#include <openthread/dataset.h>
#include <openthread/ip6.h>
#include <openthread/link.h>
#include <openthread/nat64.h>
#include <openthread/netdata.h>
#include <openthread/platform/radio.h>
#include <openthread/thread.h>

LOG_MODULE_REGISTER(thread_mqtt, LOG_LEVEL_INF);

namespace {

static constexpr int32_t kMqttConnectTimeoutMs     = 4000;
static constexpr int64_t kReconnectBackoffMs       = 2000;
static constexpr int64_t kOnlineReassertIntervalMs = 60000;
static constexpr int32_t kSocketIoTimeoutSec       = 3;

} // namespace

ThreadMqttPublisher::ThreadMqttPublisher()
    : mClient{},
      mBrokerAddr{},
      mUserUtf8{},
      mPassUtf8{},
      mWillTopic{},
      mWillMsg{},
      mRxBuf{},
      mTxBuf{},
      mOtaUpdater{},
      mPendingMeasurement{},
      mFastPollDeadlineMs(0),
      mLastConnectAttemptMs(-kReconnectBackoffMs),
      mLastDiscoveryStepMs(0),
      mLastPingSentMs(0),
      mLastOnlinePublishMs(0),
      mNextMsgId(1u),
      mPacketId(0u),
      mDiscoveryStep(0u),
      mConnected(false),
      mConnackReceived(false),
      mHasPendingPublish(false),
      mHasValidMeasurement(false),
      mFastPollActive(false)
{
    memcpy(mDeviceName, "Presence-0000", sizeof("Presence-0000"));
    memcpy(mNodeSlug, "presence_0000", sizeof("presence_0000"));
    memset(mStateTopic, 0, sizeof(mStateTopic));
    memset(mAvailabilityTopic, 0, sizeof(mAvailabilityTopic));
}

void ThreadMqttPublisher::OnMqttEventStatic(struct mqtt_client *client, const struct mqtt_evt *evt)
{
    auto *self = static_cast<ThreadMqttPublisher *>(client->user_data);
    if (self) {
        self->OnMqttEvent(evt);
    }
}

int ThreadMqttPublisher::PublishOtaStatusStatic(void *ctx, const char *topic, const char *jsonPayload)
{
    auto *self = static_cast<ThreadMqttPublisher *>(ctx);
    if (!self || !topic || !jsonPayload) {
        return -EINVAL;
    }
    return self->PublishRaw(topic, jsonPayload, strlen(jsonPayload), false);
}

void ThreadMqttPublisher::OnMqttEvent(const struct mqtt_evt *evt)
{
    if (!evt) {
        return;
    }

    switch (evt->type) {
    case MQTT_EVT_CONNACK:
        if (evt->result == 0 && evt->param.connack.return_code == MQTT_CONNECTION_ACCEPTED) {
            mConnected       = true;
            mConnackReceived = true;
            LOG_INF("MQTT CONNACK accepted by broker");
        } else {
            mConnected       = false;
            mConnackReceived = true;
            LOG_WRN("MQTT CONNACK rejected (result=%d, code=%d)",
                    evt->result,
                    static_cast<int>(evt->param.connack.return_code));
        }
        break;

    case MQTT_EVT_DISCONNECT:
        LOG_INF("MQTT disconnected (reason=%d)", evt->result);
        mConnected     = false;
        mDiscoveryStep = 0u;
        if (mHasValidMeasurement) {
            mHasPendingPublish = true;
        }
        break;

    case MQTT_EVT_PUBLISH: {
        const auto &pub = evt->param.publish;
        char topicBuf[OtaProto::kMaxOtaTopicLen] = {};
        const size_t tLen = (pub.message.topic.topic.size < (sizeof(topicBuf) - 1u))
                                ? pub.message.topic.topic.size
                                : (sizeof(topicBuf) - 1u);
        memcpy(topicBuf, pub.message.topic.topic.utf8, tLen);
        topicBuf[tLen] = '\0';

        uint8_t payloadBuf[OtaProto::kMaxChunkDataSize + 32u] = {};
        const uint32_t pLen = pub.message.payload.len;
        if (pLen > 0u && pLen <= sizeof(payloadBuf)) {
            const int readRet = mqtt_readall_publish_payload(&mClient, payloadBuf, pLen);
            if (readRet == 0) {
                mOtaUpdater.HandleMqttMessage(
                    topicBuf, payloadBuf, pLen, PublishOtaStatusStatic, this);
            }
        } else if (pLen > sizeof(payloadBuf)) {
            // Drain oversized payload so MQTT stream stays synchronized
            uint8_t discard[64];
            uint32_t remaining = pLen;
            while (remaining > 0u) {
                const uint32_t chunk = (remaining > sizeof(discard)) ? sizeof(discard) : remaining;
                if (mqtt_read_publish_payload(&mClient, discard, chunk) <= 0) {
                    break;
                }
                remaining -= chunk;
            }
        }
        break;
    }

    case MQTT_EVT_PUBACK:
    case MQTT_EVT_PINGRESP:
    case MQTT_EVT_SUBACK:
    default:
        break;
    }
}

int ThreadMqttPublisher::Init()
{
    // 1. Read factory-programmed 64-bit FICR device ID for unique node slug & display name
    uint8_t devId[16] = {};
    ssize_t devIdLen = hwinfo_get_device_id(devId, sizeof(devId));
    if (devIdLen <= 0) {
        LOG_WRN("hwinfo_get_device_id failed (%d); using fallback ID", static_cast<int>(devIdLen));
        devIdLen = 8;
    }

    BthomeProto::FormatDeviceName(devId, static_cast<size_t>(devIdLen), mDeviceName, sizeof(mDeviceName));
    HaMqttProto::FormatNodeSlug(devId, static_cast<size_t>(devIdLen), mNodeSlug, sizeof(mNodeSlug));
    HaMqttProto::FormatStateTopic(mNodeSlug, mStateTopic, sizeof(mStateTopic));
    HaMqttProto::FormatAvailabilityTopic(mNodeSlug, mAvailabilityTopic, sizeof(mAvailabilityTopic));
    (void)mOtaUpdater.Init(mNodeSlug);

    // 2. Configure OpenThread link mode (Always-On MED when USB-powered, Sleepy SED when battery-powered)
    struct openthread_context *otCtx = openthread_get_default_context();
    otInstance *instance = openthread_get_default_instance();
    if (!otCtx || !instance) {
        LOG_ERR("OpenThread context/instance unavailable");
        return -ENODEV;
    }

    openthread_api_mutex_lock(otCtx);

    const bool alwaysUsbPowered = IS_ENABLED(CONFIG_APP_ALWAYS_USB_POWERED);
    otLinkModeConfig linkMode{};
    linkMode.mRxOnWhenIdle = alwaysUsbPowered;
    linkMode.mDeviceType   = false;
    linkMode.mNetworkData  = true;
    (void)otThreadSetLinkMode(instance, linkMode);

    // Enforce +8 dBm IEEE 802.15.4 transmit power; only set sleepy parent poll period when SED
    (void)otPlatRadioSetTransmitPower(instance, 8);
    if (!alwaysUsbPowered) {
        (void)otLinkSetPollPeriod(instance, kIdlePollPeriodMs);
    }

    // Load Active Operational Dataset TLV if provided via CONFIG_APP_THREAD_DATASET_TLV_HEX
    const char *tlvHex = CONFIG_APP_THREAD_DATASET_TLV_HEX;
    const size_t tlvHexLen = strlen(tlvHex);
    if (tlvHexLen > 0u) {
        otOperationalDatasetTlvs datasetTlvs{};
        const size_t binLen = hex2bin(tlvHex, tlvHexLen, datasetTlvs.mTlvs, sizeof(datasetTlvs.mTlvs));
        if (binLen > 0u && binLen <= sizeof(datasetTlvs.mTlvs)) {
            datasetTlvs.mLength = static_cast<uint8_t>(binLen);
            otError dsErr = otDatasetSetActiveTlvs(instance, &datasetTlvs);
            if (dsErr != OT_ERROR_NONE) {
                LOG_ERR("otDatasetSetActiveTlvs failed (otError=%d)", static_cast<int>(dsErr));
            } else {
                LOG_INF("OpenThread Active Dataset loaded (%u bytes)", static_cast<unsigned>(binLen));
            }
        } else {
            LOG_ERR("Invalid CONFIG_APP_THREAD_DATASET_TLV_HEX length (%u chars)",
                    static_cast<unsigned>(tlvHexLen));
        }
    } else {
        LOG_WRN("CONFIG_APP_THREAD_DATASET_TLV_HEX is empty; using NVS stored dataset if present");
    }

    (void)otIp6SetEnabled(instance, true);
    otError startErr = otThreadSetEnabled(instance, true);

    openthread_api_mutex_unlock(otCtx);

    if (startErr != OT_ERROR_NONE) {
        LOG_ERR("otThreadSetEnabled failed (otError=%d)", static_cast<int>(startErr));
        return -EIO;
    }

    LOG_INF("OpenThread %s initialized: name=%s, slug=%s, state_topic=%s, tx_pwr=+8dBm",
            alwaysUsbPowered ? "MED (Always-On RX)" : "SED (Sleepy)",
            mDeviceName,
            mNodeSlug,
            mStateTopic);
    return 0;
}

void ThreadMqttPublisher::SetFastPoll(bool fast)
{
    if (IS_ENABLED(CONFIG_APP_ALWAYS_USB_POWERED)) {
        return;
    }

    struct openthread_context *otCtx = openthread_get_default_context();
    otInstance *instance = openthread_get_default_instance();
    if (!otCtx || !instance) {
        return;
    }

    if (fast) {
        mFastPollDeadlineMs = k_uptime_get() + kFastPollHoldMs;
    }

    if (mFastPollActive == fast) {
        return;
    }

    openthread_api_mutex_lock(otCtx);
    (void)otLinkSetPollPeriod(instance, fast ? kFastPollPeriodMs : kIdlePollPeriodMs);
    openthread_api_mutex_unlock(otCtx);

    mFastPollActive = fast;
}

bool ThreadMqttPublisher::ResolveBrokerNat64Address(struct in6_addr *outAddr6)
{
    if (!outAddr6) {
        return false;
    }

    struct openthread_context *otCtx = openthread_get_default_context();
    otInstance *instance = openthread_get_default_instance();
    if (!otCtx || !instance) {
        return false;
    }

    uint8_t ipv4Bytes[4] = {};
    if (!HaMqttProto::ParseIpv4Literal(CONFIG_APP_MQTT_BROKER_IPV4, ipv4Bytes)) {
        LOG_ERR("Invalid CONFIG_APP_MQTT_BROKER_IPV4: %s", CONFIG_APP_MQTT_BROKER_IPV4);
        return false;
    }

    bool resolved = false;
    openthread_api_mutex_lock(otCtx);

    const otDeviceRole role = otThreadGetDeviceRole(instance);
    if (role == OT_DEVICE_ROLE_CHILD ||
        role == OT_DEVICE_ROLE_ROUTER ||
        role == OT_DEVICE_ROLE_LEADER) {
        otIp4Address otIp4{};
        memcpy(otIp4.mFields.m8, ipv4Bytes, sizeof(ipv4Bytes));

        otIp6Address otIp6{};
        if (otNat64SynthesizeIp6Address(instance, &otIp4, &otIp6) == OT_ERROR_NONE) {
            memcpy(outAddr6->s6_addr, otIp6.mFields.m8, 16u);
            resolved = true;
        } else {
            // Fallback: inspect Thread Network Data external routes for a /96 NAT64 prefix
            otNetworkDataIterator iter = OT_NETWORK_DATA_ITERATOR_INIT;
            otExternalRouteConfig route{};
            while (otNetDataGetNextRoute(instance, &iter, &route) == OT_ERROR_NONE) {
                if (route.mNat64 && route.mPrefix.mLength == 96u) {
                    HaMqttProto::SynthesizeNat64Ipv6(
                        route.mPrefix.mPrefix.mFields.m8, ipv4Bytes, outAddr6->s6_addr);
                    resolved = true;
                    break;
                }
            }
        }
    }

    openthread_api_mutex_unlock(otCtx);
    return resolved;
}

void ThreadMqttPublisher::ConfigureSocketTimeouts()
{
    if (mClient.transport.type != MQTT_TRANSPORT_NON_SECURE ||
        mClient.transport.tcp.sock < 0) {
        return;
    }

    struct zsock_timeval tv{};
    tv.tv_sec  = kSocketIoTimeoutSec;
    tv.tv_usec = 0;
    (void)zsock_setsockopt(mClient.transport.tcp.sock,
                           SOL_SOCKET,
                           SO_SNDTIMEO,
                           &tv,
                           sizeof(tv));
    (void)zsock_setsockopt(mClient.transport.tcp.sock,
                           SOL_SOCKET,
                           SO_RCVTIMEO,
                           &tv,
                           sizeof(tv));
}

void ThreadMqttPublisher::DisconnectBroker()
{
    if (mConnected) {
        (void)mqtt_disconnect(&mClient);
    } else if (mClient.transport.type == MQTT_TRANSPORT_NON_SECURE &&
               mClient.transport.tcp.sock >= 0) {
        (void)zsock_close(mClient.transport.tcp.sock);
        mClient.transport.tcp.sock = -1;
    }
    mConnected       = false;
    mConnackReceived = false;
    mDiscoveryStep   = 0u;
    if (mHasValidMeasurement) {
        mHasPendingPublish = true;
    }
}

void ThreadMqttPublisher::PumpSocket(int32_t timeoutMs)
{
    if (!mConnected || mClient.transport.tcp.sock < 0) {
        return;
    }

    struct zsock_pollfd pfd{};
    pfd.fd     = mClient.transport.tcp.sock;
    pfd.events = ZSOCK_POLLIN;

    const int pollRet = zsock_poll(&pfd, 1, timeoutMs);
    if (pollRet > 0 && (pfd.revents & (ZSOCK_POLLIN | ZSOCK_POLLHUP | ZSOCK_POLLERR))) {
        if (mqtt_input(&mClient) != 0) {
            DisconnectBroker();
        }
    }
}

int ThreadMqttPublisher::ConnectToBroker()
{
    struct in6_addr brokerAddr6{};
    if (!ResolveBrokerNat64Address(&brokerAddr6)) {
        return -EAGAIN;
    }

    const int64_t nowMs = k_uptime_get();
    if ((nowMs - mLastConnectAttemptMs) < kReconnectBackoffMs) {
        return -EAGAIN;
    }
    mLastConnectAttemptMs = nowMs;

    SetFastPoll(true);

    memset(&mBrokerAddr, 0, sizeof(mBrokerAddr));
    mBrokerAddr.sin6_family = AF_INET6;
    mBrokerAddr.sin6_port   = htons(static_cast<uint16_t>(CONFIG_APP_MQTT_BROKER_PORT));
    mBrokerAddr.sin6_addr   = brokerAddr6;

    mqtt_client_init(&mClient);
    mClient.broker           = &mBrokerAddr;
    mClient.evt_cb           = OnMqttEventStatic;
    mClient.user_data        = this;
    mClient.client_id.utf8   = reinterpret_cast<const uint8_t *>(mNodeSlug);
    mClient.client_id.size   = static_cast<uint32_t>(strlen(mNodeSlug));
    mClient.protocol_version = MQTT_VERSION_3_1_1;
    mClient.transport.type   = MQTT_TRANSPORT_NON_SECURE;
    mClient.rx_buf           = mRxBuf;
    mClient.rx_buf_size      = sizeof(mRxBuf);
    mClient.tx_buf           = mTxBuf;
    mClient.tx_buf_size      = sizeof(mTxBuf);
    mClient.keepalive        = static_cast<uint16_t>(CONFIG_APP_MQTT_KEEPALIVE_SEC);
    mClient.clean_session    = 1u;

    if (CONFIG_APP_MQTT_USERNAME[0] != '\0') {
        mUserUtf8.utf8    = reinterpret_cast<const uint8_t *>(CONFIG_APP_MQTT_USERNAME);
        mUserUtf8.size    = static_cast<uint32_t>(strlen(CONFIG_APP_MQTT_USERNAME));
        mPassUtf8.utf8    = reinterpret_cast<const uint8_t *>(CONFIG_APP_MQTT_PASSWORD);
        mPassUtf8.size    = static_cast<uint32_t>(strlen(CONFIG_APP_MQTT_PASSWORD));
        mClient.user_name = &mUserUtf8;
        mClient.password  = &mPassUtf8;
    } else {
        mClient.user_name = nullptr;
        mClient.password  = nullptr;
    }

    mWillTopic.topic.utf8 = reinterpret_cast<const uint8_t *>(mAvailabilityTopic);
    mWillTopic.topic.size = static_cast<uint32_t>(strlen(mAvailabilityTopic));
    mWillTopic.qos        = MQTT_QOS_0_AT_MOST_ONCE;
    mWillMsg.utf8         = reinterpret_cast<const uint8_t *>(HaMqttProto::kAvailabilityOffline);
    mWillMsg.size         = static_cast<uint32_t>(strlen(HaMqttProto::kAvailabilityOffline));
    mClient.will_topic    = &mWillTopic;
    mClient.will_message  = &mWillMsg;
    mClient.will_retain   = 1u;

    mConnected           = false;
    mConnackReceived     = false;
    mDiscoveryStep       = 0u;
    mLastDiscoveryStepMs = 0;

    int ret = mqtt_connect(&mClient);
    if (ret != 0) {
        LOG_WRN("mqtt_connect failed (err=%d)", ret);
        return ret;
    }
    ConfigureSocketTimeouts();
    mLastPingSentMs = k_uptime_get();

    const int64_t deadlineMs = k_uptime_get() + kMqttConnectTimeoutMs;
    while (!mConnackReceived && k_uptime_get() < deadlineMs) {
        struct zsock_pollfd pfd{};
        pfd.fd     = mClient.transport.tcp.sock;
        pfd.events = ZSOCK_POLLIN;

        const int32_t remainingMs = static_cast<int32_t>(deadlineMs - k_uptime_get());
        const int pollRet = zsock_poll(&pfd, 1, remainingMs > 0 ? remainingMs : 1);
        if (pollRet > 0 && (pfd.revents & ZSOCK_POLLIN)) {
            int inRet = mqtt_input(&mClient);
            if (inRet != 0) {
                LOG_WRN("mqtt_input during CONNACK failed (err=%d)", inRet);
                break;
            }
        } else if (pollRet < 0) {
            break;
        }
    }

    if (!mConnected) {
        LOG_WRN("Timed out or failed waiting for MQTT CONNACK");
        DisconnectBroker();
        return -ETIMEDOUT;
    }

    return PublishNextDiscoveryStep();
}

int ThreadMqttPublisher::PublishRaw(const char *topic, const void *payload, size_t payloadLen, bool retain)
{
    if (!mConnected || !topic || !payload) {
        return -ENOTCONN;
    }

    struct mqtt_publish_param param{};
    param.message.topic.topic.utf8        = reinterpret_cast<const uint8_t *>(topic);
    param.message.topic.topic.size        = static_cast<uint32_t>(strlen(topic));
    param.message.topic.qos               = MQTT_QOS_0_AT_MOST_ONCE;
    param.message.payload.data            = const_cast<uint8_t *>(static_cast<const uint8_t *>(payload));
    param.message.payload.len             = static_cast<uint32_t>(payloadLen);
    param.message_id                      = mNextMsgId++;
    if (mNextMsgId == 0u) {
        mNextMsgId = 1u;
    }
    param.dup_flag                        = 0u;
    param.retain_flag                     = retain ? 1u : 0u;

    int ret = mqtt_publish(&mClient, &param);
    if (ret != 0) {
        LOG_WRN("mqtt_publish to %s failed (err=%d)", topic, ret);
        DisconnectBroker();
    }
    return ret;
}

int ThreadMqttPublisher::PublishNextDiscoveryStep()
{
    if (!mConnected) {
        return -ENOTCONN;
    }
    if (mDiscoveryStep >= kDiscoveryTotalSteps) {
        return 0;
    }

    const int64_t nowMs = k_uptime_get();
    if (mDiscoveryStep > 0u && (nowMs - mLastDiscoveryStepMs) < kDiscoveryPaceMs) {
        return 0;
    }

    SetFastPoll(true);
    PumpSocket(0);
    if (!mConnected) {
        return -ENOTCONN;
    }

    int ret = 0;
    if (mDiscoveryStep == 0u) {
        ret = PublishRaw(mAvailabilityTopic,
                         HaMqttProto::kAvailabilityOnline,
                         strlen(HaMqttProto::kAvailabilityOnline),
                         true);
        if (ret == 0) {
            mLastOnlinePublishMs = k_uptime_get();
        }
    } else {
        static constexpr HaEntityId kEntities[5] = {
            HaEntityId::Occupancy,
            HaEntityId::Motion,
            HaEntityId::Distance,
            HaEntityId::Battery,
            HaEntityId::Voltage,
        };
        const HaEntityId entity = kEntities[mDiscoveryStep - 1u];

        char discTopic[HaMqttProto::kMaxTopicLen] = {};
        char discJson[HaMqttProto::kMaxDiscoveryJsonLen] = {};

        const size_t tLen = HaMqttProto::FormatDiscoveryTopic(
            mNodeSlug, entity, discTopic, sizeof(discTopic));
        const size_t pLen = HaMqttProto::FormatDiscoveryPayload(
            mNodeSlug, mDeviceName, APP_VERSION_STRING, entity, discJson, sizeof(discJson));
        if (tLen == 0u || pLen == 0u) {
            return -EINVAL;
        }
        ret = PublishRaw(discTopic, discJson, pLen, true);
    }

    if (ret != 0) {
        return ret;
    }

    mLastDiscoveryStepMs = k_uptime_get();
    ++mDiscoveryStep;
    PumpSocket(60);

    if (mDiscoveryStep == kDiscoveryTotalSteps) {
        LOG_INF("Published Home Assistant MQTT Discovery (5 entities) for %s", mDeviceName);
        (void)SubscribeOtaTopics();
    }
    return 0;
}

int ThreadMqttPublisher::SubscribeOtaTopics()
{
    if (!mConnected) {
        return -ENOTCONN;
    }

    struct mqtt_topic topics[2] = {};
    topics[0].topic.utf8 = reinterpret_cast<const uint8_t *>(mOtaUpdater.GetCmdTopic());
    topics[0].topic.size = static_cast<uint32_t>(strlen(mOtaUpdater.GetCmdTopic()));
    topics[0].qos        = MQTT_QOS_0_AT_MOST_ONCE;

    topics[1].topic.utf8 = reinterpret_cast<const uint8_t *>(mOtaUpdater.GetChunkTopic());
    topics[1].topic.size = static_cast<uint32_t>(strlen(mOtaUpdater.GetChunkTopic()));
    topics[1].qos        = MQTT_QOS_0_AT_MOST_ONCE;

    struct mqtt_subscription_list subList{};
    subList.list       = topics;
    subList.list_count = 2u;
    subList.message_id = mNextMsgId++;
    if (mNextMsgId == 0u) {
        mNextMsgId = 1u;
    }

    int ret = mqtt_subscribe(&mClient, &subList);
    if (ret != 0) {
        LOG_WRN("mqtt_subscribe for OTA topics failed (err=%d)", ret);
        return ret;
    }
    PumpSocket(40);
    LOG_INF("Subscribed to wireless FOTA topics: %s, %s",
            mOtaUpdater.GetCmdTopic(),
            mOtaUpdater.GetChunkTopic());
    return 0;
}

int ThreadMqttPublisher::TryFlushPending()
{
    if (!mHasPendingPublish) {
        return 0;
    }

    if (!mConnected) {
        int connRet = ConnectToBroker();
        if (connRet != 0) {
            return connRet;
        }
    }

    if (mDiscoveryStep < kDiscoveryTotalSteps) {
        return PublishNextDiscoveryStep();
    }

    if ((k_uptime_get() - mLastDiscoveryStepMs) < kDiscoveryPaceMs) {
        return 0;
    }

    SetFastPoll(true);
    PumpSocket(0);
    if (!mConnected) {
        return -ENOTCONN;
    }

    if ((k_uptime_get() - mLastOnlinePublishMs) >= kOnlineReassertIntervalMs) {
        if (PublishRaw(mAvailabilityTopic,
                       HaMqttProto::kAvailabilityOnline,
                       strlen(HaMqttProto::kAvailabilityOnline),
                       true) == 0) {
            mLastOnlinePublishMs = k_uptime_get();
        } else {
            return -ENOTCONN;
        }
    }

    char stateJson[HaMqttProto::kMaxStatePayloadLen] = {};
    const size_t jsonLen = HaMqttProto::FormatStatePayload(
        mPendingMeasurement, stateJson, sizeof(stateJson));
    if (jsonLen == 0u) {
        return -EINVAL;
    }

    int ret = PublishRaw(mStateTopic, stateJson, jsonLen, true);
    if (ret == 0) {
        mHasPendingPublish = false;
        PumpSocket(40);
        LOG_INF("MQTT state published [pkt=%u]: %s", mPendingMeasurement.packetId, stateJson);
    }
    return ret;
}

int ThreadMqttPublisher::Publish(const BthomeMeasurement &m, bool burst)
{
    ARG_UNUSED(burst);

    mPendingMeasurement          = m;
    mPendingMeasurement.packetId = ++mPacketId;
    mHasPendingPublish           = true;
    mHasValidMeasurement         = true;

    return TryFlushPending();
}

void ThreadMqttPublisher::ProcessBackground()
{
    if (!mConnected && !mOtaUpdater.IsActive()) {
        (void)ConnectToBroker();
    }

    if (mConnected) {
        PumpSocket(0);
        // When a wireless FOTA session is streaming chunks, pump consecutive TCP frames rapidly
        for (int i = 0; i < 8 && mConnected && mOtaUpdater.IsActive(); ++i) {
            PumpSocket(5);
        }
    }

    if (mConnected && mDiscoveryStep < kDiscoveryTotalSteps) {
        (void)PublishNextDiscoveryStep();
    }

    if (mHasPendingPublish && !mOtaUpdater.IsActive()) {
        (void)TryFlushPending();
    }

    if (mConnected) {
        PumpSocket(0);

        if (mConnected) {
            if (mClient.unacked_ping >= 2) {
                LOG_WRN("MQTT broker missed %d keepalive PINGRESPs; reconnecting",
                        static_cast<int>(mClient.unacked_ping));
                DisconnectBroker();
            } else {
                const int timeLeftMs = mqtt_keepalive_time_left(&mClient);
                const int64_t nowMs  = k_uptime_get();
                static constexpr int kPingEarlyThresholdMs =
                    (CONFIG_APP_MQTT_KEEPALIVE_SEC * 1000) / 2;
                if (timeLeftMs >= 0 &&
                    timeLeftMs <= kPingEarlyThresholdMs &&
                    (nowMs - mLastPingSentMs) >= 10000) {
                    SetFastPoll(true);
                    mLastPingSentMs = nowMs;
                    if (mqtt_ping(&mClient) != 0) {
                        DisconnectBroker();
                    } else {
                        PumpSocket(40);
                    }
                }
            }
        }
    }

    if (mFastPollActive &&
        !mHasPendingPublish &&
        (mDiscoveryStep >= kDiscoveryTotalSteps) &&
        (k_uptime_get() >= mFastPollDeadlineMs)) {
        SetFastPoll(false);
    }
}
