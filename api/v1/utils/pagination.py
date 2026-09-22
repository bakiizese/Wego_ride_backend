#!/usr/bin/python
from sqlalchemy import asc, desc, String, Float, DateTime, Integer
from datetime import datetime, timedelta
from flask import request, abort
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Columns callers are allowed to sort on, per model. Anything else is
# rejected with a clean 400 instead of being passed straight to getattr().
ALLOWED_SORT_COLUMNS = {
    "Trip": {"created_at", "updated_at", "fare", "distance", "status", "pickup_time"},
    "TripRider": {"created_at", "updated_at", "status", "is_past"},
    "Payment": {"created_at", "updated_at", "amount", "payment_status"},
    "Notification": {"created_at", "updated_at", "is_read"},
    "Rider": {
        "created_at",
        "updated_at",
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
    },
    "Driver": {
        "created_at",
        "updated_at",
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
    },
    "Admin": {
        "created_at",
        "updated_at",
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
    },
    "Location": {"created_at", "updated_at", "address"},
    "Rating": {"created_at", "updated_at", "score"},
}


def get_sort_column(model_cls, model_name, order_by):
    """Resolve a query-string `order_by` value against an explicit
    allowlist, aborting with 400 instead of doing an unguarded getattr()."""
    allowed = ALLOWED_SORT_COLUMNS.get(model_name, set())
    if order_by not in allowed:
        logger.warning("order_by '%s' not allowed for %s", order_by, model_name)
        abort(400, description=f"cannot sort {model_name} by '{order_by}'")
    return getattr(model_cls, order_by)


def paginate(cls, column_type, column):
    page_size = request.args.get("page_size", default=15, type=int)
    asc_order_recently = request.args.get("asc_order_recently", "true").lower() == "true"
    next_page = request.args.get("next_page")
    # stored timestamps are all UTC (datetime.utcnow(), same as everywhere
    # else in the codebase) - using local time here would make the cursor
    # boundary wrong by the server's UTC offset
    date = datetime.utcnow()
    asc_order = asc if asc_order_recently else desc
    if isinstance(column_type, DateTime):
        asc_order = desc if asc_order_recently else asc
        if next_page:
            try:
                next_page = datetime.strptime(next_page, "%Y-%m-%dT%H:%M:%S.%f")
            except Exception as e:
                logger.warning(e)
                abort(400)
        else:
            if asc_order_recently:
                # MySQL's DATETIME columns here have no fractional-seconds
                # precision, so storing a Python timestamp (which has
                # microseconds) gets *rounded*, not truncated - a row
                # committed a moment ago can end up stored up to ~1s in
                # the "future" relative to this request. Padding the
                # default cursor absorbs that instead of silently
                # dropping just-written rows off the first page.
                next_page = date + timedelta(seconds=1)
            else:
                next_page = datetime.min
            next_page.isoformat()
        condition = column < next_page if asc_order_recently else column > next_page
    elif isinstance(column_type, String):
        if not next_page:
            if asc_order_recently:
                next_page = ""
            else:
                next_page = "zzzzzzzzzzzzzzzzzzzzz"
        try:
            str(next_page)
        except ValueError as e:
            logger.warning(e)
            abort(400)
        condition = column > next_page if asc_order_recently else column < next_page
    elif isinstance(column_type, Integer) or isinstance(column_type, Float):
        if not next_page:
            if asc_order_recently:
                next_page = 0.0
            else:
                next_page = sys.maxsize
        try:
            float(next_page)
        except ValueError as e:
            logger.warning(e)
            abort(400)
        condition = column > next_page if asc_order_recently else column < next_page
    else:
        logger.warning(
            "order by {column_type} not allowed, only for datetime, string, int and float"
        )
        abort(400)

    data = cls.order_by(asc_order(column)).filter(condition).limit(page_size).all()
    return data
