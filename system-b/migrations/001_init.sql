CREATE TABLE tasks_replica (
    id            uuid PRIMARY KEY,
    title         text NOT NULL,
    description   text,
    status        text NOT NULL,
    due_date      date,
    created_by    text NOT NULL,
    created_at    timestamptz NOT NULL,
    updated_at    timestamptz NOT NULL,
    version       integer NOT NULL,
    deleted_at    timestamptz,
    last_event_id uuid NOT NULL,
    synced_at     timestamptz NOT NULL
);
CREATE INDEX tasks_replica_owner_idx ON tasks_replica (created_by) WHERE deleted_at IS NULL;

CREATE TABLE task_activity (
    event_id     uuid PRIMARY KEY,
    task_id      uuid NOT NULL,
    user_id      text NOT NULL,
    event_type   text NOT NULL,
    details      jsonb NOT NULL,
    occurred_at  timestamptz NOT NULL,
    processed_at timestamptz NOT NULL
);
CREATE INDEX task_activity_user_idx ON task_activity (user_id, occurred_at DESC);
