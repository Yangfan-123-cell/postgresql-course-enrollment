<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";
import { errorMessage } from "../api/client";
import { useEnrollment } from "../stores/enrollment";
import { meetingText, dateText } from "./format";
const store = useEnrollment(),
  error = ref(""),
  message = ref(""),
  loading = ref(false),
  pending = ref<number>(),
  busy = ref(false);
async function load() {
  loading.value = true;
  error.value = "";
  try {
    await store.refresh();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
async function drop() {
  if (!pending.value) return;
  busy.value = true;
  error.value = "";
  try {
    await api.drop(pending.value);
    pending.value = undefined;
    message.value = "退课成功，空余名额由系统处理候补晋升。";
    await load();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">MY LEARNING</p>
      <h1>我的课程</h1>
      <p class="muted">
        已选 {{ store.items.length }} 门课程，共 {{ store.credits }} 学分
      </p>
    </div>
    <button @click="load" :disabled="loading">刷新课程</button>
  </div>
  <p v-if="error" role="alert" class="notice error">{{ error }}</p>
  <p v-if="message" role="status" class="notice success">{{ message }}</p>
  <p v-if="loading" class="empty">正在刷新…</p>
  <div v-else class="panel table-wrap">
    <table>
      <thead>
        <tr>
          <th>课程</th>
          <th>学分</th>
          <th>时间</th>
          <th>选课时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in store.items" :key="item.enrollment_id">
          <td>
            <RouterLink :to="`/sections/${item.section_id}`">{{
              item.course.name
            }}</RouterLink
            ><small>{{ item.course.code }}</small>
          </td>
          <td>{{ item.course.credits }}</td>
          <td>{{ meetingText(item.meetings) }}</td>
          <td>{{ dateText(item.enrolled_at) }}</td>
          <td>
            <button class="danger" @click="pending = item.enrollment_id">
              退课
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!store.items.length && !error" class="empty">
      尚未选课，前往选课大厅探索课程。
    </p>
  </div>
  <div v-if="pending" class="modal-backdrop">
    <section
      role="dialog"
      aria-modal="true"
      aria-labelledby="drop-title"
      class="modal"
    >
      <h2 id="drop-title">确认退课？</h2>
      <p>退课后名额可能立即分配给候补同学。</p>
      <div class="actions">
        <button :disabled="busy" @click="pending = undefined">取消</button
        ><button class="danger" :disabled="busy" @click="drop">
          {{ busy ? "处理中…" : "确认退课" }}
        </button>
      </div>
    </section>
  </div>
</template>
