"""Tests for Kafka topics."""

from enum import StrEnum

from prototype_highly_loaded_distributed_service_utils.kafka import KafkaTopic
from prototype_highly_loaded_distributed_service_utils.kafka.topics import KafkaTopic as TopicFromModule


class TestKafkaTopic:
    """Tests for KafkaTopic enum."""

    def test_kafka_topic_is_str_enum(self) -> None:
        """KafkaTopic should be a StrEnum."""
        assert issubclass(KafkaTopic, StrEnum)

    def test_notifications_otp_value(self) -> None:
        """NOTIFICATIONS_OTP should have correct value."""
        assert KafkaTopic.NOTIFICATIONS_OTP == "notifications.otp"
        assert KafkaTopic.NOTIFICATIONS_OTP.value == "notifications.otp"

    def test_topic_can_be_used_as_string(self) -> None:
        """Topic should work as a string."""
        topic = KafkaTopic.NOTIFICATIONS_OTP
        assert f"Publishing to {topic}" == "Publishing to notifications.otp"
        assert topic + ".test" == "notifications.otp.test"

    def test_topic_string_comparison(self) -> None:
        """Topic should be equal to its string value."""
        assert KafkaTopic.NOTIFICATIONS_OTP == "notifications.otp"
        assert "notifications.otp" == KafkaTopic.NOTIFICATIONS_OTP

    def test_topic_in_collection(self) -> None:
        """Topic should work in collections."""
        topics_set = {KafkaTopic.NOTIFICATIONS_OTP}
        assert "notifications.otp" in topics_set
        assert KafkaTopic.NOTIFICATIONS_OTP in topics_set

    def test_all_topics_iterable(self) -> None:
        """Should be able to iterate over all topics."""
        all_topics = list(KafkaTopic)
        assert len(all_topics) >= 1
        assert KafkaTopic.NOTIFICATIONS_OTP in all_topics

    def test_topic_naming_convention(self) -> None:
        """All topics should follow naming convention: domain.event_type."""
        for topic in KafkaTopic:
            assert "." in topic.value, f"Topic {topic.name} should contain a dot"
            parts = topic.value.split(".")
            assert len(parts) >= 2, f"Topic {topic.name} should have at least 2 parts"
            assert all(part.islower() for part in parts), f"Topic {topic.name} should be lowercase"

    def test_import_from_kafka_module(self) -> None:
        """KafkaTopic should be importable from kafka module."""
        assert KafkaTopic is TopicFromModule

    def test_topic_members(self) -> None:
        """Should have expected members."""
        members = KafkaTopic.__members__
        assert "NOTIFICATIONS_OTP" in members


class TestKafkaTopicAllTopics:
    """Tests for KafkaTopic.all_topics() class method."""

    def test_all_topics_returns_list(self) -> None:
        """all_topics() should return a list."""
        result = KafkaTopic.all_topics()
        assert isinstance(result, list)

    def test_all_topics_returns_strings(self) -> None:
        """all_topics() should return list of strings."""
        result = KafkaTopic.all_topics()
        assert all(isinstance(topic, str) for topic in result)

    def test_all_topics_contains_all_enum_values(self) -> None:
        """all_topics() should contain all enum values."""
        result = KafkaTopic.all_topics()
        for topic in KafkaTopic:
            assert topic.value in result

    def test_all_topics_length_matches_enum(self) -> None:
        """all_topics() length should match number of enum members."""
        result = KafkaTopic.all_topics()
        assert len(result) == len(KafkaTopic)

    def test_all_topics_contains_notifications_otp(self) -> None:
        """all_topics() should contain notifications.otp."""
        result = KafkaTopic.all_topics()
        assert "notifications.otp" in result

    def test_all_topics_returns_values_not_names(self) -> None:
        """all_topics() should return values (e.g., 'notifications.otp'), not names (e.g., 'NOTIFICATIONS_OTP')."""
        result = KafkaTopic.all_topics()
        # Should contain values
        assert "notifications.otp" in result
        # Should not contain enum names
        assert "NOTIFICATIONS_OTP" not in result

    def test_all_topics_is_classmethod(self) -> None:
        """all_topics should be callable on the class, not instance."""
        # Can call on class
        result = KafkaTopic.all_topics()
        assert isinstance(result, list)

        # Can also call on instance (classmethod behavior)
        instance_result = KafkaTopic.NOTIFICATIONS_OTP.all_topics()
        assert result == instance_result
