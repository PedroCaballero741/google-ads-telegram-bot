from sqlalchemy import (
    Column, Integer, BigInteger, String, Date, DateTime,
    Numeric, Boolean, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ThresholdType(enum.Enum):
    DAILY_SPEND = "daily_spend"
    CAMPAIGN_SPEND = "campaign_spend"


class AdCost(Base):
    """Stores Google Ads cost data."""
    __tablename__ = "ad_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    campaign_id = Column(String(50), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    cost_micros = Column(BigInteger, nullable=False, default=0)  # Cost in micros (divide by 1,000,000)
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    conversions = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure we don't have duplicate entries for same date + campaign
    __table_args__ = (
        UniqueConstraint("date", "campaign_id", name="uix_date_campaign"),
        Index("ix_ad_costs_date_campaign", "date", "campaign_id"),
    )

    @property
    def cost(self) -> float:
        """Return cost in actual currency (not micros)."""
        return self.cost_micros / 1_000_000

    def __repr__(self):
        return f"<AdCost(date={self.date}, campaign={self.campaign_name}, cost=${self.cost:.2f})>"


class AlertThreshold(Base):
    """Stores alert threshold configurations."""
    __tablename__ = "alert_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    threshold_type = Column(Enum(ThresholdType), nullable=False, default=ThresholdType.DAILY_SPEND)
    threshold_value = Column(Numeric(12, 2), nullable=False)
    campaign_id = Column(String(50), nullable=True)  # Only for campaign-specific alerts
    telegram_chat_id = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to alert history
    history = relationship("AlertHistory", back_populates="threshold", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AlertThreshold(name={self.name}, value=${self.threshold_value}, active={self.is_active})>"


class AlertHistory(Base):
    """Tracks when alerts were triggered."""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    threshold_id = Column(Integer, ForeignKey("alert_thresholds.id", ondelete="CASCADE"), nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    triggered_date = Column(Date, nullable=False, index=True)  # The date the alert was for
    actual_value = Column(Numeric(12, 2), nullable=False)
    message_sent = Column(Boolean, nullable=False, default=False)

    # Relationship to threshold
    threshold = relationship("AlertThreshold", back_populates="history")

    # Ensure we only trigger once per threshold per day
    __table_args__ = (
        UniqueConstraint("threshold_id", "triggered_date", name="uix_threshold_date"),
    )

    def __repr__(self):
        return f"<AlertHistory(threshold_id={self.threshold_id}, date={self.triggered_date}, value=${self.actual_value})>"
