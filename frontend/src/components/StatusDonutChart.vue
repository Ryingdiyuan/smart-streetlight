<template>
  <div class="status-donut-layout">
    <VChart class="trend-chart" :option="option" autoresize />
    <div class="status-summary-row">
      <div class="summary-box">
        <strong>在线 / 离线</strong>
        <span>{{ onlineCount }} / {{ offlineCount }}</span>
      </div>
      <div class="summary-box">
        <strong>开灯 / 关灯</strong>
        <span>{{ lampOnCount }} / {{ lampOffCount }}</span>
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

const totalCount = computed(() => props.onlineCount + props.offlineCount);

const option = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "item",
  },
  legend: {
    bottom: 0,
    icon: "roundRect",
    itemWidth: 14,
    itemHeight: 10,
    textStyle: {
      color: "#cbd5e1",
    },
    data: ["在线设备", "离线设备"],
  },
  graphic: [
    {
      type: "text",
      left: "center",
      top: "38%",
      style: {
        text: `${totalCount.value}`,
        fill: "#e2e8f0",
        fontSize: 26,
        fontWeight: 700,
        textAlign: "center",
      },
    },
    {
      type: "text",
      left: "center",
      top: "50%",
      style: {
        text: "设备总数",
        fill: "#94a3b8",
        fontSize: 13,
        textAlign: "center",
      },
    },
  ],
  series: [
    {
      name: "设备在线状态",
      type: "pie",
      radius: ["48%", "72%"],
      center: ["50%", "42%"],
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
      data: [
        { value: props.onlineCount, name: "在线设备", itemStyle: { color: "#22c55e" } },
        { value: props.offlineCount, name: "离线设备", itemStyle: { color: "#64748b" } },
      ],
    },
  ],
}));
</script>
