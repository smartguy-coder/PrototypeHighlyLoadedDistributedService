"""
Management command to create and manage Kafka topics.

This command:
1. Creates all topics defined in KafkaTopic enum (from shared utils)
2. Checks and increases partition count if needed
3. Checks and updates retention settings if needed
4. Validates replication factor against cluster size

Usage:
    # Development (single broker)
    python manage.py create_kafka_topics --replication-factor 1

    # Production-like (3-broker cluster)
    python manage.py create_kafka_topics --partitions 3 --replication-factor 3

    # Interactive mode with SASL auth
    python manage.py create_kafka_topics --interactive --kafka-username admin --ask-kafka-password
"""

from argparse import ArgumentParser
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from confluent_kafka.admin import AdminClient, ConfigResource, NewTopic  # type: ignore[attr-defined]
from confluent_kafka.cimpl import NewPartitions
from prototype_highly_loaded_distributed_service_utils.kafka import KafkaTopic

# Configuration constants
CONFIG_NAME_RETENTION_MS = "retention.ms"
DEFAULT_PARTITIONS_COUNT = 3
DEFAULT_REPLICATION_FACTOR = 3  # For 3-broker cluster
DEFAULT_RETENTION_MS = 7 * 24 * 60 * 60 * 1000  # 7 days
DEFAULT_TOPIC_CONFIG = {CONFIG_NAME_RETENTION_MS: str(DEFAULT_RETENTION_MS)}


