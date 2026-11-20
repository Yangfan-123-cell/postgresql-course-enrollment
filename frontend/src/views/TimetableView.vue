<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import type { Timetable } from "../api/types";
import { errorMessage } from "../api/client";
import { useCart } from "../stores/cart";
import Icon from "./widgets/Icon.vue";
import TimetableGrid from "./widgets/TimetableGrid.vue";
import type { GridCell } from "./widgets/grid";
import { PERIODS } from "./config";
import { colorOf, conflictNames, periodTime } from "./format";

const cart = useCart(),
  data = ref<Timetable>({ term: "", cells: [] }),
  error = ref(""),
  loading = ref(false),
  showWeekend = ref(false),
  showCart = ref(true);

const enrolledIds = computed(
  () => new Set(data.value.cells.map((c) => c.section_id)),
);
const enrolledRefs = computed(() =>
  data.value.cells.map((c) => ({
    id: c.section_id,
    name: c.course_name,
    meetings: [
      {
        weekday: c.weekday,
        start_period: c.start_period,
        end_period: c.end_period,
      },
    ],
  })),
);

const gridCells = computed<GridCell[]>(() => {
  const real: GridCell[] = data.value.cells.map((c, i) => ({
    key: `real-${c.section_id}-${i}`,
    weekday: c.weekday,
    start_period: c.start_period,
    end_period: c.end_period,
    title: c.course_name,
    sub: `${c.start_period}–${c.end_period} 节 · ${periodTime(c)}`,
    color: c.color || colorOf(c.section_id),
    to: `/sections/${c.section_id}`,
  }));
  if (!showCart.value) return real;
  const ghost: GridCell[] = cart.items
    .filter((item) => !enrolledIds.value.has(item.section_id))
    .flatMap((item) => {
      const conflicts = conflictNames(
        item.meetings,
        enrolledRefs.value,
        item.section_id,
      );
      return item.meetings.map((m, i) => ({
        key: `cart-${item.section_id}-${i}`,
        weekday: m.weekday,
        start_period: m.start_period,
        end_period: m.end_period,
        title: item.name,
        sub: conflicts.length ? "与已选课程冲突" : `${m.start_period}–${m.end_period} 节 · 选课单`,
        color: conflicts.length ? "#c43e3b" : colorOf(item.section_id),
        to: `/sections/${item.section_id}`,
        ghost: true,
        conflict: conflicts.length > 0,
      }));
    });
  return [...real, ...ghost];
});

const hasWeekend = computed(
  () => showWeekend.value || gridCells.value.some((c) => c.weekday > 5),
);

function printPage() {
  window.print();
}

function exportIcs() {
  // 以 2026-09-07（周一）作为示例学期第一周起始，生成标准周循环日程
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//CourseSelect//Timetable//ZH",
  ];
  for (const c of data.value.cells) {
    const day = 6 + c.weekday; // 7..13
    const dd = String(day).padStart(2, "0");
    const st = (PERIODS[c.start_period - 1]?.[0] ?? "08:00").replace(":", "");
    const ed = (PERIODS[c.end_period - 1]?.[1] ?? "09:35").replace(":", "");
    lines.push(
      "BEGIN:VEVENT",
      `UID:section-${c.section_id}-${c.weekday}-${c.start_period}@courseselect`,
      `SUMMARY:${c.course_name}`,
      `DTSTART;TZID=Asia/Shanghai:202609${dd}T${st}00`,
      `DTEND;TZID=Asia/Shanghai:202609${dd}T${ed}00`,
      "RRULE:FREQ=WEEKLY;COUNT=16",
      "END:VEVENT",
    );
  }
  lines.push("END:VCALENDAR");
  const url = URL.createObjectURL(
    new Blob([lines.join("\r\n")], { type: "text/calendar;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = `${data.value.term || "timetable"}.ics`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

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
      <p class="muted">{{ data.term || "2026-FALL" }} · 按节次与作息时间展示每周安排</p>
    </div>
    <div class="heading-actions no-print">
      <button v-if="data.cells.length" @click="exportIcs">
        <Icon name="download" :size="15" />导出日历 (.ics)
      </button>
      <button @click="printPage">
        <Icon name="printer" :size="15" />打印课表
      </button>
      <button @click="load" :disabled="loading">
        <Icon name="refresh" :size="15" />刷新课表
      </button>
    </div>
  </div>

  <div class="timetable-bar no-print">
    <div class="timetable-toggles">
      <label class="switch">
        <input v-model="showWeekend" type="checkbox" /><span></span>显示周六 / 周日
      </label>
      <label class="switch">
        <input v-model="showCart" type="checkbox" /><span></span>叠加选课单预览 ({{
          cart.items.length
        }})
      </label>
    </div>
    <div class="legend">
      <span><i class="sw solid"></i>已选课程</span>
      <span><i class="sw ghost"></i>选课单意向</span>
      <span><i class="sw conflict"></i>时间冲突</span>
    </div>
  </div>

  <p v-if="error" role="alert" class="notice error">{{ error }}</p>
  <p v-if="loading" class="empty">加载中…</p>
  <div v-else class="panel timetable-wrap">
    <TimetableGrid :cells="gridCells" :weekend="hasWeekend" />
  </div>
  <p v-if="!loading && !error && !gridCells.length" class="notice">
    暂无已选课程，选课成功后课表会显示在这里；你也可以先在选课大厅将课程加入选课单进行预排。
  </p>
</template>
