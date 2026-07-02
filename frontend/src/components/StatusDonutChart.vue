<template>
  <VChart class="trend-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart } from "echarts/charts";
import { LegendComponent, TooltipComponent } from "echarts/components";

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent]);

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

const option = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "item",
  },
  legend: {
    bottom: 0,
    textStyle: {
      color: "#cbd5e1",
    },
  },
  series: [
    {
      name: "设备状态",
      type: "pie",
      radius: ["45%", "72%"],
      center: ["50%", "45%"],
      avoidLabelOverlap: false,
      label: {
        color: "#e2e8f0",
        formatter: "{b}\n{c}",
      },
      itemStyle: {
        borderColor: "#0f172a",
        borderWidth: 4,
      },
      data: [
        { value: props.onlineCount, name: "在线设备", itemStyle: { color: "#22c55e" } },
        { value: props.offlineCount, name: "离线设备", itemStyle: { color: "#ef4444" } },
        { value: props.lampOnCount, name: "开灯设备", itemStyle: { color: "#38bdf8" } },
        { value: props.lampOffCount, name: "关灯设备", itemStyle: { color: "#64748b" } },
      ],
    },
  ],
}));
</script>
