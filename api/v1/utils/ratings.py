#!/usr/bin/python
"""Shared rating-submission logic used by both the rider and driver
rating endpoints: create the Rating row and atomically recompute the
ratee's aggregate average_rating/ratings_count in a single update() call."""

import logging

from models import storage
from models.rating import Rating

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def submit_rating(trip_id, rater_type, rater_id, ratee_type, ratee_id, score, comment):
    """Returns (rating, error). `error` is None on success, otherwise an
    (message, status_code) tuple the caller can return directly."""
    existing = storage.get(
        "Rating", trip_id=trip_id, rater_id=rater_id, ratee_id=ratee_id
    )
    if existing:
        return None, ("you have already rated this trip", 409)

    ratee = storage.get(ratee_type, id=ratee_id)
    if not ratee:
        return None, ("ratee not found", 404)

    try:
        rating = Rating(
            trip_id=trip_id,
            rater_type=rater_type,
            rater_id=rater_id,
            ratee_type=ratee_type,
            ratee_id=ratee_id,
            score=score,
            comment=comment,
        )
        rating.save()
    except Exception:
        logger.exception("failed to save rating")
        return None, ("An internal error", 500)

    old_count = ratee.ratings_count or 0
    old_avg = ratee.average_rating or 0.0
    new_count = old_count + 1
    new_avg = ((old_avg * old_count) + score) / new_count

    try:
        storage.update(
            ratee_type, ratee_id, average_rating=new_avg, ratings_count=new_count
        )
    except Exception:
        logger.exception("failed to update ratee aggregate")
        return None, ("An internal error", 500)

    return rating, None
