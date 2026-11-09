#!/usr/bin/env python3
"""Compare Smart Admin (tasks) with My Assist (tasks_replica) for all live tasks.

This is a TEST TOOL: it is the only thing allowed to connect to both databases.
Exit code 0 only if ids, titles, statuses and versions all agree.
"""
import os
import sys

from sqlalchemy import create_engine, text


COLS = ("title, status, version, description, project, attachments, parent_task, priority, assignees, "
        "lead_institution, supporting_institutions_within_gsas, supporting_institutions_outside_gsas, "
        "date_issued, due_date, labels")


def norm(v):
    return v if v is None or isinstance(v, (int, str, list, dict)) else str(v)


def fetch(url, sql):
    with create_engine(url).connect() as c:
        return {str(r.id): tuple(norm(x) for x in r[1:]) for r in c.execute(text(sql))}


def main() -> int:
    a = fetch(os.environ["DB_A_URL"], f"SELECT id, {COLS} FROM tasks")
    b = fetch(os.environ["DB_B_URL"],
              f"SELECT id, {COLS} FROM tasks_replica WHERE deleted_at IS NULL")
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    diff = sorted(i for i in set(a) & set(b) if a[i] != b[i])
    print(f"Smart Admin live tasks: {len(a)}   My Assist live tasks: {len(b)}")
    for i in only_a:
        print(f"  MISSING in B: {i} {a[i]}")
    for i in only_b:
        print(f"  EXTRA in B:   {i} {b[i]}")
    for i in diff:
        print(f"  MISMATCH {i}: A={a[i]} B={b[i]}")
    if only_a or only_b or diff:
        print("RESULT: DISAGREE")
        return 1
    print("RESULT: Smart Admin and My Assist agree (ids, version and all 14 task fields)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
