<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import { PERIODS, PERIOD_GROUPS } from "../config";
import { todayWeekday, weekdays } from "../format";
import type { GridCell } from "./grid";

const props = withDefaults(
  defineProps<{ cells: GridCell[]; weekend?: boolean; highlightToday?: boolean }>(),
  { weekend: true, highlightToday: true },
);
const days = computed(() => (props.weekend ? 7 : 5));
const visible = computed(() => props.cells.filter((c) => c.weekday <= days.value));
const today = todayWeekday();
const groupEnds = PERIOD_GROUPS.map((g) => g.to);
</script>
<template>
  <div
    class="timetable"
    :style="{ gridTemplateColumns: `76px repeat(${days}, minmax(96px, 1fr))` }"
  >
    <div class="grid-heading corner">节次</div>
    <div
      v-for="d in days"
      :key="d"
      class="grid-heading"
      :class="{ today: highlightToday && d === today }"
    >
      周{{ weekdays[d - 1] }}
      <small v-if="highlightToday && d === today">今天</small>
    </div>
    <template v-for="period in 12" :key="period">
      <div
        class="period"
        :class="{ 'group-end': groupEnds.includes(period) }"
        :style="{ gridRow: period + 1, gridColumn: 1 }"
      >
        <strong>{{ period }}</strong>
        <span>{{ PERIODS[period - 1]![0] }}</span>
      </div>
      <div
        v-for="d in days"
        :key="d"
        class="grid-cell"
        :class="{
          'group-end': groupEnds.includes(period),
          today: highlightToday && d === today,
        }"
        :style="{ gridRow: period + 1, gridColumn: d + 1 }"
      ></div>
    </template>
    <component
      :is="cell.to ? RouterLink : 'div'"
      v-for="cell in visible"
      :key="cell.key"
      :to="cell.to"
      class="timetable-course"
      :class="{ ghost: cell.ghost, conflict: cell.conflict }"
      :style="{
        gridColumn: cell.weekday + 1,
        gridRow: `${cell.start_period + 1} / ${cell.end_period + 2}`,
        '--c': cell.color,
      }"
      ><strong>{{ cell.title }}</strong
      ><span>{{ cell.sub ?? `${cell.start_period}–${cell.end_period} 节` }}</span></component
    >
  </div>
</template>
