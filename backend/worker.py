import asyncio
from datetime import datetime
from bson import ObjectId
from celery.signals import worker_process_init, worker_shutdown

from app.queue import celery
from app.ai import review_code_sync
from app import db as dbmod
from app.db import init_db_sync, close_db_sync
from app.cache import init_cache, close_cache, cache_set_review_id

_LOOP: asyncio.AbstractEventLoop | None = None


@worker_process_init.connect
def _on_worker_process_init(**_):
    global _LOOP
    if _LOOP is None:
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
        init_db_sync()
        _LOOP.run_until_complete(init_cache())


@worker_shutdown.connect
def _on_worker_shutdown(**_):
    global _LOOP
    try:
        if _LOOP is not None:
            _LOOP.run_until_complete(close_cache())
        close_db_sync()
    finally:
        if _LOOP is not None:
            _LOOP.close()
            _LOOP = None


@celery.task(name="process_review")
def process_review(submission_id: str):
    global _LOOP
    if _LOOP is None:
        _LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_LOOP)
        init_db_sync()
        _LOOP.run_until_complete(init_cache())
    return _LOOP.run_until_complete(_run(submission_id))


async def _run(submission_id: str):
    sub = await dbmod.submissions.find_one({"_id": ObjectId(submission_id)})
    if not sub:
        return None

    await dbmod.submissions.update_one(
        {"_id": sub["_id"]}, {"$set": {"status": "in_progress"}}
    )

    try:
        data = review_code_sync(sub["language"], sub["code"])
        doc = {
            "submission_id": sub["_id"],
            **data,
            "created_at": datetime.utcnow().isoformat(),
        }
        ins = await dbmod.reviews.insert_one(doc)

        code_hash = sub.get("code_hash")
        if code_hash:
            await cache_set_review_id(code_hash, str(ins.inserted_id))

        await dbmod.submissions.update_one(
            {"_id": sub["_id"]},
            {
                "$set": {
                    "status": "completed",
                    "review_id": ins.inserted_id,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        )
    except Exception as e:
        await dbmod.submissions.update_one(
            {"_id": sub["_id"]},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        )
    return True
