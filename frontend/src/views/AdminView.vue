<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api } from "../api";
import { errorMessage } from "../api/client";
import type { Course, Section, Roster, Meeting } from "../api/types";
import { meetingText, dateText } from "./format";
const tab = ref<"courses" | "sections">("courses"),
  courses = ref<Course[]>([]),
  sections = ref<Section[]>([]),
  total = ref(0),
  page = ref(1),
  loading = ref(false),
  busy = ref(false),
  error = ref(""),
  message = ref("");
const keyword = ref(""),
  term = ref("2026-FALL"),
  archived = ref(false),
  editing = ref<"course" | "section">(),
  editId = ref<number>(),
  rosterId = ref<number>(),
  roster = ref<Roster[]>([]),
  rosterPage = ref(1),
  rosterTotal = ref(0),
  selectionOpen = ref<boolean>();
const courseForm = reactive({
  code: "",
  name: "",
  credits: 3,
  dept_id: 1,
  archived: false,
});
const sectionForm = reactive({
  course_id: 1,
  term: "2026-FALL",
  teacher: "",
  capacity: 60,
  meetings: [{ weekday: 1, start_period: 1, end_period: 2 }] as Meeting[],
});
async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (tab.value === "courses") {
      const data = await api.courses({
        keyword: keyword.value,
        archived: archived.value,
        page: page.value,
        size: 20,
      });
      courses.value = data.items;
      total.value = data.total;
    } else {
      const data = await api.adminSections({
        term: term.value,
        page: page.value,
        size: 20,
      });
      sections.value = data.items;
      total.value = data.total;
      selectionOpen.value = data.items[0]?.selection_open;
    }
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
function switchTab(value: "courses" | "sections") {
  tab.value = value;
  page.value = 1;
  void load();
}
function editCourse(course?: Course) {
  editId.value = course?.id;
  Object.assign(courseForm, {
    code: course?.code || "",
    name: course?.name || "",
    credits: course?.credits || 3,
    dept_id: 1,
    archived: course?.archived || false,
  });
  editing.value = "course";
}
function editSection(section?: Section) {
  editId.value = section?.id;
  Object.assign(sectionForm, {
    course_id: section?.course.id || 1,
    term: section?.term || term.value,
    teacher: section?.teacher || "",
    capacity: section?.capacity || 60,
    meetings: section
      ? section.meetings.map((m) => ({ ...m }))
      : [{ weekday: 1, start_period: 1, end_period: 2 }],
  });
  editing.value = "section";
}
async function save() {
  error.value = "";
  busy.value = true;
  try {
    if (editing.value === "course") {
      // 契约没有返回 dept_id，编辑时不猜测院系 ID，保留原院系。
      const { dept_id, ...fields } = courseForm;
      await api.saveCourse(
        editId.value ? fields : { ...fields, dept_id },
        editId.value,
      );
    } else {
      const meetings = sectionForm.meetings;
      if (
        !meetings.length ||
        meetings.some((m) => m.start_period > m.end_period)
      )
        throw new Error("请填写有效的上课时间段");
      if (
        meetings.some((a, i) =>
          meetings.some(
            (b, j) =>
              j > i &&
              a.weekday === b.weekday &&
              a.start_period <= b.end_period &&
              b.start_period <= a.end_period,
          ),
        )
      )
        throw new Error("同一教学班的上课时间段不能重叠");
      await api.saveSection(
        editId.value
          ? {
              teacher: sectionForm.teacher,
              capacity: sectionForm.capacity,
              meetings,
            }
          : { ...sectionForm },
        editId.value,
      );
    }
    editing.value = undefined;
    message.value = "保存成功。";
    await load();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    busy.value = false;
  }
}
async function setSelection(open: boolean) {
  busy.value = true;
  error.value = "";
  try {
    const result = await api.selection(open);
    selectionOpen.value = result.selection_open;
    message.value = `选课阶段已${result.selection_open ? "开放" : "关闭"}。`;
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    busy.value = false;
  }
}
async function showRoster(id: number, nextPage = 1) {
  error.value = "";
  busy.value = true;
  try {
    const data = await api.roster(id, nextPage);
    roster.value = data.items;
    rosterTotal.value = data.total;
    rosterPage.value = nextPage;
    rosterId.value = id;
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    busy.value = false;
  }
}
async function exportCsv(id: number) {
  busy.value = true;
  error.value = "";
  try {
    await api.exportRoster(id);
    message.value = "名单已导出。";
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
      <p class="eyebrow">ACADEMIC AFFAIRS</p>
      <h1>教务管理</h1>
      <p class="muted">维护课程与教学班，管理选课开放阶段。</p>
    </div>
    <div class="actions">
      <span class="badge">{{
        selectionOpen === undefined
          ? "开放状态待查询"
          : selectionOpen
            ? "选课已开放"
            : "选课已关闭"
      }}</span
      ><button :disabled="busy" @click="setSelection(true)">开放选课</button
      ><button class="danger" :disabled="busy" @click="setSelection(false)">
        关闭选课
      </button>
    </div>
  </div>
  <p v-if="error" role="alert" class="notice error">{{ error }}</p>
  <p v-if="message" role="status" class="notice success">{{ message }}</p>
  <div class="tabs">
    <button
      :class="{ active: tab === 'courses' }"
      @click="switchTab('courses')"
    >
      课程管理</button
    ><button
      :class="{ active: tab === 'sections' }"
      @click="switchTab('sections')"
    >
      教学班管理
    </button>
  </div>
  <form
    class="filters"
    @submit.prevent="
      page = 1;
      load();
    "
  >
    <template v-if="tab === 'courses'"
      ><input
        v-model="keyword"
        aria-label="课程关键词"
        placeholder="课程名 / 课程号"
      /><label class="inline"
        ><input v-model="archived" type="checkbox" />已归档课程</label
      ></template
    ><input
      v-else
      v-model="term"
      aria-label="学期"
      required
      placeholder="学期"
    /><button :disabled="loading">查询</button
    ><button
      class="primary"
      type="button"
      @click="tab === 'courses' ? editCourse() : editSection()"
    >
      {{ tab === "courses" ? "新建课程" : "新建教学班" }}
    </button>
  </form>
  <p v-if="loading" class="empty">加载中…</p>
  <div v-else class="panel table-wrap">
    <table v-if="tab === 'courses'">
      <thead>
        <tr>
          <th>课程号</th>
          <th>名称</th>
          <th>院系</th>
          <th>学分</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in courses" :key="c.id">
          <td>
            {{ c.code }}<small>ID {{ c.id }}</small>
          </td>
          <td>{{ c.name }}</td>
          <td>{{ c.dept }}</td>
          <td>{{ c.credits }}</td>
          <td>{{ c.archived ? "已归档" : "正常" }}</td>
          <td><button @click="editCourse(c)">编辑</button></td>
        </tr>
      </tbody>
    </table>
    <table v-else>
      <thead>
        <tr>
          <th>课程 / ID</th>
          <th>教师</th>
          <th>时间</th>
          <th>人数</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in sections" :key="s.id">
          <td>
            {{ s.course.name }}<small>教学班 #{{ s.id }}</small>
          </td>
          <td>{{ s.teacher }}</td>
          <td>{{ meetingText(s.meetings) }}</td>
          <td>{{ s.enrolled_count }} / {{ s.capacity }}</td>
          <td class="actions">
            <button @click="editSection(s)">编辑</button
            ><button :disabled="busy" @click="showRoster(s.id)">名单</button
            ><button :disabled="busy" @click="exportCsv(s.id)">CSV</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!total && !error" class="empty">暂无数据</p>
  </div>
  <div class="pagination">
    <button
      :disabled="page <= 1 || loading"
      @click="
        page--;
        load();
      "
    >
      上一页</button
    ><span>第 {{ page }} 页 / 共 {{ total }} 条</span
    ><button
      :disabled="page * 20 >= total || loading"
      @click="
        page++;
        load();
      "
    >
      下一页
    </button>
  </div>
  <div v-if="editing" class="modal-backdrop">
    <form
      class="modal wide"
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-title"
      @submit.prevent="save"
    >
      <h2 id="edit-title">
        {{ editId ? "编辑" : "新建"
        }}{{ editing === "course" ? "课程" : "教学班" }}
      </h2>
      <p v-if="error" role="alert" class="notice error">{{ error }}</p>
      <template v-if="editing === 'course'"
        ><label
          >课程号<input
            v-model="courseForm.code"
            required
            maxlength="20" /></label
        ><label
          >课程名<input v-model="courseForm.name" required maxlength="100"
        /></label>
        <div class="form-row">
          <label
            >学分<input
              v-model.number="courseForm.credits"
              type="number"
              min="1"
              max="10"
              required /></label
          ><label v-if="!editId"
            >院系 ID<input
              v-model.number="courseForm.dept_id"
              type="number"
              min="1"
              required
          /></label>
        </div>
        <label v-if="editId" class="inline"
          ><input
            v-model="courseForm.archived"
            type="checkbox"
          />归档课程</label
        ></template
      ><template v-else
        ><div v-if="!editId" class="form-row">
          <label
            >课程 ID<input
              v-model.number="sectionForm.course_id"
              type="number"
              min="1"
              required /></label
          ><label>学期<input v-model="sectionForm.term" required /></label>
        </div>
        <div class="form-row">
          <label
            >授课教师<input
              v-model="sectionForm.teacher"
              required
              maxlength="50" /></label
          ><label
            >容量<input
              v-model.number="sectionForm.capacity"
              type="number"
              min="1"
              required
          /></label>
        </div>
        <h3>上课时间</h3>
        <div
          v-for="(m, i) in sectionForm.meetings"
          :key="i"
          class="meeting-row"
        >
          <label
            >周几<input
              v-model.number="m.weekday"
              type="number"
              min="1"
              max="7"
              required /></label
          ><label
            >开始节次<input
              v-model.number="m.start_period"
              type="number"
              min="1"
              max="12"
              required /></label
          ><label
            >结束节次<input
              v-model.number="m.end_period"
              type="number"
              min="1"
              max="12"
              required /></label
          ><button
            type="button"
            :disabled="sectionForm.meetings.length === 1"
            @click="sectionForm.meetings.splice(i, 1)"
          >
            移除
          </button>
        </div>
        <button
          type="button"
          @click="
            sectionForm.meetings.push({
              weekday: 1,
              start_period: 1,
              end_period: 2,
            })
          "
        >
          添加时间段
        </button></template
      >
      <div class="actions end">
        <button type="button" :disabled="busy" @click="editing = undefined">
          取消</button
        ><button class="primary" :disabled="busy">
          {{ busy ? "保存中…" : "保存" }}
        </button>
      </div>
    </form>
  </div>
  <div v-if="rosterId" class="modal-backdrop">
    <section
      class="modal wide"
      role="dialog"
      aria-modal="true"
      aria-labelledby="roster-title"
    >
      <h2 id="roster-title">教学班 #{{ rosterId }} 名单</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>学号</th>
              <th>姓名</th>
              <th>选课时间</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in roster" :key="r.student_no">
              <td>{{ r.student_no }}</td>
              <td>{{ r.name }}</td>
              <td>{{ dateText(r.enrolled_at) }}</td>
              <td>{{ r.source === "PROMOTED" ? "候补晋升" : "直接选课" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button
          :disabled="rosterPage <= 1 || busy"
          @click="showRoster(rosterId!, rosterPage - 1)"
        >
          上一页</button
        ><span>{{ rosterPage }} / 共 {{ rosterTotal }} 人</span
        ><button
          :disabled="rosterPage * 20 >= rosterTotal || busy"
          @click="showRoster(rosterId!, rosterPage + 1)"
        >
          下一页
        </button>
      </div>
      <div class="actions end">
        <button :disabled="busy" @click="exportCsv(rosterId!)">导出 CSV</button
        ><button @click="rosterId = undefined">关闭</button>
      </div>
    </section>
  </div>
</template>
