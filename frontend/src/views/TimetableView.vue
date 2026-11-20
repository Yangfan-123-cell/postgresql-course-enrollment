<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";
import type { Timetable } from "../api/types";
import { errorMessage } from "../api/client";
import { weekdays } from "./format";
const data = ref<Timetable>({ term: "", cells: [] }),
  error = ref(""),
  loading = ref(false);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await api.timetable();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">WEEKLY SCHEDULE</p>
      <h1>每周课表</h1>
      <p class="muted">{{ data.term }} · 按节次查看每周安排</p>
    </div>
    <button @click="load" :disabled="loading">刷新课表</button>
  </div>
  <p v-if="error" role="alert" class="notice error">{{ error }}</p>
  <p v-if="loading" class="empty">加载中…</p>
  <div v-else class="panel timetable-wrap">
    <div class="timetable">
      <div class="grid-heading">节次</div>
      <div v-for="day in weekdays" :key="day" class="grid-heading">
        周{{ day }}
      </div>
      <template v-for="period in 12" :key="period"
        ><div class="period" :style="{ gridRow: period + 1, gridColumn: 1 }">
          {{ period }}
        </div>
        <div
          v-for="day in 7"
          :key="day"
          class="grid-cell"
          :style="{ gridRow: period + 1, gridColumn: day + 1 }"
        ></div></template
      ><RouterLink
        v-for="(cell, i) in data.cells"
        :key="i"
        class="timetable-course"
        :to="`/sections/${cell.section_id}`"
        :style="{
          gridColumn: cell.weekday + 1,
          gridRow: `${cell.start_period + 1} / ${cell.end_period + 2}`,
          borderLeftColor: cell.color,
        }"
        ><strong>{{ cell.course_name }}</strong
        ><span
          >{{ cell.start_period }}–{{ cell.end_period }} 节</span
        ></RouterLink
      >
    </div>
  </div>
  <p v-if="!loading && !error && !data.cells.length" class="notice">
    暂无已选课程，选课成功后课表会显示在这里。
  </p>
</template>
