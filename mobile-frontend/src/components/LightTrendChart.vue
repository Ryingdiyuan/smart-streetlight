<template>
  <div class="chart-shell">
    <VChart :option="option" autoresize class="chart" />
  </div>
</template>

<script setup lang="ts">
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import VChart from "vue-echarts";
import { computed } from "vue";
import type { LightHistoryPoint } from "@/types/models";

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent]);

const props = defineProps<{
  points: LightHistoryPoint[];
}>();

const option = computed(() => ({
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(6, 14, 24, 0.94)",
    borderColor: "rgba(54, 215, 255, 0.2)",
    textStyle: { color: "#ecf4ff" },
  },
  grid: {
    top: 12,
    right: 10,
    bottom: 18,
    left: 10,
    containLabel: true,
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: props.points.map((point) => point.timestamp.slice(11, 16)),
    axisLabel: { color: "#8fa5c1", fontSize: 10 },
    axisLine: { lineStyle: { color: "rgba(143, 165, 193, 0.18)" } },
  },
  yAxis: {
    type: "value",
    axisLabel: { color: "#8fa5c1", fontSize: 10 },
    splitLine: { lineStyle: { color: "rgba(143, 165, 193, 0.12)" } },
  },
  series: [
    {
      data: props.points.map((point) => point.lightIntensity),
      type: "line",
      smooth: true,
      showSymbol: false,
      lineStyle: { color: "#36d7ff", width: 3 },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(54, 215, 255, 0.35)" },
            { offset: 1, color: "rgba(54, 215, 255, 0.02)" },
          ],
        },
      },
    },
  ],
}));
</script>

<style scoped>
.chart-shell {
  height: 200px;
  border-radius: 20px;
  overflow: hidden;
  background: var(--surface-chart);
}

.chart {
  height: 100%;
  width: 100%;
}
</style>
