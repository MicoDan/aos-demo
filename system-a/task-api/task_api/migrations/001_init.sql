CREATE TABLE tasks (
    id          uuid PRIMARY KEY,
    title       text NOT NULL,
    description text,
    status      text NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed')),
    due_date    date,
    created_by  text NOT NULL,
    created_at  timestamptz NOT NULL,
    updated_at  timestamptz NOT NULL,
    version     integer NOT NULL DEFAULT 1
);
CREATE INDEX tasks_owner_created_idx ON tasks (created_by, created_at DESC);

CREATE TABLE outbox_events (
    id           uuid PRIMARY KEY,
    aggregate_id uuid NOT NULL,
    event_type   text NOT NULL,
    payload      jsonb NOT NULL,
    created_at   timestamptz NOT NULL,
    published_at timestamptz
);
CREATE INDEX outbox_unpublished_idx ON outbox_events (created_at) WHERE published_at IS NULL;
