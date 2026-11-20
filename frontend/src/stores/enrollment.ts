import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { api } from "../api";
import type { Enrollment, Waitlist } from "../api/types";
export const useEnrollment = defineStore("enrollment", () => {
  const items = ref<Enrollment[]>([]);
  const waiting = ref<Waitlist[]>([]);
  const busy = ref<number[]>([]);
  const credits = computed(() =>
    items.value.reduce((sum, e) => sum + e.course.credits, 0),
  );
  async function refresh() {
    const [enrolled, waitlist] = await Promise.all([
      api.enrollments(),
      api.waitlist(),
    ]);
    items.value = enrolled.items;
    waiting.value = waitlist.items;
  }
  async function enroll(id: number, allow: boolean) {
    if (busy.value.includes(id)) throw new Error("该课程正在提交，请稍候");
    busy.value = [...busy.value, id];
    try {
      return await api.enroll(id, allow);
    } finally {
      busy.value = busy.value.filter((value) => value !== id);
    }
  }
  function reset() {
    items.value = [];
    waiting.value = [];
    busy.value = [];
  }
  return { items, waiting, busy, credits, refresh, enroll, reset };
});
