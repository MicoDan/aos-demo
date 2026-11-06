-- Deleted tasks are now physically removed from tasks_replica (matching System A).
-- Remove the soft-deleted rows that earlier versions left behind.
DELETE FROM tasks_replica WHERE deleted_at IS NOT NULL;
