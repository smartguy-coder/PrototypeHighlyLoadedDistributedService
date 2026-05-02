import socket
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service identification
    SERVICE_NAME: str = "notification-service"
    ENVIRONMENT: str = "production"
    HOST: str = Field(default_factory=socket.gethostname)
    LOG_LEVEL: str = "INFO"

    # Kafka connection (comma-separated string from env)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-1:9092,kafka-2:9092,kafka-3:9092"

    # Kafka consumer settings
    KAFKA_CONSUMER_GROUP: str = "notification-service-group"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"

    @property
    def kafka_bootstrap_servers_list(self) -> list[str]:
        return [s.strip() for s in self.KAFKA_BOOTSTRAP_SERVERS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
