-- ============================================================
-- 高并发选课系统 · 表结构 DDL（PostgreSQL 16）
-- 与 docs/01_技术设计文档.md 第 4 章一致
-- ============================================================

BEGIN;

-- ---------- 枚举 ----------
CREATE TYPE user_role       AS ENUM ('student', 'admin');
CREATE TYPE enrollment_state AS ENUM ('ACTIVE', 'DROPPED');
CREATE TYPE waitlist_state   AS ENUM ('WAITING', 'PROMOTED', 'CANCELLED');
CREATE TYPE audit_action     AS ENUM ('ENROLL', 'DROP', 'PROMOTE', 'DROP_WAITLIST');

-- ---------- 用户 ----------
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    student_no    VARCHAR(20)  NOT NULL,
    name          VARCHAR(50)  NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role          user_role    NOT NULL DEFAULT 'student',
    major         VARCHAR(50)  NOT NULL DEFAULT '',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_users_student_no ON users (student_no);

-- ---------- 课程（元信息） ----------
CREATE TABLE courses (
    id        BIGSERIAL PRIMARY KEY,
    code      VARCHAR(20)  NOT NULL,
    name      VARCHAR(100) NOT NULL,
    credits   SMALLINT     NOT NULL CHECK (credits BETWEEN 1 AND 10),
    dept      VARCHAR(50)  NOT NULL,
    archived  BOOLEAN      NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_courses_code ON courses (code);

-- ---------- 教学班（核心热行） ----------
CREATE TABLE sections (
    id             BIGSERIAL PRIMARY KEY,
    course_id      BIGINT      NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
    term           VARCHAR(20) NOT NULL,
    teacher        VARCHAR(50) NOT NULL,
    capacity       INT         NOT NULL CHECK (capacity >= 1),
    enrolled_count INT         NOT NULL DEFAULT 0,
    version        INT         NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- 最后一道防线：任何路径下的超卖/负计数都会被数据库拒绝
    CONSTRAINT ck_sections_count_bounds
        CHECK (enrolled_count >= 0 AND enrolled_count <= capacity)
);
CREATE UNIQUE INDEX uq_sections_course_term ON sections (course_id, term);

-- ---------- 上课时间（一个教学班可多段） ----------
CREATE TABLE section_meetings (
    id           BIGSERIAL PRIMARY KEY,
    section_id   BIGINT  NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    weekday      SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
    start_period SMALLINT NOT NULL CHECK (start_period BETWEEN 1 AND 12),
    end_period   SMALLINT NOT NULL CHECK (end_period BETWEEN 1 AND 12),
    CONSTRAINT ck_meeting_period_order CHECK (start_period <= end_period)
);
CREATE INDEX idx_meetings_weekday ON section_meetings (weekday, start_period, end_period);
CREATE INDEX idx_meetings_section ON section_meetings (section_id);

-- ---------- 选课记录 ----------
CREATE TABLE enrollments (
    id          BIGSERIAL PRIMARY KEY,
    student_id  BIGINT          NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    section_id  BIGINT          NOT NULL REFERENCES sections(id) ON DELETE RESTRICT,
    status      enrollment_state NOT NULL DEFAULT 'ACTIVE',
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT now(),
    dropped_at  TIMESTAMPTZ
);
-- 同一学生对同一教学班最多一条 ACTIVE 记录（退课后可重选）
CREATE UNIQUE INDEX uq_enrollments_active
    ON enrollments (student_id, section_id)
    WHERE status = 'ACTIVE';
-- 注：idx_enrollments_section_status 故意不在基线中创建，留作第 2 周 EXPLAIN 索引优化对比实验（见 docs/01_技术设计文档.md 4.3 & 9.3）

-- ---------- 候选队列 ----------
CREATE TABLE waitlist_entries (
    id          BIGSERIAL PRIMARY KEY,
    student_id  BIGINT         NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    section_id  BIGINT         NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    position    INT            NOT NULL,
    status      waitlist_state NOT NULL DEFAULT 'WAITING',
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT now(),
    CONSTRAINT uq_waitlist_position UNIQUE (section_id, position)
);
CREATE INDEX idx_waitlist_section_status ON waitlist_entries (section_id, status, position);
-- 同一学生对同一教学班同时只能有一个 WAITING
CREATE UNIQUE INDEX uq_waitlist_active
    ON waitlist_entries (student_id, section_id)
    WHERE status = 'WAITING';

-- ---------- 审计 ----------
CREATE TABLE audit_log (
    id         BIGSERIAL PRIMARY KEY,
    actor_id   BIGINT       NOT NULL,
    section_id BIGINT       NOT NULL,
    action     audit_action NOT NULL,
    before     JSONB,
    after      JSONB,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_section_time ON audit_log (section_id, created_at);

-- ---------- 系统配置（选课开关） ----------
CREATE TABLE system_config (
    key   VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT INTO system_config (key, value) VALUES ('selection_open', 'false');

COMMIT;
