import jwtutil
from jwtutil import auth


def test_health_public(client):
    assert client.get("/health").status_code == 200


def test_jwt_enforced_on_all_routes(client):
    for p in ("/stats", "/activity", "/sync-status"):
        assert client.get(p).status_code == 401
        assert client.get(p, headers=auth(exp_in=-60)).status_code == 401
        assert client.get(p, headers=auth(iss="http://evil/realms/x")).status_code == 401
        assert client.get(p, headers={"Authorization": f"Bearer {jwtutil.bad_signature_token()}"}).status_code == 401


def test_stats_computed_from_replica(client, put_task):
    put_task(status="pending")
    put_task(status="pending")
    put_task(status="in_progress")
    put_task(status="completed", updated_days_ago=1)
    put_task(status="completed", updated_days_ago=30)  # completed, but not in last 7 days
    s = client.get("/stats", headers=auth()).json()
    assert s == {"total": 5, "pending": 2, "in_progress": 1, "completed": 2, "completed_last_7_days": 1}


def test_stats_exclude_soft_deleted_and_other_users(client, put_task):
    put_task(status="completed")
    put_task(status="completed", deleted=True)
    put_task(status="pending", user="someone-else")
    s = client.get("/stats", headers=auth("user-1")).json()
    assert s["total"] == 1 and s["completed"] == 1 and s["pending"] == 0


def test_stats_empty(client):
    s = client.get("/stats", headers=auth()).json()
    assert s == {"total": 0, "pending": 0, "in_progress": 0, "completed": 0, "completed_last_7_days": 0}


def test_activity_scoped_limited_and_ordered(client, put_activity):
    put_activity(n=5)
    put_activity(user="someone-else", n=3)
    rows = client.get("/activity?limit=3", headers=auth()).json()
    assert len(rows) == 3
    times = [r["occurred_at"] for r in rows]
    assert times == sorted(times, reverse=True)
    assert len(client.get("/activity", headers=auth()).json()) == 5
    assert client.get("/activity?limit=0", headers=auth()).status_code == 422


def test_sync_status(client, put_task, put_activity):
    empty = client.get("/sync-status", headers=auth()).json()
    assert empty["live_tasks"] == 0 and empty["last_event_id"] is None
    put_task()
    put_task(deleted=True)
    put_activity()
    s = client.get("/sync-status", headers=auth()).json()
    assert s["live_tasks"] == 1 and s["last_event_id"] and s["seconds_since_sync"] >= 0
