import pytest
from bson import ObjectId
from app import db as dbmod


@pytest.mark.asyncio
async def test_cache_hit_returns_completed(client, run_worker):
    payload = {"language": "python", "code": "print('hello')"}

    r1 = await client.post("/api/reviews", json=payload)
    assert r1.status_code == 202
    s1 = r1.json()
    rid1 = s1["id"]

    await run_worker(rid1)

    rget = await client.get(f"/api/reviews/{rid1}")
    assert rget.status_code == 200
    assert rget.json()["status"] in ("completed", "failed")

    r2 = await client.post("/api/reviews", json=payload)
    assert r2.status_code == 202
    body2 = r2.json()
    assert body2["status"] == "completed"
    rid2 = body2["id"]

    sub2 = await dbmod.submissions.find_one({"_id": ObjectId(rid2)})
    assert sub2 and sub2.get("review_id")
