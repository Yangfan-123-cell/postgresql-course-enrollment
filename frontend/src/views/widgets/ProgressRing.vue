<script setup lang="ts">
import { computed } from "vue";
const props = withDefaults(
  defineProps<{
    value: number;
    max: number;
    size?: number;
    stroke?: number;
    color?: string;
    track?: string;
  }>(),
  { size: 120, stroke: 10, color: "#2f5fb3", track: "#e8edf5" },
);
const radius = computed(() => (props.size - props.stroke) / 2);
const length = computed(() => 2 * Math.PI * radius.value);
const ratio = computed(() =>
  props.max > 0 ? Math.min(1, Math.max(0, props.value / props.max)) : 0,
);
</script>
<template>
  <div class="ring" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size" aria-hidden="true" focusable="false">
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="track"
        :stroke-width="stroke"
      />
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="color"
        :stroke-width="stroke"
        stroke-linecap="round"
        :stroke-dasharray="length"
        :stroke-dashoffset="length * (1 - ratio)"
        :transform="`rotate(-90 ${size / 2} ${size / 2})`"
        class="ring-value"
      />
    </svg>
    <div class="ring-label"><slot /></div>
  </div>
</template>
