import pytest
from datetime import datetime
from bson import ObjectId
from app import db as dbmod


@pytest.mark.asyncio
async def test_stats_calculation(client):
    now = datetime.utcnow().isoformat()
    r1 = await dbmod.reviews.insert_one(
        {
            "submission_id": ObjectId(),
            "score": 8,
            "issues": [
                {"title": "X", "detail": "Y", "severity": "med", "category": "bug"}
            ],
            "created_at": now,
        }
    )
    await dbmod.submissions.insert_one(
        {
            "code": "print()",
            "language": "python",
            "status": "completed",
            "created_at": now,
            "updated_at": now,
            "ip": "1.1.1.1",
            "review_id": r1.inserted_id,
            "error": None,
        }
    )
    r = await client.get("/api/stats?language=python")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert data["avg_score"] is None or isinstance(data["avg_score"], (int, float))
    assert isinstance(data["common_issues"], list)
