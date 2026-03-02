from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func
from decimal import Decimal
import logging

from database import get_session, AdCost
from config import settings

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating cost reports."""

    @staticmethod
    def _format_currency(amount: float) -> str:
        """Format amount as currency."""
        return f"${amount:,.2f}"

    @staticmethod
    def _format_number(num: int) -> str:
        """Format number with thousands separator."""
        return f"{num:,}"

    def get_daily_total(self, target_date: date) -> Dict:
        """
        Get total spend for a specific date.

        Returns:
            Dictionary with total cost, impressions, clicks, conversions
        """
        with get_session() as session:
            result = session.query(
                func.sum(AdCost.cost_micros).label("total_cost_micros"),
                func.sum(AdCost.impressions).label("total_impressions"),
                func.sum(AdCost.clicks).label("total_clicks"),
                func.sum(AdCost.conversions).label("total_conversions"),
                func.count(AdCost.id).label("campaign_count")
            ).filter(AdCost.date == target_date).first()

            if not result or result.total_cost_micros is None:
                return {
                    "date": target_date,
                    "total_cost": 0.0,
                    "total_impressions": 0,
                    "total_clicks": 0,
                    "total_conversions": 0.0,
                    "campaign_count": 0,
                    "has_data": False,
                }

            return {
                "date": target_date,
                "total_cost": result.total_cost_micros / 1_000_000,
                "total_impressions": result.total_impressions or 0,
                "total_clicks": result.total_clicks or 0,
                "total_conversions": float(result.total_conversions or 0),
                "campaign_count": result.campaign_count,
                "has_data": True,
            }

    def get_date_range_summary(self, start_date: date, end_date: date) -> Dict:
        """Get aggregated summary for a date range."""
        with get_session() as session:
            result = session.query(
                func.sum(AdCost.cost_micros).label("total_cost_micros"),
                func.sum(AdCost.impressions).label("total_impressions"),
                func.sum(AdCost.clicks).label("total_clicks"),
                func.sum(AdCost.conversions).label("total_conversions"),
            ).filter(
                AdCost.date >= start_date,
                AdCost.date <= end_date
            ).first()

            if not result or result.total_cost_micros is None:
                return {
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_cost": 0.0,
                    "total_impressions": 0,
                    "total_clicks": 0,
                    "total_conversions": 0.0,
                    "days": (end_date - start_date).days + 1,
                    "has_data": False,
                }

            return {
                "start_date": start_date,
                "end_date": end_date,
                "total_cost": result.total_cost_micros / 1_000_000,
                "total_impressions": result.total_impressions or 0,
                "total_clicks": result.total_clicks or 0,
                "total_conversions": float(result.total_conversions or 0),
                "days": (end_date - start_date).days + 1,
                "has_data": True,
            }

    def get_daily_breakdown(self, start_date: date, end_date: date) -> List[Dict]:
        """Get daily breakdown for a date range."""
        with get_session() as session:
            results = session.query(
                AdCost.date,
                func.sum(AdCost.cost_micros).label("total_cost_micros"),
                func.sum(AdCost.impressions).label("total_impressions"),
                func.sum(AdCost.clicks).label("total_clicks"),
            ).filter(
                AdCost.date >= start_date,
                AdCost.date <= end_date
            ).group_by(AdCost.date).order_by(AdCost.date.desc()).all()

            return [
                {
                    "date": row.date,
                    "cost": row.total_cost_micros / 1_000_000,
                    "impressions": row.total_impressions or 0,
                    "clicks": row.total_clicks or 0,
                }
                for row in results
            ]

    def get_campaign_costs(
        self,
        target_date: date,
        campaign_name: Optional[str] = None
    ) -> List[Dict]:
        """Get campaign-level costs for a date."""
        with get_session() as session:
            query = session.query(AdCost).filter(AdCost.date == target_date)

            if campaign_name:
                query = query.filter(AdCost.campaign_name.ilike(f"%{campaign_name}%"))

            results = query.order_by(AdCost.cost_micros.desc()).all()

            return [
                {
                    "campaign_id": row.campaign_id,
                    "campaign_name": row.campaign_name,
                    "cost": row.cost,
                    "impressions": row.impressions,
                    "clicks": row.clicks,
                    "conversions": float(row.conversions),
                }
                for row in results
            ]

    def format_today_report(self) -> str:
        """Generate formatted report for today."""
        today = date.today()
        data = self.get_daily_total(today)

        if not data["has_data"]:
            return f"📊 *Today's Report* ({today.strftime('%b %d, %Y')})\n\nNo data available yet."

        return (
            f"📊 *Today's Report* ({today.strftime('%b %d, %Y')})\n\n"
            f"💰 Total Spend: {self._format_currency(data['total_cost'])}\n"
            f"👁 Impressions: {self._format_number(data['total_impressions'])}\n"
            f"👆 Clicks: {self._format_number(data['total_clicks'])}\n"
            f"🎯 Conversions: {data['total_conversions']:.1f}\n"
            f"📋 Active Campaigns: {data['campaign_count']}"
        )

    def format_yesterday_report(self) -> str:
        """Generate formatted report for yesterday."""
        yesterday = date.today() - timedelta(days=1)
        data = self.get_daily_total(yesterday)

        if not data["has_data"]:
            return f"📊 *Yesterday's Report* ({yesterday.strftime('%b %d, %Y')})\n\nNo data available."

        return (
            f"📊 *Yesterday's Report* ({yesterday.strftime('%b %d, %Y')})\n\n"
            f"💰 Total Spend: {self._format_currency(data['total_cost'])}\n"
            f"👁 Impressions: {self._format_number(data['total_impressions'])}\n"
            f"👆 Clicks: {self._format_number(data['total_clicks'])}\n"
            f"🎯 Conversions: {data['total_conversions']:.1f}"
        )

    def format_week_report(self) -> str:
        """Generate formatted report for the last 7 days."""
        end_date = date.today()
        start_date = end_date - timedelta(days=6)

        summary = self.get_date_range_summary(start_date, end_date)
        daily = self.get_daily_breakdown(start_date, end_date)

        if not summary["has_data"]:
            return "📊 *Last 7 Days Report*\n\nNo data available."

        report = (
            f"📊 *Last 7 Days Report*\n"
            f"({start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')})\n\n"
            f"💰 Total Spend: {self._format_currency(summary['total_cost'])}\n"
            f"📈 Daily Average: {self._format_currency(summary['total_cost'] / summary['days'])}\n"
            f"👁 Impressions: {self._format_number(summary['total_impressions'])}\n"
            f"👆 Clicks: {self._format_number(summary['total_clicks'])}\n"
            f"🎯 Conversions: {summary['total_conversions']:.1f}\n\n"
            f"*Daily Breakdown:*\n"
        )

        for day in daily[:7]:
            report += f"  {day['date'].strftime('%a %m/%d')}: {self._format_currency(day['cost'])}\n"

        return report

    def format_month_report(self) -> str:
        """Generate formatted report for the current month."""
        today = date.today()
        start_date = today.replace(day=1)

        summary = self.get_date_range_summary(start_date, today)

        if not summary["has_data"]:
            return f"📊 *{today.strftime('%B %Y')} Report*\n\nNo data available."

        days_elapsed = (today - start_date).days + 1

        return (
            f"📊 *{today.strftime('%B %Y')} Report*\n\n"
            f"💰 Total Spend: {self._format_currency(summary['total_cost'])}\n"
            f"📅 Days Elapsed: {days_elapsed}\n"
            f"📈 Daily Average: {self._format_currency(summary['total_cost'] / days_elapsed)}\n"
            f"👁 Impressions: {self._format_number(summary['total_impressions'])}\n"
            f"👆 Clicks: {self._format_number(summary['total_clicks'])}\n"
            f"🎯 Conversions: {summary['total_conversions']:.1f}"
        )

    def format_campaign_report(self, campaign_name: str) -> str:
        """Generate formatted report for a specific campaign."""
        today = date.today()
        campaigns = self.get_campaign_costs(today, campaign_name)

        if not campaigns:
            return f"No campaigns found matching '{campaign_name}' for today."

        report = f"📋 *Campaign Report* ({today.strftime('%b %d, %Y')})\n"
        report += f"Search: '{campaign_name}'\n\n"

        for c in campaigns[:10]:  # Limit to 10 results
            report += (
                f"*{c['campaign_name']}*\n"
                f"  💰 {self._format_currency(c['cost'])} | "
                f"👁 {self._format_number(c['impressions'])} | "
                f"👆 {c['clicks']}\n\n"
            )

        return report

    def format_daily_summary_for_telegram(self) -> str:
        """Generate the daily summary report sent via scheduler."""
        yesterday = date.today() - timedelta(days=1)
        data = self.get_daily_total(yesterday)

        # Get top campaigns
        campaigns = self.get_campaign_costs(yesterday)[:5]

        if not data["has_data"]:
            return f"📊 *Daily Summary* - {yesterday.strftime('%b %d, %Y')}\n\nNo data recorded."

        report = (
            f"📊 *Daily Summary* - {yesterday.strftime('%b %d, %Y')}\n\n"
            f"💰 Total Spend: {self._format_currency(data['total_cost'])}\n"
            f"👁 Impressions: {self._format_number(data['total_impressions'])}\n"
            f"👆 Clicks: {self._format_number(data['total_clicks'])}\n"
            f"🎯 Conversions: {data['total_conversions']:.1f}\n"
        )

        if campaigns:
            report += "\n*Top Campaigns:*\n"
            for c in campaigns:
                report += f"  • {c['campaign_name'][:30]}: {self._format_currency(c['cost'])}\n"

        return report
