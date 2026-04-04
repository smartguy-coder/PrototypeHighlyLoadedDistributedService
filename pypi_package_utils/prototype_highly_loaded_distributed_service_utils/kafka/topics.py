"""
Kafka topics registry.

All Kafka topic names should be defined here as StrEnum.
This ensures consistency across producers and consumers in all services,
provides type safety, and enables IDE autocomplete.

Naming convention: <domain>.<event_type>
Examples:
    - notifications.otp
    - orders.created
    - inventory.updated

Usage:
    from prototype_highly_loaded_distributed_service_utils.kafka import KafkaTopic

    # As string (auto-converts)
    broker.subscriber(KafkaTopic.NOTIFICATIONS_OTP)

    # Get all topic names as list
    all_topics = KafkaTopic.all_topics()  # ["notifications.otp", ...]
"""

from enum import StrEnum


class KafkaTopic(StrEnum):
    """Kafka topic names for the microservices ecosystem."""

    # Notifications domain
    NOTIFICATIONS_OTP = "notifications.otp"

    @classmethod
    def all_topics(cls) -> list[str]:
        """
        Return a list of all topic names.

        Returns:
            List of topic name strings.

        Example:
            >>> KafkaTopic.all_topics()
            ['notifications.otp']
        """
        return [topic.value for topic in cls]


__all__ = [
    "KafkaTopic",
]
