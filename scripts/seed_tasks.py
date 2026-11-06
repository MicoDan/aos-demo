#!/usr/bin/env python3
"""Seed ~30 varied tasks through the Task API (so they flow A -> outbox -> Kafka -> B).

Auth: uses the dedicated public client `task-seeder` (direct-grant enabled, dev only)
to get a token for the demo user from Keycloak's token endpoint.

Re-runnable: every seeded task has a stable title ("[seed] ..."). Titles that already
exist for the demo user are skipped, so repeated runs do not duplicate data.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

TASK_API = os.environ.get("TASK_API_URL", "http://localhost:8001")
TOKEN_URL = os.environ.get(
    "KEYCLOAK_TOKEN_URL", "http://localhost:8080/realms/taskapp/protocol/openid-connect/token")

# (title, description, final status, due offset in days or None, extra edit?)
SEEDS = [
    ("Write quarterly report", "Summarise Q3 results", "completed", -10, True),
    ("Review pull requests", "Clear the review backlog", "in_progress", 1, False),
    ("Plan team offsite", "Venue, budget, agenda", "pending", 21, False),
    ("Fix login redirect bug", "Users bounce back to /login", "completed", -3, False),
    ("Update dependencies", "Bump patch versions", "in_progress", 4, False),
    ("Design onboarding flow", None, "pending", 14, False),
    ("Migrate database to v16", "Rehearse on staging first", "in_progress", 9, True),
    ("Respond to customer feedback", "Triage the inbox", "completed", -1, False),
    ("Prepare demo for Friday", "Slides + live walkthrough", "pending", 3, False),
    ("Refactor billing module", "Split into smaller services", "pending", 30, False),
    ("Set up monitoring alerts", "Latency + error-rate SLOs", "in_progress", 6, False),
    ("Write onboarding docs", None, "completed", -7, False),
    ("Audit access permissions", "Quarterly review", "pending", 12, False),
    ("Optimise slow queries", "Look at top 10 by total time", "in_progress", 2, True),
    ("Book flights for conference", None, "completed", -14, False),
    ("Renew TLS certificates", "Expire next month", "pending", 25, False),
    ("Clean up feature flags", "Remove 6 stale flags", "pending", None, False),
    ("Interview candidate - backend", "Panel at 14:00", "completed", -2, False),
    ("Draft Kafka runbook", "Outage + replay procedures", "in_progress", 5, False),
    ("Backup restore drill", "Restore prod snapshot to scratch", "pending", 18, False),
    ("Improve test coverage", "Target 80%", "in_progress", 10, False),
    ("Archive old projects", None, "completed", -20, False),
    ("Evaluate search options", "Compare Postgres FTS vs. a search engine", "pending", 40, False),
    ("Accessibility review", "Run axe on main flows", "pending", 8, False),
    ("Update privacy policy", "Legal sign-off needed", "in_progress", 15, False),
    ("Create release notes", None, "completed", -5, False),
    ("Load-test the API", "k6, 200 rps for 10 min", "pending", 11, False),
    ("Rotate API keys", "Quarterly rotation", "completed", -9, False),
    ("Mentor session with intern", "Weekly 1:1", "in_progress", 0, False),
    ("Plan holiday coverage", None, "pending", 45, False),
]


PROJECTS = ["Accreditation 2026", "Digital Campus", "Research Grants"]
INSTITUTIONS = ["Institution A", "Institution B", "Institution C"]
EXTERNAL = ["External Partner X", "External Partner Y"]
PEOPLE = ["amina", "jean", "grace", "luc"]
LABELS = ["urgent", "finance", "docs", "ops", "q4"]
PRIORITIES = ["low", "medium", "high", "critical"]


def extra_fields(i, due, today):
    """Deterministic variety for the 14 standard task fields."""
    return {
        "project": PROJECTS[i % 3],
        "priority": PRIORITIES[i % 4],
        "assignees": PEOPLE[: 1 + i % 3],
        "lead_institution": INSTITUTIONS[i % 3],
        "supporting_institutions_within_gsas": INSTITUTIONS[: i % 3],
        "supporting_institutions_outside_gsas": EXTERNAL[: i % 3] if i % 2 else [],
        "labels": [LABELS[i % 5], LABELS[(i + 2) % 5]],
        "attachments": [{"name": f"brief-{i + 1}.pdf", "url": f"https://example.org/files/brief-{i + 1}.pdf"}] if i % 3 == 0 else [],
        "date_issued": (today - timedelta(days=i % 20 + 1)).isoformat(),
    }


def call(method, url, token=None, body=None, form=None):
    data = None
    headers = {}
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url} -> HTTP {e.code}: {e.read().decode()[:300]}")


def main():
    token = call("POST", TOKEN_URL, form={
        "client_id": "task-seeder", "grant_type": "password",
        "username": "demo", "password": "demo1234"})["access_token"]

    existing, offset = set(), 0
    while True:
        page = call("GET", f"{TASK_API}/tasks?limit=100&offset={offset}", token)
        existing |= {t["title"] for t in page["items"]}
        offset += 100
        if offset >= page["total"]:
            break

    created = skipped = 0
    today = date.today()
    first_id = None
    for i, (title, desc, status, due, extra) in enumerate(SEEDS):
        full_title = f"[seed] {title}"
        if full_title in existing:
            skipped += 1
            continue
        task = call("POST", f"{TASK_API}/tasks", token, {
            "title": full_title, "description": desc,
            "due_date": (today + timedelta(days=due)).isoformat() if due is not None else None,
            **extra_fields(i, due, today),
            **({"parent_task": first_id} if first_id and i % 7 == 3 else {})})
        tid = task["id"]
        first_id = first_id or tid
        if status in ("in_progress", "completed"):
            call("PUT", f"{TASK_API}/tasks/{tid}", token, {"status": "in_progress"})
        if extra:
            call("PUT", f"{TASK_API}/tasks/{tid}", token, {"description": (desc or "") + " (revised)"})
        if status == "completed":
            call("PUT", f"{TASK_API}/tasks/{tid}", token, {"status": "completed"})
        created += 1
    print(f"seed: created {created}, skipped {skipped} already present "
          f"(of {len(SEEDS)}). Events flow A -> outbox -> Kafka -> B.")


if __name__ == "__main__":
    main()
