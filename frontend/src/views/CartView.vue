<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { errorMessage } from "../api/client";
import { useCart, type CartItem } from "../stores/cart";
import { useEnrollment } from "../stores/enrollment";
import Icon from "./widgets/Icon.vue";
import TimetableGrid from "./widgets/TimetableGrid.vue";
import type { GridCell } from "./widgets/grid";
import { CREDIT_RULE } from "./config";
import { colorOf, conflictNames, meetingText } from "./format";

const cart = useCart(),
  store = useEnrollment(),
  submitting = ref(false),
  error = ref(""),
  message = ref("");

const enrolledIds = computed(() => new Set(store.items.map((e) => e.section_id)));
const waitingIds = computed(() => new Set(store.waiting.map((w) => w.section_id)));
const enrolledRefs = computed(() =>
  store.items.map((e) => ({
    id: e.section_id,
    name: e.course.name,
    meetings: e.meetings,
  })),
);
const cartRefs = computed(() =>
  cart.items.map((c) => ({
    id: c.section_id,
    name: c.name,
    meetings: c.meetings,
  })),
);

function enrolledConflicts(item: CartItem) {
  return conflictNames(item.meetings, enrolledRefs.value, item.section_id);
}
function internalConflicts(item: CartItem) {
  return conflictNames(item.meetings, cartRefs.value, item.section_id);
}
function isDone(id: number) {
  return enrolledIds.value.has(id) || waitingIds.value.has(id);
}

const previewCells = computed<GridCell[]>(() => {
  const real: GridCell[] = store.items.flatMap((e) =>
    e.meetings.map((m, i) => ({
      key: `e-${e.section_id}-${i}`,
      weekday: m.weekday,
      start_period: m.start_period,
      end_period: m.end_period,
      title: e.course.name,
      sub: `${m.start_period}–${m.end_period} 节 · 已选`,
      color: colorOf(e.section_id),
      to: `/sections/${e.section_id}`,
    })),
  );
  const ghost: GridCell[] = cart.items
    .filter((c) => !enrolledIds.value.has(c.section_id))
    .flatMap((c) =>
      c.meetings.map((m, i) => {
        const hasConflict =
          enrolledConflicts(c).length > 0 || internalConflicts(c).length > 0;
        return {
          key: `c-${c.section_id}-${i}`,
          weekday: m.weekday,
          start_period: m.start_period,
          end_period: m.end_period,
          title: c.name,
          sub: hasConflict ? "时间冲突" : `${m.start_period}–${m.end_period} 节 · 意向`,
          color: hasConflict ? "#c43e3b" : colorOf(c.section_id),
          to: `/sections/${c.section_id}`,
          ghost: true,
          conflict: hasConflict,
        };
      }),
    );
  return [...real, ...ghost];
});

const hasWeekend = computed(() => previewCells.value.some((c) => c.weekday > 5));
const projectedCredits = computed(
  () =>
    store.credits +
    cart.items
      .filter((c) => !enrolledIds.value.has(c.section_id))
      .reduce((sum, c) => sum + c.credits, 0),
);
const submittable = computed(() =>
  cart.items.filter(
    (c) => !isDone(c.section_id) && enrolledConflicts(c).length === 0,
  ),
);

async function submitOne(item: CartItem) {
  error.value = "";
  message.value = "";
  try {
    const res = await store.enroll(item.section_id, true);
    await store.refresh();
    if (res.status === "ENROLLED") {
      message.value = `已选中《${item.name}》`;
      cart.remove(item.section_id);
    } else {
      message.value = `已加入《${item.name}》候补队列，当前第 ${res.waitlist.position} 位`;
    }
  } catch (e) {
    error.value = errorMessage(e);
  }
}

async function submitAll() {
  if (!submittable.value.length) return;
  submitting.value = true;
  error.value = "";
  message.value = "";
  let ok = 0;
  let wait = 0;
  const failed: string[] = [];
  for (const item of [...submittable.value]) {
    try {
      const res = await store.enroll(item.section_id, true);
      if (res.status === "ENROLLED") {
        ok++;
        cart.remove(item.section_id);
      } else {
        wait++;
      }
    } catch (e) {
      failed.push(`《${item.name}》：${errorMessage(e)}`);
    }
  }
  try {
    await store.refresh();
  } catch {
    // 忽略刷新异常，保留上方提交结果
  }
  submitting.value = false;
  if (ok || wait) {
    message.value = `批量提交完成：${ok} 门选课成功，${wait} 门进入候补。`;
  }
  if (failed.length) {
    error.value = failed.join("；");
  }
}

