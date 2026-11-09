-- Deleted tasks are now physically removed from tasks_replica (matching Smart Admin).
-- Remove the soft-deleted rows that earlier versions left behind.
DELETE FROM tasks_replica WHERE deleted_at IS NOT NULL;
