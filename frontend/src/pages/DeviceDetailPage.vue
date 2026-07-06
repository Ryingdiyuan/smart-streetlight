<template>
  <section class="page-section">
    <header class="section-header">
      <div>
        <p class="section-kicker">Device Detail</p>
        <h3>设备详情</h3>
      </div>
      <div class="button-row">
        <p class="section-note">查看设备详情、阈值配置、控制日志和关联告警。</p>
        <button class="ghost-button" type="button" @click="goBackToList">返回设备列表</button>
      </div>
    </header>

    <div v-if="device" class="stats-grid">
      <StatCard v-for="item in overviewStats" :key="item.label" :stat="item" />
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="基础信息" :subtitle="`设备 ID：${route.params.id}`">
        <dl class="detail-list">
          <div>
            <dt>设备编号</dt>
            <dd>{{ device.deviceCode }}</dd>
          </div>
          <div>
            <dt>在线状态</dt>
            <dd>
              <StatusBadge :status="device.status" :text="device.status === 'online' ? '在线' : '离线'" />
            </dd>
          </div>
          <div>
            <dt>当前光照</dt>
            <dd>{{ device.currentLightIntensity }} lx</dd>
          </div>
          <div>
            <dt>路灯状态</dt>
            <dd>
              <StatusBadge
                :status="device.lampStatus === 'ON' ? 'success' : 'info'"
                :text="device.lampStatus"
              />
            </dd>
          </div>
          <div>
            <dt>安装位置</dt>
            <dd>{{ device.location }}</dd>
          </div>
          <div>
            <dt>最近心跳</dt>
            <dd>{{ device.lastHeartbeatAt }}</dd>
          </div>
        </dl>
      </PanelCard>

      <PanelCard title="控制与阈值" subtitle="管理员和维修人员可保存阈值并下发控制命令">
        <div v-if="canOperateDevices" class="button-row">
          <button class="primary-button" @click="handleCommand('TURN_ON')">手动开灯</button>
          <button class="ghost-button" @click="handleCommand('TURN_OFF')">手动关灯</button>
        </div>
        <p v-else class="inline-note">当前角色仅可查看阈值配置，不能执行控制或保存修改。</p>

        <div class="detail-tip-grid">
          <div class="summary-box">
            <strong>自动控制</strong>
            <span>{{ threshold.enabled ? "已启用" : "未启用" }}</span>
          </div>
          <div class="summary-box">
            <strong>建议动作</strong>
            <span>{{ thresholdSuggestion }}</span>
          </div>
        </div>

        <div class="form-grid">
          <label>
            <span>开灯阈值</span>
            <input v-model.number="threshold.lowThreshold" type="number" :disabled="!canOperateDevices" />
          </label>
          <label>
            <span>关灯阈值</span>
            <input v-model.number="threshold.highThreshold" type="number" :disabled="!canOperateDevices" />
          </label>
          <label class="checkbox-field">
            <input v-model="threshold.enabled" type="checkbox" :disabled="!canOperateDevices" />
            <span>启用自动控制</span>
          </label>
        </div>

        <div class="button-row">
          <button v-if="canOperateDevices" class="primary-button" @click="saveThreshold">保存阈值</button>
          <span class="inline-note">{{ actionMessage }}</span>
        </div>
      </PanelCard>
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="历史光照曲线" subtitle="设备详情页趋势展示">
        <TrendLineChart :points="device.history" />
      </PanelCard>
      <PanelCard title="状态摘要" subtitle="当前设备运行情况">
        <div class="detail-summary-grid">
          <div class="summary-box">
            <strong>历史点位</strong>
            <span>{{ device.history.length }} 条</span>
          </div>
          <div class="summary-box">
            <strong>控制日志</strong>
            <span>{{ device.commandLogs.length }} 条</span>
          </div>
          <div class="summary-box">
            <strong>关联告警</strong>
            <span>{{ device.alarms.length }} 条</span>
          </div>
          <div class="summary-box">
            <strong>阈值区间</strong>
            <span>{{ threshold.lowThreshold }} - {{ threshold.highThreshold }} lx</span>
          </div>
          <div class="summary-box">
            <strong>最新趋势</strong>
            <span>{{ trendLabel }}</span>
          </div>
          <div class="summary-box">
            <strong>最后一次控制</strong>
            <span>{{ lastCommandLabel }}</span>
          </div>
        </div>
      </PanelCard>
    </div>

    <div v-if="device" class="content-grid two-columns">
      <PanelCard title="最近采样记录" subtitle="用于展示上报历史点位">
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>光照强度</th>
                <th>路灯状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="point in recentHistory" :key="point.timestamp">
                <td>{{ point.timestamp }}</td>
                <td>{{ point.lightIntensity }} lx</td>
                <td>
                  <StatusBadge
                    :status="point.lampStatus === 'ON' ? 'success' : 'info'"
                    :text="point.lampStatus"
                  />
                </td>
              </tr>
              <tr v-if="!recentHistory.length">
                <td colspan="3" class="table-empty">当前没有采样记录</td>
              </tr>
            </tbody>
          </table>
        </div>
      </PanelCard>

      <PanelCard title="运维建议" subtitle="结合当前阈值和设备状态给出提示">
        <div class="detail-summary-grid">
          <div class="summary-box">
            <strong>巡检建议</strong>
            <span>{{ maintenanceSuggestion }}</span>
          </div>
          <div class="summary-box">
            <strong>联调建议</strong>
            <span>{{ integrationSuggestion }}</span>
          </div>
        </div>
      </PanelCard>
    </div>

    <div v-if="device" class="content-grid two-columns">
      <CommandLogPanel :logs="device.commandLogs" />
      <AlarmRecordPanel :alarms="device.alarms" />
    </div>

    <PanelCard v-else title="设备详情" subtitle="数据不存在">
      <div class="placeholder-box">未找到对应设备，请返回列表页重新选择。</div>
    </PanelCard>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AlarmRecordPanel from "@/components/AlarmRecordPanel.vue";
