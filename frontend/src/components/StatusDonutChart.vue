<template>
  <div class="status-donut-layout">
    <div class="status-donut-grid">
      <div class="status-donut-panel">
        <VChart class="status-donut-chart" :option="onlineOption" autoresize />
        <div class="summary-box">
          <strong>在线 / 离线</strong>
          <span>{{ onlineCount }} / {{ offlineCount }}</span>
        </div>
      </div>

      <div class="status-donut-panel">
        <VChart class="status-donut-chart" :option="lampOption" autoresize />
        <div class="summary-box">
          <strong>开灯 / 关灯</strong>
          <span>{{ lampOnCount }} / {{ lampOffCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { PieChart } from "echarts/charts";
import { GraphicComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent, GraphicComponent]);

defineOptions({
  components: {
    VChart,
  },
});

const props = defineProps<{
  onlineCount: number;
  offlineCount: number;
  lampOnCount: number;
  lampOffCount: number;
}>();

function buildOption(
  totalText: string,
  totalLabel: string,
  seriesName: string,
  legendData: string[],
  data: Array<{ value: number; name: string; itemStyle: { color: string } }>,
) {
  return {
  backgroundColor: "transparent",
  tooltip: {
    trigger: "item",
  },
  legend: {
    bottom: 4,
    icon: "roundRect",
    itemWidth: 14,
    itemHeight: 10,
    textStyle: {
      color: "#cbd5e1",
    },
    data: legendData,
  },
  graphic: [
    {
      type: "text",
      left: "center",
      top: "36%",
      style: {
        text: totalText,
        fill: "#e2e8f0",
        fontSize: 24,
        fontWeight: 700,
        textAlign: "center",
      },
    },
    {
      type: "text",
      left: "center",
      top: "48%",
      style: {
        text: totalLabel,
        fill: "#94a3b8",
        fontSize: 13,
        textAlign: "center",
      },
    },
  ],
  series: [
    {
      name: seriesName,
      type: "pie",
      radius: ["48%", "72%"],
      center: ["50%", "40%"],
      avoidLabelOverlap: true,
      label: {
        show: false,
      },
      labelLine: {
        show: false,
      },
      itemStyle: {
        borderColor: "#0f172a",
        borderWidth: 4,
      },
      data,
    },
  ],
  };
}

const totalCount = computed(() => props.onlineCount + props.offlineCount);

const onlineOption = computed(() =>
  buildOption(`${totalCount.value}`, "设备总数", "设备在线状态", ["在线设备", "离线设备"], [
    { value: props.onlineCount, name: "在线设备", itemStyle: { color: "#22c55e" } },
    { value: props.offlineCount, name: "离线设备", itemStyle: { color: "#64748b" } },
  ]),
);

const lampOption = computed(() =>
  buildOption(`${props.lampOnCount + props.lampOffCount}`, "路灯总数", "路灯开关状态", ["开灯设备", "关灯设备"], [
    { value: props.lampOnCount, name: "开灯设备", itemStyle: { color: "#38bdf8" } },
    { value: props.lampOffCount, name: "关灯设备", itemStyle: { color: "#1e3a8a" } },
  ]),
);
</script>