class Command(BaseCommand):
    help = "Create and manage Kafka topics defined in KafkaTopic enum"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--kafka-username",
            type=str,
            help="Override Kafka SASL username",
        )
        parser.add_argument(
            "--kafka-password",
            type=str,
            help="Kafka SASL password (for non-interactive mode)",
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            default=False,
            help="Run with confirmation prompts (default: non-interactive)",
        )
        parser.add_argument(
            "--partitions",
            type=int,
            default=DEFAULT_PARTITIONS_COUNT,
            help=f"Number of partitions for topics (default: {DEFAULT_PARTITIONS_COUNT})",
        )
        parser.add_argument(
            "--replication-factor",
            type=int,
            default=DEFAULT_REPLICATION_FACTOR,
            help=f"Replication factor for topics (default: {DEFAULT_REPLICATION_FACTOR})",
        )

    def get_kafka_config(self, options: dict[str, Any]) -> dict[str, Any]:
        """Build Kafka admin client configuration."""
        config = {"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS}

        # Add SASL configuration if provided
        if options.get("kafka_username"):
            config["sasl.username"] = options["kafka_username"]
            config["sasl.mechanism"] = "PLAIN"
            config["security.protocol"] = "SASL_PLAINTEXT"

        if options.get("kafka_password"):
            config["sasl.password"] = options["kafka_password"]

        return config

    def get_cluster_broker_count(self, admin: AdminClient) -> int:
        """Get the number of brokers in the cluster."""
        try:
            metadata = admin.list_topics(timeout=10)
            return len(metadata.brokers)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not get broker count: {e}"))
            return 1

    def handle(self, *args: Any, **options: Any) -> None:
        kafka_config = self.get_kafka_config(options)
        topic_names = KafkaTopic.all_topics()
        interactive = options.get("interactive", False)
        partitions = options.get("partitions", DEFAULT_PARTITIONS_COUNT)
        replication_factor = options.get("replication_factor", DEFAULT_REPLICATION_FACTOR)

        self.stdout.write(self.style.HTTP_INFO(f"Kafka: {kafka_config['bootstrap.servers']}"))

        try:
            admin = AdminClient(kafka_config)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to connect to Kafka: {e}"))
            return

        # Check cluster size
        broker_count = self.get_cluster_broker_count(admin)
        self.stdout.write("\nCluster info:")
        self.stdout.write(f"  • Brokers: {broker_count}")

        # Validate replication factor
        if replication_factor > broker_count:
            self.stdout.write(
                self.style.WARNING(f"\n⚠ Replication factor ({replication_factor}) > broker count ({broker_count})")
            )
            replication_factor = broker_count
            self.stdout.write(self.style.WARNING(f"  Adjusting replication factor to {replication_factor}"))

        self.stdout.write(f"\nTopics to manage ({len(topic_names)}):")
        for topic in KafkaTopic:
            self.stdout.write(f"  • {topic.name}: {topic.value}")

        self.stdout.write("\nSettings:")
        self.stdout.write(f"  • Partitions: {partitions}")
        self.stdout.write(f"  • Replication factor: {replication_factor}")
        self.stdout.write(
            f"  • Retention: {DEFAULT_RETENTION_MS}ms ({DEFAULT_RETENTION_MS // (24 * 60 * 60 * 1000)} days)"
        )

        if interactive:
            confirm = input("\nContinue? [y/n] ").strip().lower()
            if confirm != "y":
                self.stdout.write(self.style.WARNING("Aborted"))
                return

        # 1. Create topics
        self._create_topics(admin, topic_names, partitions, replication_factor)

        # 2. Check and fix partitions
        self._check_partitions(admin, topic_names, partitions, interactive)

        # 3. Check and fix retention
        self._check_retention(admin, topic_names, interactive)

        # 4. Show topic details
        self._show_topic_details(admin, topic_names)

        self.stdout.write(self.style.SUCCESS("\n✓ Done"))

    def _create_topics(
        self,
        admin: AdminClient,
        topic_names: list[str],
        partitions: int,
        replication_factor: int,
    ) -> None:
        """Create all topics that don't exist yet."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Creating topics ---"))

        new_topics = [
            NewTopic(
                topic,
                num_partitions=partitions,
                replication_factor=replication_factor,
                config=DEFAULT_TOPIC_CONFIG,
            )
            for topic in topic_names
        ]

        fs = admin.create_topics(new_topics)
        for topic, f in fs.items():
            try:
                f.result()
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {topic} created (partitions={partitions}, rf={replication_factor})")
                )
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower():
                    self.stdout.write(f"  • {topic} already exists")
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {topic}: {e}"))

    def _check_partitions(
        self,
        admin: AdminClient,
        topic_names: list[str],
        required_partitions: int,
        interactive: bool,
    ) -> None:
        """Check partition count and increase if needed."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Checking partitions ---"))

        try:
            server_topics = admin.list_topics().topics
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to list topics: {e}"))
            return

        need_increase = []

        for name in topic_names:
            if name not in server_topics:
                self.stdout.write(self.style.WARNING(f"  ⚠ {name}: not found on server"))
                continue

            count = len(server_topics[name].partitions)
            if count < required_partitions:
                self.stdout.write(self.style.WARNING(f"  ⚠ {name}: {count}/{required_partitions} partitions (TOO LOW)"))
                need_increase.append(name)
            elif count > required_partitions:
                self.stdout.write(f"  • {name}: {count} partitions (more than required, OK)")
            else:
                self.stdout.write(self.style.SUCCESS(f"  ✓ {name}: {count} partitions"))

        if not need_increase:
            return

        if interactive:
            confirm = input(f"\nIncrease partitions for {len(need_increase)} topics? [y/n] ").strip().lower()
            if confirm != "y":
                self.stdout.write(self.style.WARNING("  Skipped partition increase"))
                return

        new_partitions = [NewPartitions(name, required_partitions) for name in need_increase]
        resp = admin.create_partitions(new_partitions)

        for name, f in resp.items():
            try:
                f.result()
                self.stdout.write(self.style.SUCCESS(f"  ✓ {name}: partitions increased to {required_partitions}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ {name}: {e}"))

    def _check_retention(
        self,
        admin: AdminClient,
        topic_names: list[str],
        interactive: bool,
    ) -> None:
        """Check retention settings and update if needed."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Checking retention ---"))

        resources = [ConfigResource(ConfigResource.Type.TOPIC, name) for name in topic_names]

        try:
            fs = admin.describe_configs(resources)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to describe configs: {e}"))
            return

        need_change = []

        for resource, f in fs.items():
            try:
                config = f.result()
                retention = int(config[CONFIG_NAME_RETENTION_MS].value)

                retention_days = retention / (24 * 60 * 60 * 1000)
                required_days = DEFAULT_RETENTION_MS / (24 * 60 * 60 * 1000)

                if retention < DEFAULT_RETENTION_MS:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ {resource.name}: {retention_days:.1f} days (expected {required_days:.0f} days)"
                        )
                    )
                    need_change.append(resource.name)
                else:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {resource.name}: {retention_days:.1f} days"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ {resource.name}: {e}"))

        if not need_change:
            return

        if interactive:
            confirm = input(f"\nUpdate retention for {len(need_change)} topics? [y/n] ").strip().lower()
            if confirm != "y":
                self.stdout.write(self.style.WARNING("  Skipped retention update"))
                return

        new_configs = [ConfigResource(ConfigResource.Type.TOPIC, name, DEFAULT_TOPIC_CONFIG) for name in need_change]
        resp = admin.alter_configs(new_configs)

        for resource, f in resp.items():
            try:
                f.result()
                self.stdout.write(self.style.SUCCESS(f"  ✓ {resource.name}: retention updated"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ {resource.name}: {e}"))

    def _show_topic_details(
        self,
        admin: AdminClient,
        topic_names: list[str],
    ) -> None:
        """Show detailed information about created topics."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Topic Details ---"))

        try:
            metadata = admin.list_topics()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to get metadata: {e}"))
            return

        for name in topic_names:
            if name not in metadata.topics:
                continue

            topic = metadata.topics[name]
            partitions = len(topic.partitions)

            # Get replica info from first partition
            if topic.partitions:
                first_partition = topic.partitions[0]
                replicas = len(first_partition.replicas) if first_partition.replicas else 0
                leader = first_partition.leader
                isr = len(first_partition.isrs) if first_partition.isrs else 0

                status = "✓" if isr >= 2 else "⚠"
                self.stdout.write(
                    f"  {status} {name}: {partitions} partitions, rf={replicas}, leader={leader}, ISR={isr}"
                )
            else:
                self.stdout.write(f"  • {name}: {partitions} partitions")
