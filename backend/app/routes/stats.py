from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional
from .. import db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(
    language: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    match: dict = {"status": "completed"}
    if language:
        match["language"] = language

    date_match = None
    if start or end:
        exprs = []
        if start:
            try:
                start_dt = datetime.fromisoformat(start)
            except Exception:
                start_dt = start
            exprs.append({"$gte": [{"$toDate": "$created_at"}, start_dt]})
        if end:
            try:
                end_dt = datetime.fromisoformat(end)
            except Exception:
                end_dt = end
            exprs.append({"$lt": [{"$toDate": "$created_at"}, end_dt]})
        if exprs:
            date_match = {"$expr": {"$and": exprs}}

    pipeline = [
        {"$match": match},
    ]

    if date_match:
        pipeline.append({"$match": date_match})

    pipeline += [
        {
            "$lookup": {
                "from": "reviews",
                "localField": "review_id",
                "foreignField": "_id",
                "as": "review",
            }
        },
        {"$unwind": "$review"},
        {
            "$facet": {
                "stats": [
                    {
                        "$group": {
                            "_id": None,
                            "total": {"$sum": 1},
                            "avg_score": {"$avg": "$review.score"},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "total": 1,
                            "avg_score": {
                                "$cond": [
                                    {"$ne": ["$avg_score", None]},
                                    {"$round": ["$avg_score", 2]},
                                    None,
                                ]
                            },
                        }
                    },
                ],
                "issues": [
                    {
                        "$unwind": {
                            "path": "$review.issues",
                            "preserveNullAndEmptyArrays": False,
                        }
                    },
                    {"$group": {"_id": "$review.issues.title", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 100},
                    {"$project": {"_id": 0, "title": "$_id"}},
                ],
            }
        },
        {
            "$project": {
                "total": {"$ifNull": [{"$arrayElemAt": ["$stats.total", 0]}, 0]},
                "avg_score": {"$arrayElemAt": ["$stats.avg_score", 0]},
                "common_issues": "$issues.title",
            }
        },
    ]

    cur = db.submissions.aggregate(pipeline)
    docs = await cur.to_list(length=1)
    out = docs[0] if docs else {"total": 0, "avg_score": None, "common_issues": []}
    return out
