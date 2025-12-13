from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    endpoint: str = Field(..., description="OpenMHz API endpoint to poll for calls")
    slack_webhook_url: str | None = Field(
        default=None, description="Slack webhook URL for notifications"
    )
    fetch_interval: int = Field(
        default=900, description="Seconds to wait between polls for new calls"
    )
    whisper_model_size: str = Field(
        default="distil-small.en", description="Whisper model size for transcription"
    )
    whisper_compute_type: str = Field(
        default="default", description="Computation type for fast-whisper"
    )
    notification_patterns: str | None = Field(
        default=None,
        description="Python regex patterns separated by &&& for notification triggers",
    )

    @computed_field
    def notification_patterns_list(self) -> list[str] | None:
        """Parse notification patterns string into a list."""
        if not self.notification_patterns:
            return None
        patterns = [
            pattern.strip()
            for pattern in self.notification_patterns.split("&&&")
            if pattern.strip()
        ]
        return patterns if patterns else None


application_settings = Settings()
