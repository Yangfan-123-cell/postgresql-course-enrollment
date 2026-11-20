-- ============================================================
-- 压测轮次重置脚本：清空选课/候补/审计记录并归零计数，保留用户与课程数据
-- 用法：psql -f sql/03_reset.sql
-- ============================================================

BEGIN;

TRUNCATE TABLE enrollments, waitlist_entries, audit_log RESTART IDENTITY;

UPDATE sections
   SET enrolled_count = 0,
       version        = 0;

INSERT INTO system_config (key, value)
VALUES ('selection_open', 'false')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

COMMIT;
