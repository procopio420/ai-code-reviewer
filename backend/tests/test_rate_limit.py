import pytest


@pytest.mark.asyncio
async def test_rate_limit_hits_429(client):
    payload = {"language": "python", "code": "print('x')"}
    codes = []

    for _ in range(4):
        r = await client.post("/api/reviews", json=payload)
        codes.append(r.status_code)

    assert codes[:3] == [202, 202, 202]
    assert codes[3] == 429
