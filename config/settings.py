from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import pytz


class Settings(BaseSettings):
    # Google Ads Configuration
    google_ads_developer_token: str = Field(..., alias="GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_client_id: str = Field(..., alias="GOOGLE_ADS_CLIENT_ID")
    google_ads_client_secret: str = Field(..., alias="GOOGLE_ADS_CLIENT_SECRET")
    google_ads_refresh_token: str = Field(..., alias="GOOGLE_ADS_REFRESH_TOKEN")
    google_ads_customer_id: str = Field(..., alias="GOOGLE_ADS_CUSTOMER_ID")
    google_ads_login_customer_id: Optional[str] = Field(None, alias="GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    # Telegram Configuration
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(..., alias="TELEGRAM_CHAT_ID")
    authorized_users: str = Field("", alias="AUTHORIZED_USERS")  # Comma-separated user IDs

    @property
    def authorized_user_ids(self) -> list[int]:
        """Return list of authorized user IDs."""
        if not self.authorized_users:
            # If not set, allow the default chat_id
            return [int(self.telegram_chat_id)]
        return [int(uid.strip()) for uid in self.authorized_users.split(",") if uid.strip()]

    # Database Configuration
    database_url: str = Field(..., alias="DATABASE_URL")

    # Alert Settings
    default_daily_threshold: float = Field(1000.00, alias="DEFAULT_DAILY_THRESHOLD")

    # Timezone
    timezone: str = Field("America/New_York", alias="TIMEZONE")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def tz(self):
        return pytz.timezone(self.timezone)

    def get_google_ads_config(self) -> dict:
        """Return Google Ads client configuration dictionary."""
        config = {
            "developer_token": self.google_ads_developer_token,
            "client_id": self.google_ads_client_id,
            "client_secret": self.google_ads_client_secret,
            "refresh_token": self.google_ads_refresh_token,
            "use_proto_plus": True,
        }
        if self.google_ads_login_customer_id:
            config["login_customer_id"] = self.google_ads_login_customer_id
        return config


settings = Settings()