onMounted(async () => {
  try {
    await store.refresh();
  } catch (e) {
    error.value = errorMessage(e);
  }
});
</script>
<template>
  <div class="page-heading">
    <div>
      <p class="eyebrow">COURSE PLANNER</p>
      <h1>选课单</h1>
      <p class="muted">
        收藏意向课程、检查时间冲突并预览课表，选课单保存在本机浏览器，不占用实际名额。
      </p>
    </div>
    <div class="heading-actions">
      <RouterLink to="/hall" class="btn">
        <Icon name="grid" :size="16" />继续挑课
      </RouterLink>
      <button
        class="primary"
        :disabled="submitting || !submittable.length"
        @click="submitAll"
      >
        <Icon name="send" :size="16" />
        {{ submitting ? "批量提交中…" : `一键提交 (${submittable.length})` }}
      </button>
    </div>
  </div>

  <div class="stat-strip">
    <div class="stat-tile">
      <span>选课单课程</span>
      <strong>{{ cart.items.length }} <small>门</small></strong>
    </div>
    <div class="stat-tile">
      <span>意向学分</span>
      <strong>{{ cart.credits }} <small>学分</small></strong>
    </div>
    <div class="stat-tile">
      <span>预计总学分</span>
      <strong>{{ projectedCredits }} <small>/ {{ CREDIT_RULE.max }}</small></strong>
    </div>
    <div class="stat-tile">
      <span>当前已选</span>
      <strong>{{ store.items.length }} <small>门 · {{ store.credits }} 学分</small></strong>
    </div>
  </div>

  <p v-if="message" role="status" class="notice success">
    <Icon name="check-circle" />{{ message }}
  </p>
  <p v-if="error" role="alert" class="notice error">{{ error }}</p>

  <div v-if="!cart.items.length" class="panel empty-state">
    <Icon name="bookmark" :size="36" />
    <p>选课单还是空的，去选课大厅点击课程右上角的星标即可加入规划。</p>
    <RouterLink to="/hall" class="btn primary">前往选课大厅</RouterLink>
  </div>

  <div v-else class="split-layout">
    <section class="cart-list">
      <article
        v-for="item in cart.items"
        :key="item.section_id"
        class="panel cart-card"
        :class="{
          'is-conflict': enrolledConflicts(item).length || internalConflicts(item).length,
        }"
      >
        <div class="cart-main">
          <div class="cart-head">
            <span class="course-code">{{ item.code }}</span>
            <span class="tag">{{ item.dept }}</span>
            <span class="tag">{{ item.credits }} 学分</span>
            <span v-if="enrolledIds.has(item.section_id)" class="badge green">已选中</span>
            <span v-else-if="waitingIds.has(item.section_id)" class="badge amber">候补中</span>
          </div>
          <RouterLink :to="`/sections/${item.section_id}`" class="course-title">
            {{ item.name }}
          </RouterLink>
          <p class="muted small">
            {{ item.teacher }} · {{ meetingText(item.meetings) }}
          </p>
          <p v-if="enrolledConflicts(item).length" class="conflict-hint">
            <Icon name="alert" :size="15" />与已选课程《{{
              enrolledConflicts(item).join("》《")
            }}》时间冲突
          </p>
          <p v-else-if="internalConflicts(item).length" class="conflict-hint warn">
            <Icon name="alert" :size="15" />与选课单中《{{
              internalConflicts(item).join("》《")
            }}》时间重叠，请择一提交
          </p>
        </div>
        <div class="cart-actions">
          <button
            class="primary sm"
            :disabled="
              submitting ||
              store.busy.includes(item.section_id) ||
              isDone(item.section_id) ||
              enrolledConflicts(item).length > 0
            "
            @click="submitOne(item)"
          >
            {{
              store.busy.includes(item.section_id)
                ? "提交中…"
                : enrolledIds.has(item.section_id)
                  ? "已选"
                  : waitingIds.has(item.section_id)
                    ? "候补中"
                    : "提交选课"
            }}
          </button>
          <button
            class="sm danger"
            :disabled="submitting"
            @click="cart.remove(item.section_id)"
          >
            移出
          </button>
        </div>
      </article>
    </section>

    <section class="panel preview-panel">
      <div class="panel-head">
        <div>
          <h2>课表叠合预览</h2>
          <p class="muted small">实线为已选课程，虚线为选课单意向课程</p>
        </div>
        <RouterLink to="/timetable" class="small">完整课表 →</RouterLink>
      </div>
      <div class="timetable-wrap compact">
        <TimetableGrid :cells="previewCells" :weekend="hasWeekend" :highlight-today="false" />
      </div>
    </section>
  </div>
</template>
