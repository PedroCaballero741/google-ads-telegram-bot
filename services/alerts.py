from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal
import logging

from sqlalchemy import func
from database import get_session, AdCost, AlertThreshold, AlertHistory
from database.models import ThresholdType
from config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing and checking alerts."""

    def create_alert(
        self,
        name: str,
        threshold_value: float,
        telegram_chat_id: str,
        threshold_type: ThresholdType = ThresholdType.DAILY_SPEND,
        campaign_id: Optional[str] = None
    ) -> dict:
        """Create a new alert threshold. Returns dict to avoid DetachedInstanceError."""
        with get_session() as session:
            alert = AlertThreshold(
                name=name,
                threshold_type=threshold_type,
                threshold_value=Decimal(str(threshold_value)),
                campaign_id=campaign_id,
                telegram_chat_id=telegram_chat_id,
                is_active=True,
            )
            session.add(alert)
            session.flush()

            logger.info(f"Created alert '{name}' with threshold ${threshold_value}")

            # Refresh to get all fields
            session.refresh(alert)

            # Return dict before session closes to avoid DetachedInstanceError
            return {
                "id": alert.id,
                "name": alert.name,
                "threshold_type": alert.threshold_type,
                "threshold_value": float(alert.threshold_value),
                "campaign_id": alert.campaign_id,
                "telegram_chat_id": alert.telegram_chat_id,
                "is_active": alert.is_active,
            }

    def get_active_alerts(self, chat_id: Optional[str] = None) -> List[dict]:
        """Get all active alert thresholds as dictionaries to avoid DetachedInstanceError."""
        with get_session() as session:
            query = session.query(AlertThreshold).filter(AlertThreshold.is_active == True)

            if chat_id:
                query = query.filter(AlertThreshold.telegram_chat_id == chat_id)

            alerts = query.all()

            # Convert to dicts before session closes to avoid DetachedInstanceError
            return [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "threshold_type": alert.threshold_type,
                    "threshold_value": float(alert.threshold_value),
                    "campaign_id": alert.campaign_id,
                    "telegram_chat_id": alert.telegram_chat_id,
                    "is_active": alert.is_active,
                }
                for alert in alerts
            ]

    def deactivate_alert(self, alert_id: int) -> bool:
        """Deactivate an alert by ID."""
        with get_session() as session:
            alert = session.query(AlertThreshold).filter(AlertThreshold.id == alert_id).first()
            if alert:
                alert.is_active = False
                logger.info(f"Deactivated alert {alert_id}")
                return True
            return False

    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert by ID."""
        with get_session() as session:
            alert = session.query(AlertThreshold).filter(AlertThreshold.id == alert_id).first()
            if alert:
                session.delete(alert)
                logger.info(f"Deleted alert {alert_id}")
                return True
            return False

    def _get_current_daily_spend(self, target_date: date) -> float:
        """Get the current total daily spend."""
        with get_session() as session:
            result = session.query(
                func.sum(AdCost.cost_micros)
            ).filter(AdCost.date == target_date).scalar()

            if result is None:
                return 0.0
            return result / 1_000_000

    def _get_campaign_spend(self, campaign_id: str, target_date: date) -> float:
        """Get spend for a specific campaign."""
        with get_session() as session:
            result = session.query(
                func.sum(AdCost.cost_micros)
            ).filter(
                AdCost.date == target_date,
                AdCost.campaign_id == campaign_id
            ).scalar()

            if result is None:
                return 0.0
            return result / 1_000_000

    def _has_already_triggered(self, threshold_id: int, target_date: date) -> bool:
        """Check if an alert has already triggered for this date."""
        with get_session() as session:
            existing = session.query(AlertHistory).filter(
                AlertHistory.threshold_id == threshold_id,
                AlertHistory.triggered_date == target_date
            ).first()
            return existing is not None

    def _record_alert_trigger(
        self,
        threshold_id: int,
        target_date: date,
        actual_value: float
    ) -> AlertHistory:
        """Record that an alert was triggered."""
        with get_session() as session:
            history = AlertHistory(
                threshold_id=threshold_id,
                triggered_date=target_date,
                actual_value=Decimal(str(actual_value)),
                message_sent=False,
            )
            session.add(history)
            session.flush()
            session.refresh(history)
            return history

    def mark_alert_sent(self, history_id: int) -> None:
        """Mark an alert as having its message sent."""
        with get_session() as session:
            history = session.query(AlertHistory).filter(AlertHistory.id == history_id).first()
            if history:
                history.message_sent = True

    def check_alerts(self, target_date: Optional[date] = None) -> List[dict]:
        """
        Check all active alerts and return list of triggered alerts.

        Returns:
            List of dicts with alert info for triggered thresholds
        """
        if target_date is None:
            target_date = date.today()

        triggered = []
        alerts = self.get_active_alerts()

        for alert in alerts:
            # Skip if already triggered today
            if self._has_already_triggered(alert["id"], target_date):
                continue

            # Get current value based on alert type
            if alert["threshold_type"] == ThresholdType.DAILY_SPEND:
                current_value = self._get_current_daily_spend(target_date)
            elif alert["threshold_type"] == ThresholdType.CAMPAIGN_SPEND:
                if not alert["campaign_id"]:
                    continue
                current_value = self._get_campaign_spend(alert["campaign_id"], target_date)
            else:
                continue

            # Check if threshold exceeded
            threshold_value = alert["threshold_value"]
            if current_value >= threshold_value:
                # Record the trigger
                history = self._record_alert_trigger(alert["id"], target_date, current_value)

                triggered.append({
                    "alert_id": alert["id"],
                    "history_id": history.id,
                    "alert_name": alert["name"],
                    "threshold_type": alert["threshold_type"].value,
                    "threshold_value": threshold_value,
                    "actual_value": current_value,
                    "chat_id": alert["telegram_chat_id"],
                    "campaign_id": alert["campaign_id"],
                })

                logger.warning(
                    f"Alert triggered: {alert['name']} - "
                    f"Threshold: ${threshold_value:.2f}, Actual: ${current_value:.2f}"
                )

        return triggered

    def format_alert_message(self, alert_info: dict) -> str:
        """Format an alert notification message."""
        return (
            f"⚠️ *ALERT: {alert_info['alert_name']}*\n\n"
            f"Threshold of ${alert_info['threshold_value']:,.2f} exceeded!\n"
            f"Current spend: ${alert_info['actual_value']:,.2f}\n"
            f"Type: {alert_info['threshold_type'].replace('_', ' ').title()}"
        )

    def format_alerts_list(self, chat_id: str) -> str:
        """Format a list of active alerts for display."""
        alerts = self.get_active_alerts(chat_id)

        if not alerts:
            return "No active alerts configured.\n\nUse /setalert <amount> to create one."

        message = "📋 *Active Alerts*\n\n"
        for alert in alerts:
            status = "✅" if alert["is_active"] else "❌"
            message += (
                f"{status} *{alert['name']}*\n"
                f"   Threshold: ${alert['threshold_value']:,.2f}\n"
                f"   Type: {alert['threshold_type'].value.replace('_', ' ').title()}\n"
                f"   ID: {alert['id']}\n\n"
            )

        return message
