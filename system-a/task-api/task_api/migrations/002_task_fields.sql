-- Standard per-task fields. Everything lives on the task row itself (lists as JSONB arrays);
-- no related tables or foreign keys.
ALTER TABLE tasks
    ADD COLUMN project text,
    ADD COLUMN attachments jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN parent_task uuid,
    ADD COLUMN priority text NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    ADD COLUMN assignees jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN lead_institution text,
    ADD COLUMN supporting_institutions_within_gsas jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN supporting_institutions_outside_gsas jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN date_issued date,
    ADD COLUMN labels jsonb NOT NULL DEFAULT '[]';
UPDATE tasks SET date_issued = (created_at AT TIME ZONE 'UTC')::date;
ALTER TABLE tasks ALTER COLUMN date_issued SET NOT NULL;
