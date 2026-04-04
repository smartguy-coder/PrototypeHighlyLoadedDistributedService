"""Tests for Kafka module exports."""

from prototype_highly_loaded_distributed_service_utils import kafka
from prototype_highly_loaded_distributed_service_utils.kafka import (
    KafkaTopic,
    NotificationChannel,
    OTPNotificationSchema,
)


class TestKafkaModuleExports:
    """Tests for kafka module public API."""

    def test_exports_kafka_topic(self) -> None:
        """KafkaTopic should be exported."""
        assert hasattr(kafka, "KafkaTopic")
        assert kafka.KafkaTopic is KafkaTopic

    def test_exports_notification_channel(self) -> None:
        """NotificationChannel should be exported."""
        assert hasattr(kafka, "NotificationChannel")
        assert kafka.NotificationChannel is NotificationChannel

    def test_exports_otp_notification_schema(self) -> None:
        """OTPNotificationSchema should be exported."""
        assert hasattr(kafka, "OTPNotificationSchema")
        assert kafka.OTPNotificationSchema is OTPNotificationSchema

    def test_all_contains_expected_exports(self) -> None:
        """__all__ should contain all public exports."""
        expected = {"KafkaTopic", "NotificationChannel", "OTPNotificationSchema"}
        assert expected.issubset(set(kafka.__all__))


class TestTopLevelExports:
    """Tests for top-level package exports."""

    def test_kafka_topic_from_top_level(self) -> None:
        """KafkaTopic should be importable from top level."""
        from prototype_highly_loaded_distributed_service_utils import KafkaTopic as TopLevelKafkaTopic

        assert TopLevelKafkaTopic is KafkaTopic

    def test_notification_channel_from_top_level(self) -> None:
        """NotificationChannel should be importable from top level."""
        from prototype_highly_loaded_distributed_service_utils import (
            NotificationChannel as TopLevelNotificationChannel,
        )

        assert TopLevelNotificationChannel is NotificationChannel

    def test_otp_schema_from_top_level(self) -> None:
        """OTPNotificationSchema should be importable from top level."""
        from prototype_highly_loaded_distributed_service_utils import (
            OTPNotificationSchema as TopLevelOTPSchema,
        )

        assert TopLevelOTPSchema is OTPNotificationSchema
