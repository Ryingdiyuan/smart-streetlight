<template>
  <VChart class="trend-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";

import type { LightHistoryPoint } from "@/types/models";

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

defineOptions({
  components: {
    VChart,
  },
});

const props = defineProps<{
  points: LightHistoryPoint[];
}>();

const option = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "axis",
  },
  legend: {
    data: ["光照强度"],
    textStyle: {
      color: "#cbd5e1",
    },
  },
  grid: {
    top: 42,
    left: 28,
    right: 16,
    bottom: 28,
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: props.points.map((item) => item.timestamp),
    axisLine: {
      lineStyle: {
        color: "rgba(148, 163, 184, 0.35)",
      },
    },
    axisLabel: {
      color: "#94a3b8",
    },
  },
  yAxis: {
    type: "value",
    axisLine: {
      show: false,
    },
    splitLine: {
      lineStyle: {
        color: "rgba(148, 163, 184, 0.12)",
      },
    },
    axisLabel: {
      color: "#94a3b8",
    },
  },
  series: [
    {
      name: "光照强度",
      type: "line",
      smooth: true,
      data: props.points.map((item) => item.lightIntensity),
      symbolSize: 8,
      lineStyle: {
        width: 3,
        color: "#38bdf8",
      },
      itemStyle: {
        color: "#38bdf8",
      },
      areaStyle: {
        color: "rgba(56, 189, 248, 0.18)",
      },
    },
  ],
}));
</script>
