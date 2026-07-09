<template>
  <view class="detail-page">
    <LoadingSpinner v-if="loading" text="加载设备详情..." />
    <template v-else-if="device">
      <scroll-view scroll-y class="detail-scroll">
        <!-- Basic info -->
        <view class="card">
          <text class="card-title">基础信息</text>
          <view class="info-grid">
            <view class="info-item">
              <text class="info-label">设备编号</text>
              <text class="info-value">{{ device.deviceCode }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">设备名称</text>
              <text class="info-value">{{ device.deviceName }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">位置</text>
              <text class="info-value">{{ device.location }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">状态</text>
              <StatusBadge :type="device.status === 'online' ? 'online' : 'offline'">
                {{ device.status === "online" ? "在线" : "离线" }}
              </StatusBadge>
            </view>
            <view class="info-item">
              <text class="info-label">心跳</text>
              <text class="info-value">{{ device.lastHeartbeatAt }}</text>
            </view>
          </view>
        </view>

        <!-- Current state -->
        <view class="card">
          <text class="card-title">当前状态</text>
          <view class="state-grid">
            <view class="state-item">
              <text class="state-value intensity">{{ device.currentLightIntensity }}</text>
              <text class="state-label">光照强度 (lux)</text>
            </view>
            <view class="state-item">
              <StatusBadge :type="device.lampStatus === 'ON' ? 'on' : 'off'" size="md">
                {{ device.lampStatus === "ON" ? "灯亮" : "灯灭" }}
              </StatusBadge>
              <text class="state-label">灯具状态</text>
            </view>
          </view>
        </view>

        <!-- Controls (maintainer+) -->
        <view v-if="canOperate" class="card">
          <text class="card-title">控制</text>
          <view class="control-row">
            <view class="control-btn on" @tap="sendCommand('TURN_ON')">开灯</view>
            <view class="control-btn off" @tap="sendCommand('TURN_OFF')">关灯</view>
          </view>
        </view>

        <!-- Threshold (maintainer+) -->
        <view v-if="canOperate" class="card">
          <text class="card-title">阈值配置</text>
          <view class="threshold-row">
            <view class="threshold-item">
              <text class="threshold-label">下限</text>
              <text class="threshold-value">{{ device.threshold.lowThreshold }} lux</text>
            </view>
            <text class="threshold-arrow">→</text>
            <view class="threshold-item">
              <text class="threshold-label">上限</text>
              <text class="threshold-value">{{ device.threshold.highThreshold }} lux</text>
            </view>
          </view>
          <view class="threshold-status">
            <StatusBadge :type="device.threshold.enabled ? 'online' : 'offline'" size="sm">
              {{ device.threshold.enabled ? "自动控制已开启" : "自动控制已关闭" }}
            </StatusBadge>
          </view>
        </view>

        <!-- Light history -->
        <view class="card">
          <text class="card-title">光照历史 (最近)</text>
          <view v-if="device.history.length" class="history-list">
            <view v-for="(point, i) in device.history.slice(0, 10)" :key="i" class="history-row">
              <text class="history-time">{{ point.timestamp }}</text>
              <text class="history-intensity" :style="{ color: intensityColor(point.lightIntensity) }">
                {{ point.lightIntensity }} lux
              </text>
              <StatusBadge :type="point.lampStatus === 'ON' ? 'on' : 'off'" size="sm">
                {{ point.lampStatus === "ON" ? "灯亮" : "灯灭" }}
              </StatusBadge>
            </view>
          </view>
          <EmptyState v-else message="暂无光照历史" />
        </view>

        <!-- Command logs -->
        <view class="card">
          <text class="card-title">控制日志</text>
          <view v-if="device.commandLogs.length" class="cmd-list">
            <view v-for="cmd in device.commandLogs.slice(0, 10)" :key="cmd.id" class="cmd-row">
              <text class="cmd-command">{{ cmd.command }}</text>
              <StatusBadge
                :type="cmd.result === 'success' ? 'success' : cmd.result === 'failed' ? 'failed' : 'pending'"
                size="sm"
              >
                {{ cmd.result === 'success' ? '成功' : cmd.result === 'failed' ? '失败' : cmd.result === 'skipped' ? '跳过' : '待处理' }}
              </StatusBadge>
              <text class="cmd-time">{{ cmd.createdAt }}</text>
            </view>
          </view>
          <EmptyState v-else message="暂无控制记录" />
        </view>

        <!-- Alarms -->
        <view class="card">
          <text class="card-title">关联告警</text>
          <AlarmItem
            v-for="alarm in device.alarms"
            :key="alarm.id"
            :alarm="alarm"
            :show-handle="canHandle"
            @handle="onHandleAlarm(alarm)"
          />
          <EmptyState v-if="!device.alarms.length" message="暂无告警" />
        </view>
      </scroll-view>
    </template>
    <EmptyState v-else message="设备不存在" icon="🔍" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onShow, onHide } from "@dcloudio/uni-app";
import type { DeviceDetail, AlarmRecord } from "@/types/models";
import { getDeviceDetail, sendDeviceCommand } from "@/services/api/deviceService";
import { handleAlarm as handleAlarmApi } from "@/services/api/alarmService";
import { can } from "@/services/permissions";
import StatusBadge from "@/components/StatusBadge.vue";
import AlarmItem from "@/components/AlarmItem.vue";
import LoadingSpinner from "@/components/LoadingSpinner.vue";
import EmptyState from "@/components/EmptyState.vue";

const loading = ref(true);
const device = ref<DeviceDetail | null>(null);
const deviceId = ref(0);
const canOperate = can("operateDevices");
const canHandle = can("handleAlarms");
let refreshTimer: ReturnType<typeof setInterval> | null = null;

function intensityColor(lux: number): string {
  if (lux < 80) return "#ff5252";
  if (lux < 180) return "#ffc107";
  if (lux < 300) return "#00c853";
  return "#38d5ff";
}

async function loadData() {
  if (!deviceId.value) return;
  try {
    device.value = await getDeviceDetail(deviceId.value);
  } catch (err) {
    console.error("加载设备详情失败", err);
  } finally {
    loading.value = false;
  }
}

async function sendCommand(command: "TURN_ON" | "TURN_OFF") {
  try {
    await sendDeviceCommand(deviceId.value, command);
    uni.showToast({ title: "命令已发送", icon: "success" });
    loadData();
  } catch (err) {
    uni.showToast({ title: "命令发送失败", icon: "error" });
  }
}

async function onHandleAlarm(alarm: AlarmRecord) {
  try {
    await handleAlarmApi(alarm.id);
    uni.showToast({ title: "告警已确认", icon: "success" });
    loadData();
  } catch (err) {
    uni.showToast({ title: "操作失败", icon: "error" });
  }
}

onShow(() => {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1] as any;
  deviceId.value = Number(page.$page?.options?.id || page.options?.id || 0);
  if (deviceId.value) {
    loading.value = true;
    loadData();
    refreshTimer = setInterval(loadData, 3000);
  }
});

onHide(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>

<style scoped>
.detail-page {
  padding: 12px 16px;
  height: 100%;
}

.detail-scroll {
  height: 100%;
  overflow-y: auto;
}

.card {
  background: rgba(10, 26, 45, 0.8);
  border: 1px solid rgba(56, 213, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #e8edf3;
  margin-bottom: 12px;
  display: block;
  border-left: 3px solid #38d5ff;
  padding-left: 10px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-label {
  font-size: 13px;
  color: #6a8299;
  width: 60px;
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  color: #e8edf3;
  flex: 1;
}

.state-grid {
  display: flex;
  gap: 20px;
}

.state-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px;
  background: rgba(7, 17, 29, 0.5);
  border-radius: 10px;
}

.state-value.intensity {
  font-size: 32px;
  font-weight: 700;
  color: #38d5ff;
}

.state-label {
  font-size: 12px;
  color: #6a8299;
}

.control-row {
  display: flex;
  gap: 12px;
}

.control-btn {
  flex: 1;
  height: 46px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.control-btn.on {
  background: rgba(255, 193, 7, 0.2);
  border: 1px solid rgba(255, 193, 7, 0.4);
  color: #ffc107;
}

.control-btn.off {
  background: rgba(158, 180, 200, 0.2);
  border: 1px solid rgba(158, 180, 200, 0.4);
  color: #9fb4c8;
}

.threshold-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 10px;
}

.threshold-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.threshold-label {
  font-size: 12px;
  color: #6a8299;
}

.threshold-value {
  font-size: 20px;
  font-weight: 700;
  color: #38d5ff;
}

.threshold-arrow {
  font-size: 20px;
  color: #6a8299;
}

.threshold-status {
  display: flex;
  justify-content: center;
}

.history-list,
.cmd-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-row,
.cmd-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(7, 17, 29, 0.4);
  border-radius: 6px;
}

.history-time,
.cmd-time {
  font-size: 12px;
  color: #6a8299;
  min-width: 100px;
}

.history-intensity {
  font-size: 14px;
  font-weight: 600;
  min-width: 60px;
}

.cmd-command {
  font-size: 13px;
  color: #38d5ff;
  font-weight: 500;
  min-width: 70px;
}
</style>
