#!/usr/bin/python
from sqlalchemy import Column, String, ForeignKey, Integer, Float, Boolean, DateTime
from models.base_model import Base, BaseModel


class TotalPayment(BaseModel, Base):
    __tablename__ = "total_payments"
    trip_id = Column(String(128), ForeignKey("trips.id"), nullable=False)
    driver_id = Column(String(128), ForeignKey("drivers.id"), nullable=False)
    trip_fare = Column(Float, nullable=False)
    total_revenue = Column(Float, default=0.0)
    driver_earning = Column(Float, default=0.0)
    driver_commission = Column(Float, nullable=False)
    total_number_of_riders = Column(Integer, default=0)
    number_of_riders_paid = Column(Integer, default=0)
    number_of_riders_not_paid = Column(Integer, default=0)
    transaction_over = Column(Boolean, default=False)
    transaction_time = Column(DateTime)
    status = Column(String(60), default="pending")

    def validate_rider_counts(self):
        if (
            self.number_of_riders_not_paid + self.number_of_riders_paid
            != self.total_number_of_riders
        ):
            raise ValueError(
                "Total riders must equal the sum of paid and unpaid riders."
            )
