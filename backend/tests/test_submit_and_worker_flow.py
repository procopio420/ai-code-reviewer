import pytest


@pytest.mark.asyncio
async def test_submit_then_worker_then_get_review(client, stub_ai_review, run_worker):
    payload = {
        "language": "python",
        "code": "def calculate_average(numbers):\n    return sum(numbers)/len(numbers)\n\nresult = calculate_average([])\n",
    }
    r = await client.post("/api/reviews", json=payload)
    assert r.status_code == 202
    data = r.json()
    sub_id = data["id"]

    assert r.headers.get("Location") == f"/api/reviews/{sub_id}"

    await run_worker(sub_id)

    r2 = await client.get(f"/api/reviews/{sub_id}")
    assert r2.status_code == 200
    review = r2.json()
    assert review["status"] in ("completed", "failed")
