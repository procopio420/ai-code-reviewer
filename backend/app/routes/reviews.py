from fastapi import APIRouter, Request, Query, Response, status
from datetime import datetime
from bson import ObjectId
from typing import Optional
import asyncio
import json

from sse_starlette.sse import EventSourceResponse

from ..schemas import ReviewCreate, ReviewOut, ReviewAccepted
from ..rate_limit import limit_check
from ..queue import celery
from ..cache import code_hash as compute_hash, cache_get_review_id
from .. import db

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


async def get_reviews_for_submission(id: str) -> ReviewOut:
    submission = await db.submissions.find_one({"_id": ObjectId(id)})
    if not submission:
        raise ValueError("Not found")

    score = issues = security = performance = suggestions = None

    if submission.get("review_id"):
        review = await db.reviews.find_one({"_id": submission["review_id"]})
        if review:
            score = review.get("score")
            issues = review.get("issues", [])
            security = review.get("security", [])
            performance = review.get("performance", [])
            suggestions = review.get("suggestions", [])

    return ReviewOut(
        id=str(submission["_id"]),
        status=submission["status"],
        created_at=submission["created_at"],
        updated_at=submission["updated_at"],
        language=submission["language"],
        score=score,
        issues=issues,
        security=security,
        performance=performance,
        suggestions=suggestions,
        error=submission.get("error"),
    )


@router.post("", response_model=ReviewAccepted, status_code=status.HTTP_202_ACCEPTED)
async def submit_review(payload: ReviewCreate, request: Request, response: Response):
    ip = request.client.host
    await limit_check(ip)

    now = datetime.utcnow().isoformat()
    code_hash = compute_hash(payload.language, payload.code)

    cached_review_id = await cache_get_review_id(code_hash)
    if cached_review_id:
        doc = {
            "code": payload.code,
            "language": payload.language,
            "status": "completed",
            "created_at": now,
            "updated_at": now,
            "ip": ip,
            "review_id": ObjectId(cached_review_id),
            "error": None,
            "code_hash": code_hash,
        }
        res = await db.submissions.insert_one(doc)
        return ReviewAccepted(id=str(res.inserted_id), status="completed")

    submission = {
        "code": payload.code,
        "language": payload.language,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "ip": ip,
        "review_id": None,
        "error": None,
        "code_hash": code_hash,
    }
    result = await db.submissions.insert_one(submission)
    submission_id = str(result.inserted_id)

    celery.send_task("process_review", args=[submission_id])

    response.headers["Location"] = f"/api/reviews/{submission_id}"

    return ReviewAccepted(id=submission_id, status="pending")


@router.get("/{id}", response_model=ReviewOut)
async def get_review(id: str):
    return await get_reviews_for_submission(id)


@router.get("", response_model=list[ReviewOut])
async def list_reviews(
    language: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[int] = Query(None, ge=1, le=10),
    max_score: Optional[int] = Query(None, ge=1, le=10),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    q = {}
    if language:
        q["language"] = language
    if status:
        q["status"] = status
    if start_date or end_date:
        created = {}
        if start_date:
            created["$gte"] = start_date
        if end_date:
            created["$lte"] = end_date
        q["created_at"] = created

    cursor = (
        db.submissions.find(q)
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    submissions = await cursor.to_list(length=page_size)

    reviews = [
        await get_reviews_for_submission(str(submission["_id"]))
        for submission in submissions
    ]

    if min_score is not None or max_score is not None:
        reviews = [
            review
            for review in reviews
            if (
                review.score is not None
                and (min_score is None or review.score >= min_score)
                and (max_score is None or review.score <= max_score)
            )
        ]
    return reviews


@router.get("/{id}/stream")
async def stream_review(
    id: str,
    interval_ms: int = Query(1000, ge=10, le=60000),
    ping: int = Query(15000, ge=0, le=60000),
):
    async def event_gen():
        try:
            oid = ObjectId(id)
        except Exception:
            yield {"event": "error", "data": "invalid_id"}
            return

        while True:
            sub = await db.submissions.find_one({"_id": oid})
            if not sub:
                yield {"event": "error", "data": "not_found"}
                return

            status_val = sub.get("status", "pending")
            yield {"event": "status", "data": status_val}

            if status_val in ("completed", "failed"):
                payload = {"status": status_val}
                if sub.get("review_id"):
                    review = await db.reviews.find_one({"_id": sub["review_id"]})
                    if review:
                        review["_id"] = str(review["_id"])
                        if "submission_id" in review:
                            review["submission_id"] = str(review["submission_id"])
                    payload["review"] = review
                yield {"event": "done", "data": json.dumps(payload)}
                return

            await asyncio.sleep(interval_ms / 1000.0)

    return EventSourceResponse(
        event_gen(),
        ping=None if ping == 0 else ping,
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
