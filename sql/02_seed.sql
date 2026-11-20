-- ============================================================
-- 种子数据：1 名管理员 + 2000 名学生 + 200 门课 + 200 个教学班
-- 用法：psql -f sql/02_seed.sql（在空库、已执行 sql/01_schema.sql 后）
-- 默认测试密码明文：Passw0rd!（下方为真实 bcrypt cost=12 哈希）
-- ============================================================

BEGIN;

-- 管理员（密码明文 Passw0rd!）
INSERT INTO users (student_no, name, password_hash, role, major) VALUES
('admin', '教务管理员',
 '$2b$12$BfOVw5Q5EwcZWhGIpTQdouFfKizbD1A/VkU619cKPB1zJ0xKGjMDK', 'admin', '教务处');

-- 学生：S0001 ~ S2000（密码明文 Passw0rd!）
INSERT INTO users (student_no, name, password_hash, major)
SELECT 'S' || LPAD(g::text, 4, '0'),
       '学生' || g,
       '$2b$12$BfOVw5Q5EwcZWhGIpTQdouFfKizbD1A/VkU619cKPB1zJ0xKGjMDK',
       (ARRAY['计算机','软件工程','数学','物理','电子'])[1 + (g % 5)]
FROM generate_series(1, 2000) AS g;

-- 200 门课程（20 个基础科目 × 10 个班次方向，保持与 uq_sections_course_term 唯一约束一致）
INSERT INTO courses (code, name, credits, dept)
SELECT 'CS' || LPAD((100 + g)::text, 3, '0'),
       (ARRAY['数据结构','操作系统','计算机网络','编译原理','数据库系统',
              '机器学习','并发编程','算法设计','离散数学','线性代数',
              '概率论','大学物理','电路分析','软件工程','信息安全',
              '人工智能导论','数字逻辑','计算机图形学','分布式系统','程序语言'])[1 + ((g - 1) % 20)]
       || '（' || (1 + ((g - 1) / 20)) || '班）',
       (ARRAY[4,4,4,3,4,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3])[1 + ((g - 1) % 20)],
       (ARRAY['计算机','计算机','计算机','计算机','计算机','计算机','计算机','计算机','数学','数学','数学','物理','电子','软件工程','计算机','计算机','电子','计算机','计算机','计算机'])[1 + ((g - 1) % 20)]
FROM generate_series(1, 200) AS g;

-- 200 个教学班：每门课程在 2026-FALL 开设 1 个班，容量 30~120（其中 id=1 容量为 60，匹配 k6_grab.js 压测场景）
INSERT INTO sections (course_id, term, teacher, capacity)
SELECT c.id,
       '2026-FALL',
       (ARRAY['李四','王五','赵六','陈七','周八'])[1 + (c.id % 5)],
       30 + 10 * ((c.id + 2) % 10)
FROM courses c;

-- 每个教学班 1~2 段上课时间（周几与节次按 ID 伪随机，保证节次在 1~12 且同班内不重叠）
INSERT INTO section_meetings (section_id, weekday, start_period, end_period)
SELECT s.id,
       1 + (s.id % 5)::int,                    -- 周一~周五
       1 + (s.id % 3)::int * 2,                -- 1/3/5 节起
       2 + (s.id % 3)::int * 2                 -- 2/4/6 节止
FROM sections s;

INSERT INTO section_meetings (section_id, weekday, start_period, end_period)
SELECT s.id,
       1 + ((s.id + 2) % 5)::int,              -- 与第一段错开周几
       7 + (s.id % 2)::int * 2,                -- 7/9 节起
       8 + (s.id % 2)::int * 2                 -- 8/10 节止
FROM sections s
WHERE s.id % 2 = 0;

COMMIT;
