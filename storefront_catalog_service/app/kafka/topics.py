"""
Kafka topics registry.

All Kafka topic names should be defined here and exported via __all__.
This ensures consistency across producers and consumers, and allows
the create_kafka_topics management command to dynamically discover all topics.

Naming convention: <domain>.<event_type>
Examples:
    - notifications.otp

"""

# todo create python package

# Notifications domain
TOPIC_NOTIFICATIONS_OTP = "notifications.otp"


__all__ = [
    "TOPIC_NOTIFICATIONS_OTP",
]
