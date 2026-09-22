#!/usr/bin/python
from models.base_model import BaseModel, Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    VARCHAR,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)


class Rating(BaseModel, Base):
    __tablename__ = "ratings"
    trip_id = Column(String(128), ForeignKey("trips.id"), nullable=False)
    # rater/ratee are polymorphic (Rider or Driver), same pattern as
    # Notification's sender/receiver - no FK, the *_type column says which
    # table *_id belongs to
    rater_type = Column(VARCHAR(20), nullable=False)
    rater_id = Column(String(128), nullable=False)
    ratee_type = Column(VARCHAR(20), nullable=False)
    ratee_id = Column(String(128), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(String(500), nullable=True)

    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_rating_score_range"),
        UniqueConstraint(
            "trip_id", "rater_id", "ratee_id", name="uq_rating_once_per_pair_per_trip"
        ),
    )
