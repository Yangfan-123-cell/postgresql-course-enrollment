<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import { errorMessage } from "../api/client";
import { useEnrollment } from "../stores/enrollment";
import Icon from "./widgets/Icon.vue";
import { CREDIT_RULE } from "./config";
import { dateText, downloadCsv, meetingText, periodCount } from "./format";

const store = useEnrollment(),
  error = ref(""),
  message = ref(""),
  loading = ref(false),
  pending = ref<number>(),
  busy = ref(false);

const totalPeriods = computed(() =>
  store.items.reduce((sum, e) => sum + periodCount(e.meetings), 0),
);
const pendingCourse = computed(() =>
  store.items.find((e) => e.enrollment_id === pending.value),
);

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
function exportList() {
  downloadCsv("my_courses.csv", [
    ["课程号", "课程名称", "院系", "学分", "上课时间", "选课时间"],
    ...store.items.map((e) => [
      e.course.code,
      e.course.name,
      e.course.dept,
      e.course.credits,
      meetingText(e.meetings),
      dateText(e.enrolled_at),
    ]),
  ]);
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
    <div class="heading-actions">
      <button v-if="store.items.length" @click="exportList">
        <Icon name="download" :size="15" />导出课程清单
      </button>
      <button @click="load" :disabled="loading">
        <Icon name="refresh" :size="15" />刷新课程
      </button>
    </div>
  </div>

  <div class="stat-strip">
    <div class="stat-tile">
      <span>已选门数</span>
      <strong>{{ store.items.length }} <small>门</small></strong>
    </div>
    <div class="stat-tile">
      <span>已选学分</span>
      <strong>{{ store.credits }} <small>/ {{ CREDIT_RULE.max }}</small></strong>
    </div>
    <div class="stat-tile">
      <span>每周学时</span>
      <strong>{{ totalPeriods }} <small>节</small></strong>
    </div>
    <div class="stat-tile">
      <span>候补中</span>
      <strong>{{ store.waiting.length }} <small>门</small></strong>
    </div>
  </div>

  <p v-if="error" role="alert" class="notice error">{{ error }}</p>
  <p v-if="message" role="status" class="notice success">
    <Icon name="check-circle" />{{ message }}
  </p>
  <p v-if="loading" class="empty">正在刷新…</p>
  <div v-else class="panel table-wrap">
    <table>
      <thead>
        <tr>
          <th>课程</th>
          <th>院系</th>
          <th>学分</th>
          <th>上课时间</th>
          <th>选课时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in store.items" :key="item.enrollment_id">
          <td>
            <RouterLink :to="`/sections/${item.section_id}`" class="strong-link">{{
              item.course.name
            }}</RouterLink>
            <small>{{ item.course.code }} · 教学班 #{{ item.section_id }}</small>
          </td>
          <td>
            <span class="tag">{{ item.course.dept }}</span>
          </td>
          <td>{{ item.course.credits }} 学分</td>
          <td>{{ meetingText(item.meetings) }}</td>
          <td>{{ dateText(item.enrolled_at) }}</td>
          <td>
            <button class="danger sm" @click="pending = item.enrollment_id">
              退课
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!store.items.length && !error" class="empty-state">
      <Icon name="book" :size="34" />
      <p>尚未选课，前往选课大厅探索课程。</p>
      <RouterLink to="/hall" class="btn primary">浏览课程</RouterLink>
    </div>
  </div>
  <div v-if="pending" class="modal-backdrop">
    <section
      role="dialog"
      aria-modal="true"
      aria-labelledby="drop-title"
      class="modal"
    >
      <h2 id="drop-title">确认退课？</h2>
      <p>
        即将退出《{{ pendingCourse?.course.name }}》。退课后名额可能立即分配给候补同学。
      </p>
      <div class="actions end">
        <button :disabled="busy" @click="pending = undefined">取消</button>
        <button class="danger" :disabled="busy" @click="drop">
          {{ busy ? "处理中…" : "确认退课" }}
        </button>
      </div>
    </section>
  </div>
</template>
