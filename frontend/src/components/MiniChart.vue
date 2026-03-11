<script setup lang="ts">
import * as echarts from "echarts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{
  title: string;
  labels: string[];
  values: number[];
  type?: "bar" | "line";
}>();

const root = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function render() {
  if (!root.value) return;
  chart ??= echarts.init(root.value);
  chart.setOption({
    backgroundColor: "transparent",
    title: {
      text: props.title,
      textStyle: { color: "#f4efe6", fontFamily: "Iowan Old Style, Georgia, serif", fontWeight: 600 }
    },
    xAxis: {
      type: "category",
      data: props.labels,
      axisLabel: { color: "#b8b2a8" },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } }
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#b8b2a8" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.08)" } }
    },
    series: [
      {
        type: props.type ?? "bar",
        data: props.values,
        smooth: true,
        itemStyle: { color: "#e0b66c" },
        lineStyle: { color: "#72d6c9", width: 3 },
        areaStyle: props.type === "line" ? { color: "rgba(114, 214, 201, 0.12)" } : undefined
      }
    ]
  });
}

onMounted(() => render());
watch(() => [props.labels, props.values], () => render(), { deep: true });
onBeforeUnmount(() => chart?.dispose());
</script>

<template>
  <div ref="root" class="mini-chart" />
</template>

<style scoped>
.mini-chart {
  height: 280px;
  border-radius: 26px;
  padding: 0.6rem;
  background: rgba(13, 17, 19, 0.88);
  border: 1px solid rgba(255, 227, 184, 0.14);
}
</style>
