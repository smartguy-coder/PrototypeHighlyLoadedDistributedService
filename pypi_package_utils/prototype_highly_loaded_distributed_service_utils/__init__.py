"""
Prototype Highly Loaded Distributed Service Utils.

Shared utilities for microservices ecosystem.
"""

__version__ = "0.1.5"
__author__ = "Vasyl Kartychak"

from prototype_highly_loaded_distributed_service_utils.kafka import (
    KafkaTopic,
    NotificationChannel,
    OTPNotificationSchema,
)

__all__ = [
    # Kafka schemas
    "NotificationChannel",
    "OTPNotificationSchema",
    # Kafka topics
    "KafkaTopic",
]
