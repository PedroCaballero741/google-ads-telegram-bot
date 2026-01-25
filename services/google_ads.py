from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from datetime import date, timedelta
from typing import List, Dict, Optional
import logging

from config import settings
from database import get_session, AdCost

logger = logging.getLogger(__name__)


class GoogleAdsService:
    """Service for interacting with Google Ads API."""

    def __init__(self):
        self.client = GoogleAdsClient.load_from_dict(settings.get_google_ads_config())
        self.customer_id = settings.google_ads_customer_id.replace("-", "")

    def fetch_cost_report(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Fetch cost report data from Google Ads.

        Args:
            start_date: Start date for the report
            end_date: End date for the report (defaults to start_date)

        Returns:
            List of dictionaries with campaign cost data
        """
        if end_date is None:
            end_date = start_date

        ga_service = self.client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                segments.date,
                campaign.id,
                campaign.name,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions
            FROM campaign
            WHERE segments.date BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
            ORDER BY segments.date DESC, campaign.name
        """

        results = []
        try:
            response = ga_service.search_stream(
                customer_id=self.customer_id,
                query=query
            )

            for batch in response:
                for row in batch.results:
                    results.append({
                        "date": row.segments.date,
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "cost_micros": row.metrics.cost_micros,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "conversions": float(row.metrics.conversions),
                    })

            logger.info(f"Fetched {len(results)} rows from Google Ads for {start_date} to {end_date}")

        except GoogleAdsException as ex:
            logger.error(f"Google Ads API error: {ex.failure.errors[0].message}")
            raise

        return results

    def sync_costs(self, start_date: date, end_date: Optional[date] = None) -> int:
        """
        Sync cost data from Google Ads to the database.

        Args:
            start_date: Start date to sync
            end_date: End date to sync (defaults to start_date)

        Returns:
            Number of records synced
        """
        data = self.fetch_cost_report(start_date, end_date)

        if not data:
            logger.info("No data to sync")
            return 0

        synced_count = 0
        with get_session() as session:
            for row in data:
                # Parse date string to date object
                row_date = date.fromisoformat(row["date"])

                # Try to find existing record
                existing = session.query(AdCost).filter(
                    AdCost.date == row_date,
                    AdCost.campaign_id == row["campaign_id"]
                ).first()

                if existing:
                    # Update existing record
                    existing.campaign_name = row["campaign_name"]
                    existing.cost_micros = row["cost_micros"]
                    existing.impressions = row["impressions"]
                    existing.clicks = row["clicks"]
                    existing.conversions = row["conversions"]
                else:
                    # Create new record
                    ad_cost = AdCost(
                        date=row_date,
                        campaign_id=row["campaign_id"],
                        campaign_name=row["campaign_name"],
                        cost_micros=row["cost_micros"],
                        impressions=row["impressions"],
                        clicks=row["clicks"],
                        conversions=row["conversions"],
                    )
                    session.add(ad_cost)

                synced_count += 1

        logger.info(f"Synced {synced_count} records to database")
        return synced_count

    def sync_today(self) -> int:
        """Sync today's cost data."""
        today = date.today()
        return self.sync_costs(today)

    def sync_last_n_days(self, days: int = 7) -> int:
        """Sync the last N days of cost data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        return self.sync_costs(start_date, end_date)
