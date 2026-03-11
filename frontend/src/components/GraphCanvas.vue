<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import ForceGraph from "force-graph";
import type { GraphLink, GraphNode } from "../types/api";

const props = defineProps<{
  nodes: GraphNode[];
  links: GraphLink[];
}>();

const emit = defineEmits<{
  (event: "nodeSelected", nodeId: string): void;
  (event: "edgeSelected", edgeId: string): void;
}>();

const root = ref<HTMLDivElement | null>(null);
let instance: ReturnType<typeof ForceGraph> | null = null;

function drawGraph() {
  if (!root.value || !instance) return;
  instance.graphData({
    nodes: props.nodes.map((node) => ({ ...node, id: node.node_id })),
    links: props.links.map((link) => ({ ...link, source: link.source, target: link.target }))
  });
}

onMounted(() => {
  if (!root.value) return;
  instance = ForceGraph()(root.value)
    .backgroundColor("rgba(10, 16, 19, 0)")
    .nodeLabel((node: GraphNode) => `${node.label} (${node.node_type})`)
    .nodeColor((node: GraphNode) => {
      if (node.node_type === "channel") return "#e0b66c";
      if (node.node_type === "cluster") return "#72d6c9";
      if (node.node_type === "team") return "#7da0ff";
      return "#f4efe6";
    })
    .nodeVal((node: GraphNode) => Math.max(3, Number(node.message_volume ?? 0) / 2))
    .linkColor(() => "rgba(255, 242, 218, 0.28)")
    .linkDirectionalParticles((link: GraphLink) => Math.min(6, Math.max(0, Math.round(link.weight / 2))))
    .linkDirectionalParticleWidth(1.5)
    .onNodeClick((node: GraphNode) => emit("nodeSelected", node.node_id))
    .onLinkClick((link: GraphLink) => emit("edgeSelected", link.edge_id));
  drawGraph();
});

watch(
  () => [props.nodes, props.links],
  () => drawGraph(),
  { deep: true }
);

onBeforeUnmount(() => {
  instance?.pauseAnimation();
  instance = null;
});
</script>

<template>
  <div class="graph-surface">
    <div ref="root" class="graph-canvas" />
  </div>
</template>

<style scoped>
.graph-surface {
  height: 100%;
  min-height: 460px;
  border: 1px solid rgba(255, 222, 170, 0.18);
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(255, 199, 103, 0.08), transparent 28%),
    radial-gradient(circle at bottom right, rgba(80, 160, 190, 0.1), transparent 24%),
    rgba(11, 15, 18, 0.8);
  box-shadow: inset 0 1px 0 rgba(255, 248, 231, 0.06);
}

.graph-canvas {
  width: 100%;
  height: 100%;
}
</style>
