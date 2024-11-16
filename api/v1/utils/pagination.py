#!/usr/bin/python3
from sqlalchemy import asc, desc, String, Float, DateTime, Integer
import sqlalchemy
from datetime import datetime
from flask import request, abort
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def paginate(cls, column_type, column):
    page_size = request.args.get("page_size", default=15, type=int)
    asc_order_recently = (
        request.args.get("asc_order_recently", "true").lower() == "true"
    )
    next_page = request.args.get("next_page")
    date = datetime.now()
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
                next_page = date
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
