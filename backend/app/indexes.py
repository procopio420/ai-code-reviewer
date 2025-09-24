from pymongo import ASCENDING, DESCENDING, IndexModel


async def ensure_indexes(db):
    sub_indexes = [
        IndexModel([("code_hash", ASCENDING)], name="sub_code_hash"),
        IndexModel([("review_id", ASCENDING)], name="sub_review_id"),
        IndexModel(
            [("language", ASCENDING), ("created_at", DESCENDING)],
            name="sub_lang_created",
        ),
        IndexModel(
            [("ip", ASCENDING), ("created_at", DESCENDING)], name="sub_ip_created"
        ),
    ]

    rev_indexes = [
        IndexModel(
            [("submission_id", ASCENDING)], name="rev_unique_submission", unique=True
        ),
        IndexModel([("created_at", DESCENDING)], name="rev_created_at_desc"),
        IndexModel(
            [("score", DESCENDING), ("created_at", DESCENDING)],
            name="rev_score_created",
        ),
        IndexModel([("issues.title", ASCENDING)], name="rev_issues_title"),
    ]

    await db["submissions"].create_indexes(sub_indexes)
    await db["reviews"].create_indexes(rev_indexes)