import CommandLogPanel from "@/components/CommandLogPanel.vue";
import PanelCard from "@/components/PanelCard.vue";
import StatCard from "@/components/StatCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import TrendLineChart from "@/components/TrendLineChart.vue";
import { getDeviceDetail, sendDeviceCommand, updateDeviceThreshold } from "@/services/deviceService";
import { can } from "@/services/permissions";
import type { CommandLog, DeviceDetail, ThresholdConfig } from "@/types/models";

const route = useRoute();
const router = useRouter();
const device = ref<DeviceDetail | null>(null);
const actionMessage = ref("可查看真实后端阈值和控制状态");
let refreshTimer: number | undefined;
let commandRefreshTimer: number | undefined;

const threshold = reactive<ThresholdConfig>({
  deviceId: "",
  lowThreshold: 0,
  highThreshold: 0,
  enabled: false,
});

const canOperateDevices = computed(() => can("operateDevices"));

const overviewStats = computed(() => {
  if (!device.value) return [];
  return [
    {
      label: "当前光照",
      value: `${device.value.currentLightIntensity}`,
      helper: "单位 lx",
    },
    {
      label: "在线状态",
      value: device.value.status === "online" ? "在线" : "离线",
      helper: "基于最近心跳判断",
    },
    {
      label: "自动控制",
      value: threshold.enabled ? "开启" : "关闭",
      helper: "当前阈值策略状态",
    },
    {
      label: "告警数量",
      value: String(device.value.alarms.length),
      helper: "设备关联异常记录",
    },
  ];
});

const recentHistory = computed(() => device.value?.history.slice().reverse().slice(0, 5) ?? []);
const lastCommand = computed<CommandLog | null>(() => device.value?.commandLogs[0] ?? null);

const lastCommandLabel = computed(() => {
  if (!lastCommand.value) return "暂无控制记录";
  return `${lastCommand.value.command} / ${lastCommand.value.result}`;
});

const trendLabel = computed(() => {
  const history = device.value?.history ?? [];
  if (history.length < 2) return "数据不足";
  const latest = history[history.length - 1].lightIntensity;
  const previous = history[history.length - 2].lightIntensity;
  if (latest > previous) return `较上一周期上升 ${latest - previous} lx`;
  if (latest < previous) return `较上一周期下降 ${previous - latest} lx`;
  return "与上一周期持平";
});

const thresholdSuggestion = computed(() => {
  if (!device.value) return "等待设备数据";
  if (!threshold.enabled) return "建议先启用自动控制后再观察效果";
  if (device.value.currentLightIntensity < threshold.lowThreshold) return "当前偏暗，建议保持开灯";
  if (device.value.currentLightIntensity > threshold.highThreshold) return "当前偏亮，可考虑关灯";
  return "当前处于阈值区间内，保持现状即可";
});

const maintenanceSuggestion = computed(() => {
  if (!device.value) return "等待设备数据";
  if (device.value.status === "offline") return "设备离线，优先检查供电、网络和 MQTT 心跳。";
  if (device.value.alarms.length > 0) return "存在历史告警，建议结合日志核查控制链路。";
  return "设备运行平稳，可继续观察趋势数据。";
});

const integrationSuggestion = computed(() => {
  if (!device.value) return "等待设备数据";
  if (!device.value.commandLogs.length) return "联调时优先确认控制日志回写。";
  if (device.value.commandLogs.some((log) => log.result === "pending")) {
    return "存在 pending 指令，建议补充执行结果轮询。";
  }
  return "可继续联调设备详情聚合接口与告警接口。";
});

async function loadDetail() {
  const currentId = Number(route.params.id);
  device.value = await getDeviceDetail(currentId);
  if (device.value) {
    Object.assign(threshold, device.value.threshold);
  }
}

async function saveThreshold() {
  if (!device.value || !canOperateDevices.value) return;
  const saved = await updateDeviceThreshold(device.value.id, { ...threshold });
  Object.assign(threshold, saved);
  actionMessage.value = "阈值已保存到真实后端";
}

async function handleCommand(command: "TURN_ON" | "TURN_OFF") {
  if (!device.value || !canOperateDevices.value) return;
  const log = await sendDeviceCommand(device.value.id, command);
  actionMessage.value = `已发送 ${log.command} 指令，结果：${log.result}`;
  await loadDetail();
  if (commandRefreshTimer !== undefined) {
    window.clearTimeout(commandRefreshTimer);
  }
  commandRefreshTimer = window.setTimeout(() => {
    void loadDetail();
  }, 1200);
}

async function goBackToList() {
  await router.push("/devices");
}

onMounted(() => {
  void loadDetail();
  refreshTimer = window.setInterval(() => {
    void loadDetail();
  }, 3000);
});

onBeforeUnmount(() => {
  if (refreshTimer !== undefined) {
    window.clearInterval(refreshTimer);
  }
  if (commandRefreshTimer !== undefined) {
    window.clearTimeout(commandRefreshTimer);
  }
});

watch(() => route.params.id, loadDetail);
</script>
