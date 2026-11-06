ALTER TABLE tasks_replica
    ADD COLUMN project text,
    ADD COLUMN attachments jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN parent_task uuid,
    ADD COLUMN priority text NOT NULL DEFAULT 'medium',
    ADD COLUMN assignees jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN lead_institution text,
    ADD COLUMN supporting_institutions_within_gsas jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN supporting_institutions_outside_gsas jsonb NOT NULL DEFAULT '[]',
    ADD COLUMN date_issued date,
    ADD COLUMN labels jsonb NOT NULL DEFAULT '[]';
UPDATE tasks_replica SET date_issued = (created_at AT TIME ZONE 'UTC')::date;
ALTER TABLE tasks_replica ALTER COLUMN date_issued SET NOT NULL;
