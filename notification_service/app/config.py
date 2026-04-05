from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service identification
    service_name: str = "notification-service"
    log_level: str = "INFO"

    # Kafka connection (comma-separated string from env)
    kafka_bootstrap_servers: str = "kafka-1:9092,kafka-2:9092,kafka-3:9092"

    # Kafka consumer settings
    kafka_consumer_group: str = "notification-service-group"
    kafka_auto_offset_reset: str = "earliest"

    @property
    def kafka_bootstrap_servers_list(self) -> list[str]:
        return [s.strip() for s in self.kafka_bootstrap_servers.split(",")]

    class Config:
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
