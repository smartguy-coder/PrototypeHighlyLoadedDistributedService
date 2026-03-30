# Apache Kafka

Apache Kafka is a distributed event streaming platform used for high-throughput, fault-tolerant messaging between services.

---

## Table of Contents

1. [Theory](#theory)
2. [Architecture](#architecture)
3. [Why KRaft (No Zookeeper)](#why-kraft-no-zookeeper)
4. [Why Confluent Images](#why-confluent-images)
5. [Key Concepts](#key-concepts)
6. [Serialization (Serde)](#serialization-serde)
7. [Schema Registry](#schema-registry)
8. [Our Implementation](#our-implementation)
9. [Configuration](#configuration)
10. [Usage Examples](#usage-examples)
11. [Monitoring](#monitoring)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

---

## Theory

### What is Kafka?

Kafka is a **distributed commit log** that provides:

- **Publish/Subscribe messaging** — Producers send messages, consumers read them
- **Message persistence** — Messages are stored on disk, not just in memory
- **Horizontal scaling** — Add more brokers to increase throughput
- **Fault tolerance** — Data is replicated across multiple brokers

### When to Use Kafka?

| Use Case | Kafka | Alternative |
|----------|-------|-------------|
| Event streaming | ✅ Best choice | — |
| High throughput (100k+ msg/sec) | ✅ Best choice | — |
| Message replay needed | ✅ Best choice | — |
| Simple task queue | ⚠️ Overkill | RabbitMQ, Redis |
| Real-time analytics | ✅ Best choice | — |
| Log aggregation | ✅ Best choice | ELK Stack |

### Kafka vs RabbitMQ

| Aspect | Kafka | RabbitMQ |
|--------|-------|----------|
| **Model** | Distributed log | Message queue |
| **Throughput** | Very high (millions/sec) | Moderate (tens of thousands/sec) |
| **Message retention** | Configurable (days/weeks) | Until consumed |
| **Replay** | ✅ Yes | ❌ No |
| **Ordering** | Per partition | Per queue |
| **Consumer model** | Pull | Push |
| **Complexity** | Higher | Lower |
| **Best for** | Event streaming | Task queues |

---

## Architecture

### KRaft Mode (Kafka without Zookeeper)

Starting with Kafka 3.5+, Kafka uses **KRaft** (Kafka Raft) mode for metadata management instead of Zookeeper. This simplifies the architecture and improves performance.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              Kafka KRaft Cluster (3 nodes)                              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  ┌─────────────────────────────┐
│  │      kafka-1 (Node 1)       │  │      kafka-2 (Node 2)       │  │      kafka-3 (Node 3)       │
│  │    Combined Broker+Ctrl     │  │    Combined Broker+Ctrl     │  │    Combined Broker+Ctrl     │
│  ├─────────────────────────────┤  ├─────────────────────────────┤  ├─────────────────────────────┤
│  │                             │  │                             │  │                             │
│  │  ┌───────────────────────┐  │  │  ┌───────────────────────┐  │  │  ┌───────────────────────┐  │
│  │  │     Controller        │  │  │  │     Controller        │  │  │  │     Controller        │  │
│  │  │     (Raft voter)      │◄─┼──┼─►│     (Raft voter)      │◄─┼──┼─►│     (Raft voter)      │  │
│  │  │     Port: 9093        │  │  │  │     Port: 9093        │  │  │  │     Port: 9093        │  │
│  │  └───────────────────────┘  │  │  └───────────────────────┘  │  │  └───────────────────────┘  │
│  │                             │  │                             │  │                             │
│  │  ┌───────────────────────┐  │  │  ┌───────────────────────┐  │  │  ┌───────────────────────┐  │
│  │  │       Broker          │  │  │  │       Broker          │  │  │  │       Broker          │  │
│  │  │   Internal: 9092      │  │  │  │   Internal: 9092      │  │  │  │   Internal: 9092      │  │
│  │  │   External: 29092     │  │  │  │   External: 29093     │  │  │  │   External: 29094     │  │
│  │  └───────────────────────┘  │  │  └───────────────────────┘  │  │  └───────────────────────┘  │
│  │                             │  │                             │  │                             │
│  │  ┌───────────────────────┐  │  │  ┌───────────────────────┐  │  │  ┌───────────────────────┐  │
│  │  │     Partitions        │  │  │  │     Partitions        │  │  │  │     Partitions        │  │
│  │  │  ┌─────┬─────┬─────┐  │  │  │  │  ┌─────┬─────┬─────┐  │  │  │  ┌─────┬─────┬─────┐  │  │
│  │  │  │ P0  │ P1  │ P2  │  │  │  │  │  │ P0  │ P1  │ P2  │  │  │  │  │ P0  │ P1  │ P2  │  │  │
│  │  │  │ LDR │ FLW │ FLW │  │  │  │  │  │ FLW │ LDR │ FLW │  │  │  │  │ FLW │ FLW │ LDR │  │  │
│  │  │  └─────┴─────┴─────┘  │  │  │  │  └─────┴─────┴─────┘  │  │  │  └─────┴─────┴─────┘  │  │
│  │  └───────────────────────┘  │  │  └───────────────────────┘  │  │  └───────────────────────┘  │
│  │                             │  │                             │  │                             │
│  └─────────────────────────────┘  └─────────────────────────────┘  └─────────────────────────────┘
│                                                                                         │
│  Legend: LDR = Leader, FLW = Follower                                                   │
│  Each partition has 1 leader + 2 followers (replication-factor = 3)                     │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                    │                          │                          │
                    │                          │                          │
┌───────────────────▼──────────────────────────▼──────────────────────────▼───────────────┐
│                                     Data Flow                                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   ┌──────────────┐         Writes go to partition leaders                               │
│   │   Producer   │─────────────────────────────────────────────────────┐                │
│   │  (Django)    │                                                     │                │
│   └──────────────┘                                                     │                │
│          │                                                             │                │
│          │  key="user123" ──► hash(key) % 3 = partition               │                │
│          │                                                             │                │
│          ├────────────────────► P0 Leader (kafka-1)                    │                │
│          ├────────────────────► P1 Leader (kafka-2)                    │                │
│          └────────────────────► P2 Leader (kafka-3)                    │                │
│                                                                        │                │
│                   Leaders replicate to followers                       │                │
│                   (min.insync.replicas = 2)                            │                │
│                                                                        ▼                │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                              │
│   │  Consumer 1  │    │  Consumer 2  │    │  Consumer 3  │  Consumer Group              │
│   │  (reads P0)  │    │  (reads P1)  │    │  (reads P2)  │  "notification-service"      │
│   └──────────────┘    └──────────────┘    └──────────────┘                              │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Roles

| Component | Role | Our Setup |
|-----------|------|-----------|
| **Controller** | Cluster metadata, leader election (via Raft) | Built into each broker |
| **Broker** | Stores and serves messages | 3 instances (combined mode) |
| **Producer** | Sends messages to topics | Django app |
| **Consumer** | Reads messages from topics | Notification service |
| **Schema Registry** | Manages message schemas | ❌ Not used (we use Pydantic + JSON) |

### Listeners Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         kafka-1                                 │
├─────────────────────────────────────────────────────────────────┤
│  CONTROLLER (9093)  │  Used for Raft quorum between controllers │
│  INTERNAL (9092)    │  Inter-broker + internal services         │
│  EXTERNAL (29092)   │  Host machine access (localhost)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why KRaft (No Zookeeper)

### The Problem with Zookeeper

Historically, Kafka relied on Apache Zookeeper for:

- Storing cluster metadata (topics, partitions, replicas)
- Controller election (which broker manages partition leaders)
- Broker membership tracking

**This caused several problems:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Zookeeper Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐                │
│   │ Kafka-1  │     │ Kafka-2  │     │ Kafka-3  │                │
│   └────┬─────┘     └────┬─────┘     └────┬─────┘                │
│        │                │                │                      │
│        └────────────────┼────────────────┘                      │
│                         │                                       │
│                         ▼                                       │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐                │
│   │   ZK-1   │◄───►│   ZK-2   │◄───►│   ZK-3   │                │
│   └──────────┘     └──────────┘     └──────────┘                │
│                                                                 │
│   Problems:                                                     │
│   • 6 containers instead of 3                                   │
│   • Two different systems to monitor                            │
│   • Dual failure modes                                          │
│   • Metadata sync bottleneck (~200k partitions max)             │
│   • Slow controller failover (seconds to minutes)               │
└─────────────────────────────────────────────────────────────────┘
```

### The KRaft Solution

KRaft (Kafka Raft) moves metadata management **inside Kafka itself**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      KRaft Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│   │     Kafka-1      │  │     Kafka-2      │  │    Kafka-3     ││
│   │  ┌────────────┐  │  │  ┌────────────┐  │  │ ┌────────────┐ ││
│   │  │ Controller │◄─┼──┼─►│ Controller │◄─┼──┼─► Controller │ ││
│   │  └────────────┘  │  │  └────────────┘  │  │ └────────────┘ ││
│   │  ┌────────────┐  │  │  ┌────────────┐  │  │ ┌────────────┐ ││
│   │  │   Broker   │  │  │  │   Broker   │  │  │ │   Broker   │ ││
│   │  └────────────┘  │  │  └────────────┘  │  │ └────────────┘ ││
│   └──────────────────┘  └──────────────────┘  └────────────────┘│
│            ▲                     ▲                    ▲         │
│            └─────────────────────┴────────────────────┘         │
│                         Raft Consensus                          │
│                                                                 │
│   Benefits:                                                     │
│   • 3 containers instead of 6                                   │
│   • Single system to monitor                                    │
│   • Faster failover (milliseconds)                              │
│   • Millions of partitions supported                            │
│   • Simpler operations                                          │
└─────────────────────────────────────────────────────────────────┘
```

### KRaft vs Zookeeper Comparison

| Aspect | KRaft Mode | Zookeeper Mode |
|--------|------------|----------------|
| **Containers needed** | 3 (Kafka only) | 6+ (Kafka + ZK) |
| **Metadata storage** | Internal Raft log | External Zookeeper |
| **Startup time** | ~10-15 seconds | ~30-60 seconds |
| **Controller failover** | Milliseconds | Seconds to minutes |
| **Max partitions** | Millions | ~200,000 |
| **Operational complexity** | Lower | Higher |
| **Memory overhead** | Less (1 JVM per node) | More (2 JVMs per node) |
| **Debugging** | Single log source | Two log sources |
| **Status (2024+)** | ✅ Production ready | ⚠️ Deprecated |

### Our KRaft Configuration

```yaml
# Combined mode: each node is both broker AND controller
KAFKA_PROCESS_ROLES: broker,controller

# Raft quorum voters (all 3 nodes participate)
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-1:9093,2@kafka-2:9093,3@kafka-3:9093

# Cluster ID (must be same across all nodes)
CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
```

**Why combined mode?** For small clusters (3-5 nodes), running broker and controller on the same node is efficient. For large clusters (50+ nodes), you might separate them.

---

## Why Confluent Images

### The Image Size Problem

When you run `docker pull`, you might notice Confluent images are **large**:

| Image | Size | Notes |
|-------|------|-------|
| `confluentinc/cp-kafka:7.6.0` | ~1.5 GB | Full Confluent Platform |
| `bitnami/kafka:latest` | ~500 MB | Minimal Kafka |
| `apache/kafka:latest` | ~400 MB | Official Apache |

**Total for our 3-broker cluster:**
- Confluent: ~4.5 GB
- Alternatives: ~1.5 GB

### Why We Still Use Confluent (Despite Size)

#### 1. Production-Grade Stability

```
Confluent images are used by:
• LinkedIn (invented Kafka)
• Netflix, Uber, Airbnb
• Most Fortune 500 companies

They are the de-facto standard for production Kafka.
```

#### 2. Better Documentation

Every configuration option, every error message, every edge case is documented. When you Google a Kafka error, 90% of answers assume Confluent images.

#### 3. Consistent Environment Variables

```yaml
# Confluent: predictable pattern
KAFKA_BROKER_ID: 1
KAFKA_LISTENERS: ...
KAFKA_ADVERTISED_LISTENERS: ...

# Bitnami: different prefix
KAFKA_CFG_NODE_ID: 1
KAFKA_CFG_LISTENERS: ...
```

#### 4. Built-in Tooling

Confluent images include all Kafka CLI tools:

```bash
# These just work:
docker exec kafka-1 kafka-topics --list ...
docker exec kafka-1 kafka-console-producer ...
docker exec kafka-1 kafka-consumer-groups ...
docker exec kafka-1 kafka-metadata ...
```

### What Makes Confluent Images Large?

```
┌─────────────────────────────────────────────────────────────────┐
│                 Confluent Image Contents (~1.5GB)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐                                        │
│  │   Base OS (Ubuntu)  │  ~150 MB                               │
│  └─────────────────────┘                                        │
│  ┌─────────────────────┐                                        │
│  │   Full JDK 17       │  ~400 MB  (not JRE!)                   │
│  └─────────────────────┘                                        │
│  ┌─────────────────────┐                                        │
│  │   Apache Kafka      │  ~100 MB                               │
│  └─────────────────────┘                                        │
│  ┌─────────────────────┐                                        │
│  │   Confluent libs    │  ~300 MB                               │
│  │   • Monitoring      │                                        │
│  │   • Security        │                                        │
│  │   • Connectors      │                                        │
│  └─────────────────────┘                                        │
│  ┌─────────────────────┐                                        │
│  │   CLI Tools         │  ~50 MB                                │
│  └─────────────────────┘                                        │
│  ┌─────────────────────┐                                        │
│  │   Docs & Configs    │  ~100 MB                               │
│  └─────────────────────┘                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Trade-offs Summary

| Aspect | Confluent | Bitnami/Apache |
|--------|-----------|----------------|
| **Image size** | ❌ Large (~1.5GB) | ✅ Small (~500MB) |
| **Pull time** | ❌ Slow (first time) | ✅ Fast |
| **Disk usage** | ❌ ~4.5GB total | ✅ ~1.5GB total |
| **Documentation** | ✅ Excellent | ⚠️ Limited |
| **Production use** | ✅ Industry standard | ⚠️ Less common |
| **Debugging** | ✅ Well-known | ⚠️ Harder to Google |
| **Tooling** | ✅ All included | ⚠️ May need extras |
| **KRaft support** | ✅ Stable | ⚠️ Varies |
| **Tag stability** | ✅ Versioned tags work | ❌ Tags often missing |

### Our Decision

> **We prioritize reliability over disk space.**
>
> For a production-like development environment, the extra ~3GB is worth:
> - Not debugging obscure image-specific issues
> - Having all CLI tools available
> - Following the same setup as production systems
> - Finding answers quickly when things break

**If disk space is critical**, you can try:

```yaml
# Alternative (lighter, but less tested)
image: apache/kafka:3.7.0
```

But be prepared to adjust environment variables and troubleshoot independently.

---

## Key Concepts

### Topics and Partitions

A **topic** is a category/feed name to which messages are published.

A **partition** is an ordered, immutable sequence of messages within a topic.

```
Topic: notifications.otp
├── Partition 0: [msg1, msg4, msg7, ...]  → Consumer 1
├── Partition 1: [msg2, msg5, msg8, ...]  → Consumer 2
└── Partition 2: [msg3, msg6, msg9, ...]  → Consumer 3
```

**Why partitions matter:**

- **Parallelism** — Multiple consumers can read in parallel
- **Ordering** — Messages within a partition are ordered
- **Scalability** — More partitions = higher throughput

### Replication

Each partition is replicated across multiple brokers for fault tolerance.

```
Partition 0:
├── Broker 1: LEADER   (handles all reads/writes)
├── Broker 2: Follower (replicates from leader)
└── Broker 3: Follower (replicates from leader)
```

**Key settings:**

| Setting | Description | Our Value |
|---------|-------------|-----------|
| `replication.factor` | Number of copies | 3 |
| `min.insync.replicas` | Min replicas for acks | 2 |
| `acks` | Producer acknowledgment | all |

### Consumer Groups

Consumers with the same `group.id` share the workload:

```
Consumer Group: notification-service
├── Consumer 1 → Partition 0
├── Consumer 2 → Partition 1
└── Consumer 3 → Partition 2
```

**Rules:**

- One partition → One consumer (within a group)
- If consumers > partitions, some consumers are idle
- If partitions > consumers, some consumers handle multiple partitions

### Offsets

An **offset** is a unique identifier for each message within a partition.

```
Partition 0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                          ↑
                    Current offset = 5
                    (Consumer has processed 0-4)
```

**Offset management:**

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Auto commit | Kafka commits periodically | Simple consumers |
| Manual commit | App commits after processing | At-least-once |
| Transactional | Exactly-once semantics | Critical data |

---

## Serialization (Serde)

### What is Serde?

**Serde** = **Ser**ializer + **De**serializer

Kafka stores messages as raw **bytes** (`byte[]`). To write an object to Kafka and read it back, you need:

1. **Serializer** — Converts object → bytes (when producing)
2. **Deserializer** — Converts bytes → object (when consuming)

Together they form a **Serde**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Message Flow with Serde                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Producer                    Kafka                   Consumer  │
│   ┌──────────┐              ┌───────┐              ┌──────────┐ │
│   │ Python   │  serialize   │ Bytes │  deserialize │ Python   │ │
│   │  dict    │ ──────────►  │ [...] │ ──────────►  │  dict    │ │
│   └──────────┘              └───────┘              └──────────┘ │
│                                                                 │
│   {"phone": "+380..."}  →  [0x7B, 0x22, ...]  →  {"phone": ...} │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Types of Serde

| Serde | Format | Size | Schema Required | Use Case |
|-------|--------|------|-----------------|----------|
| **String** | Text (UTF-8) | Large | ❌ No | Simple cases, JSON as text |
| **JSON** | JSON text | Large | Optional | Human-readable, flexible |
| **Avro** | Binary | Small | ✅ Yes (Schema Registry) | Production, high throughput |
| **Protobuf** | Binary | Small | ✅ Yes (Schema Registry) | gRPC compatibility |

### Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    Same Message, Different Serdes               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Original data:                                                 │
│  {"phone": "+380501234567", "code": "1234", "channel": "sms"}   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ String/JSON Serde                                           ││
│  │ Size: 58 bytes                                              ││
│  │ {"phone":"+380501234567","code":"1234","channel":"sms"}     ││
│  │                                                             ││
│  │ ✅ Human-readable                                           ││
│  │ ✅ No schema needed                                         ││
│  │ ❌ Larger size                                              ││
│  │ ❌ No type validation                                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Avro Serde                                                  ││
│  │ Size: 24 bytes (59% smaller!)                               ││
│  │ [binary data - not human readable]                          ││
│  │                                                             ││
│  │ ✅ Compact binary format                                    ││
│  │ ✅ Schema validation                                        ││
│  │ ✅ Schema evolution support                                 ││
│  │ ❌ Requires Schema Registry                                 ││
│  │ ❌ Not human-readable                                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Our Approach: JSON with Pydantic

We use **JSON serialization** (String serde) with **Pydantic validation**:

```python
# Producer side
from pydantic import BaseModel

class OTPNotification(BaseModel):
    phone: str
    secret_code: str
    channel: str

# Serialize
data = OTPNotification(phone="+380...", secret_code="1234", channel="sms")
message = data.model_dump_json()  # → '{"phone":"+380...","secret_code":"1234",...}'
producer.produce(value=message.encode("utf-8"))  # → bytes
```

```python
# Consumer side
raw_bytes = message.value()  # bytes from Kafka
json_str = raw_bytes.decode("utf-8")  # → JSON string
data = json.loads(json_str)  # → Python dict
notification = OTPNotification.model_validate(data)  # → validated object
```

### Why Not Avro (Yet)?

| Aspect | Our JSON Approach | Avro |
|--------|-------------------|------|
| **Setup complexity** | Simple | Requires Schema Registry |
| **Debugging** | Easy (human-readable) | Hard (binary) |
| **Message size** | Larger | 40-60% smaller |
| **Schema evolution** | Manual | Automatic |
| **Type safety** | Via Pydantic | Native |

**For a learning project**, JSON is easier to debug and understand. For high-volume production, consider Avro.

### Kafka UI and Serde

When you see **"Value Serde: Fallback"** warning in Kafka UI:

```
┌─────────────────────────────────────────────────────────────────┐
│  Kafka UI attempts to deserialize messages automatically:       │
│                                                                 │
│  1. Try Avro  → No magic bytes found  → ❌                      │
│  2. Try Protobuf → Not valid protobuf → ❌                      │
│  3. Try JSON Schema → Not registered  → ❌                      │
│  4. Fallback → Show as raw text       → ⚠️ Warning shown        │
│                                                                 │
│  This is NOT an error! Messages are fine.                       │
│  UI just doesn't know the format.                               │
└─────────────────────────────────────────────────────────────────┘
```

**Fix:** Configure default serde in docker-compose:

```yaml
kafka-ui:
  environment:
    # Tell UI to use String serde (our JSON messages are strings)
    KAFKA_CLUSTERS_0_DEFAULTKEYSERDE: String
    KAFKA_CLUSTERS_0_DEFAULTVALUESERDE: String
```

### Future: Migration to Avro

When ready for production, consider Avro:

```python
# With Avro (future implementation)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_registry = SchemaRegistryClient({"url": "http://schema-registry:8081"})

avro_schema = """
{
  "type": "record",
  "name": "OTPNotification",
  "fields": [
    {"name": "phone", "type": "string"},
    {"name": "secret_code", "type": "string"},
    {"name": "channel", "type": "string"}
  ]
}
"""

serializer = AvroSerializer(schema_registry, avro_schema)
producer.produce(value=serializer(data, ctx))
```

**Benefits of Avro:**

- Smaller messages (binary format)
- Schema Registry ensures compatibility
- Automatic schema evolution
- Type validation at Kafka level

---

## Schema Registry

### What is Schema Registry?

**Schema Registry** is a centralized service for storing and versioning data schemas (typically Avro, JSON Schema, or Protobuf) used in Kafka.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Schema Registry Architecture                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Producer                Schema Registry              Consumer │
│   ┌──────────┐           ┌─────────────┐           ┌──────────┐ │
│   │ Message  │           │   Schemas   │           │ Message  │ │
│   │ + Schema │──────────►│   v1, v2,   │◄──────────│ + Schema │ │
│   │   ID     │  register │   v3...     │  lookup   │   ID     │ │
│   └──────────┘           └─────────────┘           └──────────┘ │
│        │                       │                        ▲       │
│        │    ┌──────────────────┘                        │       │
│        │    │  Validates compatibility                  │       │
│        ▼    ▼                                           │       │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                      Kafka Broker                       │   │
│   │  Message = [Schema ID (4 bytes)] + [Avro Binary Data]   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Responsibilities

| Function | Description |
|----------|-------------|
| **Schema Storage** | Centralized repository of all schema versions |
| **Schema Versioning** | Automatic versioning on changes (v1 → v2 → v3) |
| **Compatibility Validation** | Validates new schema compatibility with previous versions |
| **Schema ID Assignment** | Each schema gets a unique ID |
| **Serialization Optimization** | Messages contain only 4-byte schema ID instead of full schema |

### Compatibility Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compatibility Types                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BACKWARD (default)                                             │
│  ─────────────────                                              │
│  New schema can READ data written by old schema                 │
│  ✅ Add optional fields                                         │
│  ✅ Remove fields with defaults                                 │
│  ❌ Add required fields                                         │
│                                                                 │
│  Example: Consumer v2 can read Producer v1 messages             │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  FORWARD                                                        │
│  ───────                                                        │
│  Old schema can READ data written by new schema                 │
│  ✅ Add fields with defaults                                    │
│  ✅ Remove optional fields                                      │
│  ❌ Remove required fields                                      │
│                                                                 │
│  Example: Consumer v1 can read Producer v2 messages             │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  FULL                                                           │
│  ────                                                           │
│  Both BACKWARD and FORWARD compatible                           │
│  Most restrictive, safest for production                        │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  NONE                                                           │
│  ────                                                           │
│  No compatibility checking (dangerous!)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Our Setup: No Schema Registry

We **do not use Schema Registry**. Instead, we use **Pydantic + JSON** for message serialization:

| Aspect | Schema Registry + Avro | Our Approach (Pydantic + JSON) |
|--------|------------------------|--------------------------------|
| **Status** | ❌ Not deployed | ✅ Actively used |
| **Schema Format** | Avro/Protobuf (binary) | Pydantic models (Python-native) |
| **Message Format** | Schema ID + binary data | JSON (human-readable) |
| **Schema Versioning** | Centralized registry | Git + code versioning |
| **Validation** | At Kafka level | At producer/consumer side |
| **Debugging** | Difficult (binary format) | Easy (readable in Kafka UI) |
| **Language Support** | Multi-language (Java, Go, Python) | Python-first |

**Why we chose Pydantic + JSON:**

1. **Learning project** — JSON is easier to debug and understand
2. **Python-only services** — no need for cross-language schema sharing
3. **Kafka UI readability** — messages are human-readable without special tools
4. **Simpler infrastructure** — no extra service to maintain

### Our Alternative: Shared Pydantic Schemas

Instead of Schema Registry we define schemas in code:

```python
# kafka/schemas.py
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Self

class OTPNotification(BaseModel):
    """Schema for OTP notification messages."""

    phone: str | None = None
    email: str | None = None
    secret_code: str = Field(..., min_length=4, max_length=4)
    verification_code: str = Field(..., min_length=6, max_length=6)
    channel: NotificationChannel
    expires_at: datetime

    @model_validator(mode="after")
    def validate_recipient(self) -> Self:
        if self.phone is None and self.email is None:
            raise ValueError("At least one of 'phone' or 'email' must be provided")
        return self
```

For multi-service architectures, schemas can be shared via a **pip package**:

```bash
# Producer service
pip install shared-schemas==1.2.0

# Consumer service
pip install shared-schemas==1.2.0

# Both use the same schema version!
```

### When TO Use Schema Registry ✅

Schema Registry makes sense when:

| Scenario | Why Schema Registry Helps |
|----------|---------------------------|
| **Multi-language teams** | Java producer, Go consumer, Python analytics — all read the same schema |
| **High message volume** | Avro is 40-60% smaller than JSON → saves bandwidth/storage |
| **Strict compatibility** | Automatic validation that new schema won't break consumers |
| **Enterprise compliance** | Audit trail of all schema changes |
| **Large payload** | Binary Avro is much more efficient for large objects |
| **Schema evolution** | Automatic versioning without manual control |

### Schema Registry vs Pydantic: Decision Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    When to Use What?                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Use Schema Registry + Avro when:                               │
│  ✅ Multiple teams with different languages                     │
│  ✅ Very high throughput (millions msg/sec)                     │
│  ✅ Large messages (KB to MB)                                   │
│  ✅ Need guaranteed schema compatibility                        │
│  ✅ Enterprise/regulated environment                            │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  Use Pydantic + JSON when:                                      │
│  ✅ Python-only or Python-primary stack                         │
│  ✅ Small to medium throughput                                  │
│  ✅ Need easy debugging (human-readable)                        │
│  ✅ Want simpler infrastructure                                 │
│  ✅ Learning/prototype project                                  │
│  ✅ Schema changes are infrequent                               │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  Our project: Pydantic + JSON ✓                                 │
│  • Python-only services                                         │
│  • Learning project (easy debugging important)                  │
│  • Simpler ops (no extra service to maintain)                   │
│  • Schema versioning via code                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### If You Need Schema Registry Later

Migration from JSON to Avro:

```python
# Step 1: Add Schema Registry to docker-compose.yml
schema-registry:
  image: confluentinc/cp-schema-registry:7.6.0
  environment:
    SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka-1:9092
    SCHEMA_REGISTRY_HOST_NAME: schema-registry
  ports:
    - "8081:8081"

# Step 2: Define Avro schema
avro_schema = """
{
  "type": "record",
  "name": "OTPNotification",
  "namespace": "com.example.notifications",
  "fields": [
    {"name": "phone", "type": ["null", "string"], "default": null},
    {"name": "email", "type": ["null", "string"], "default": null},
    {"name": "secret_code", "type": "string"},
    {"name": "verification_code", "type": "string"},
    {"name": "channel", "type": "string"},
    {"name": "expires_at", "type": "long", "logicalType": "timestamp-millis"}
  ]
}
"""

# Step 3: Use Avro serializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_registry = SchemaRegistryClient({"url": "http://schema-registry:8081"})
serializer = AvroSerializer(schema_registry, avro_schema)

# Step 4: Produce with Avro
producer.produce(
    topic="notifications.otp",
    value=serializer(data, SerializationContext(topic, MessageField.VALUE)),
)
```

---

## Our Implementation

### Project Structure

```
storefront_catalog_service/app/
├── kafka/
│   ├── __init__.py      # Public API exports
│   ├── topics.py        # Topic name constants
│   ├── schemas.py       # Pydantic message schemas
│   ├── producer.py      # BaseKafkaProducer class
│   ├── producers.py     # Singleton producer instances
│   └── services.py      # High-level functions
└── settings/
    └── settings_kafka.py # Configuration
```

### Topics Registry

All topics are defined in `kafka/topics.py`:

```python
# Notifications domain
TOPIC_NOTIFICATIONS_OTP = "notifications.otp"
TOPIC_NOTIFICATIONS_EMAIL = "notifications.email"
TOPIC_NOTIFICATIONS_SMS = "notifications.sms"

# User domain
TOPIC_USER_REGISTERED = "user.registered"
TOPIC_USER_UPDATED = "user.updated"
TOPIC_USER_DELETED = "user.deleted"
```

**Naming convention:** `<domain>.<event_type>`

### Message Schemas

We use Pydantic for type-safe message validation:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class NotificationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"

class OTPNotification(BaseModel):
    phone: str | None = None
    email: str | None = None
    secret_code: str = Field(..., min_length=4, max_length=6)
    verification_code: str = Field(..., min_length=6, max_length=6)
    channel: NotificationChannel
    expires_at: datetime
```

### Producer Implementation

#### Base Producer Class

```python
from confluent_kafka import Producer
from pydantic import BaseModel

class BaseKafkaProducer:
    topic: str
    schema: type[BaseModel]

    def publish(
        self,
        data: dict | BaseModel,
        key: str | None = None,
        headers: dict | None = None,
        flush: bool = False,
    ) -> None:
        # 1. Validate with Pydantic schema
        validated = self.schema.model_validate(data)

        # 2. Serialize to JSON (String serde)
        message = validated.model_dump_json()

        # 3. Send to Kafka (async)
        self.producer.produce(
            topic=self.topic,
            value=message.encode("utf-8"),
            key=key.encode("utf-8") if key else None,
            callback=self._delivery_callback,
        )

        # 4. Trigger delivery
        self.producer.poll(0)

        # 5. Optional: wait for confirmation
        if flush:
            self.producer.flush()
```

#### Singleton Producers

```python
# kafka/producers.py
class OTPNotificationProducer(BaseKafkaProducer):
    topic = TOPIC_NOTIFICATIONS_OTP
    schema = OTPNotification

# Create singleton (lazy initialization)
otp_notification_producer = create_producer(OTPNotificationProducer)
```

### High-Level Services

For clean separation, we provide service functions:

```python
# kafka/services.py
from kafka.producers import otp_notification_producer
from core.utils import get_client_ip, get_user_agent

def send_otp_notification(
    verification_code: str,
    secret_code: str,
    expires_at: datetime,
    email: str | None = None,
    phone: str | None = None,
) -> bool:
    """Send OTP via Kafka. Returns True on success."""

    notification_data = {
        "email": email,
        "phone": phone,
        "secret_code": secret_code,
        "verification_code": verification_code,
        "channel": "email" if email else "sms",
        "expires_at": expires_at,
    }

    try:
        otp_notification_producer.publish(
            data=notification_data,
            key=email or phone,
            flush=True,  # Ensure delivery
        )
        return True
    except KafkaPublisherException:
        logger.exception("Failed to publish OTP")
        return False
```

### Usage in Application

```python
# In serializers.py or views.py
from kafka.services import send_otp_notification

class OTPRequestSerializer(serializers.Serializer):
    def create(self, validated_data):
        otp, secret_code = OTPCode.create_otp(...)

        # Send to Kafka (with flush for guaranteed delivery)
        send_otp_notification(
            verification_code=otp.verification_code,
            secret_code=secret_code,
            expires_at=otp.expires_at,
            phone=validated_data["phone"],
        )

        return {"verification_code": otp.verification_code}
```

---

## Configuration

### Docker Compose (3-Node KRaft Cluster)

```yaml
x-kafka-env-common: &kafka-env-common
  # KRaft mode settings (no Zookeeper!)
  KAFKA_PROCESS_ROLES: broker,controller
  KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
  KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-1:9093,2@kafka-2:9093,3@kafka-3:9093
  CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
  # Listeners
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT
  KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
  # Cluster settings
  KAFKA_DEFAULT_REPLICATION_FACTOR: 3
  KAFKA_MIN_INSYNC_REPLICAS: 2
  KAFKA_NUM_PARTITIONS: 3
  KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"

services:
  kafka-1:
    image: confluentinc/cp-kafka:7.6.0  # Large but stable
    environment:
      <<: *kafka-env-common
      KAFKA_NODE_ID: 1
      KAFKA_LISTENERS: CONTROLLER://0.0.0.0:9093,INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:29092
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka-1:9092,EXTERNAL://localhost:29092
    ports:
      - "29092:29092"
    volumes:
      - kafka-1-data:/var/lib/kafka/data

  # kafka-2 and kafka-3 similar...
```

### Django Settings

```python
# settings/settings_kafka.py

# All brokers use the same INTERNAL port (9092)
KAFKA_BOOTSTRAP_SERVERS = "kafka-1:9092,kafka-2:9092,kafka-3:9092"

KAFKA_PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "acks": "all",                    # Wait for all replicas
    "retries": 3,                     # Retry on failure
    "enable.idempotence": True,       # Exactly-once
    "compression.type": "lz4",        # Compress messages
    "linger.ms": 5,                   # Batch for 5ms
}
```

### Environment Variables

```bash
# .env file

# For container-to-container communication:
KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9092,kafka-3:9092

# For local development OUTSIDE Docker:
# KAFKA_BOOTSTRAP_SERVERS=localhost:29092,localhost:29093,localhost:29094
```

### Topic Creation

```bash
# Via management command
python manage.py create_kafka_topics \
    --partitions 3 \
    --replication-factor 3
```

---

## Usage Examples

### Sending a Message

```python
from kafka.services import send_otp_notification

# Simple usage
send_otp_notification(
    verification_code="123456",
    secret_code="1234",
    expires_at=datetime.utcnow() + timedelta(minutes=5),
    phone="+380501234567",
)

# With request metadata
send_otp_notification(
    verification_code="123456",
    secret_code="1234",
    expires_at=otp.expires_at,
    email="user@example.com",
    ip_address=get_client_ip(request),
    user_agent=get_user_agent(request),
)
```

### Low-Level Producer Access

```python
from kafka.producers import otp_notification_producer

# Custom message with headers
otp_notification_producer.publish(
    data={
        "phone": "+380501234567",
        "secret_code": "1234",
        "verification_code": "123456",
        "channel": "sms",
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
    },
    key="+380501234567",
    headers={
        "source": "api-v1",
        "trace_id": "abc-123",
    },
    flush=True,
)
```

### Creating a New Producer

```python
# 1. Define schema in kafka/schemas.py
class OrderCreated(BaseModel):
    order_id: int
    user_id: int
    total: Decimal
    items: list[OrderItem]
    created_at: datetime

# 2. Add topic in kafka/topics.py
TOPIC_ORDER_CREATED = "order.created"

# 3. Create producer in kafka/producers.py
class OrderCreatedProducer(BaseKafkaProducer):
    topic = TOPIC_ORDER_CREATED
    schema = OrderCreated

order_created_producer = create_producer(OrderCreatedProducer)

# 4. Add service function in kafka/services.py
def publish_order_created(order: Order) -> bool:
    return order_created_producer.publish({
        "order_id": order.id,
        "user_id": order.user_id,
        "total": order.total,
        "items": [item.to_dict() for item in order.items],
        "created_at": order.created_at,
    }, flush=True)
```

---

## Monitoring

### Kafka UI

Access at: **http://localhost:7001**

Features:

- View all brokers and their status
- Browse topics and messages
- Monitor consumer groups and lag
- View partition distribution
- **KRaft mode:** Shows controller quorum status

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| **Under-replicated partitions** | Partitions with fewer replicas than configured | > 0 |
| **Offline partitions** | Partitions without a leader | > 0 |
| **Consumer lag** | Messages behind real-time | > 1000 |
| **Request latency** | Time to process requests | > 100ms |
| **Disk usage** | Broker disk space | > 80% |
| **Controller quorum** | Raft quorum health | < 2 voters |

### Checking Cluster Health

```bash
# List all topics
docker compose exec kafka-1 kafka-topics \
    --bootstrap-server kafka-1:9092 \
    --list

# Describe a topic
docker compose exec kafka-1 kafka-topics \
    --bootstrap-server kafka-1:9092 \
    --describe \
    --topic notifications.otp

# Check cluster metadata (KRaft)
docker compose exec kafka-1 kafka-metadata \
    --snapshot /var/lib/kafka/data/__cluster_metadata-0/00000000000000000000.log \
    --command "cat"

# Check consumer group lag
docker compose exec kafka-1 kafka-consumer-groups \
    --bootstrap-server kafka-1:9092 \
    --describe \
    --group notification-service
```

---

## Troubleshooting

### Common Issues

#### 1. "No brokers available"

**Cause:** Producer can't connect to Kafka.

**Solution:**
```bash
# Check if brokers are running
docker compose ps kafka-1 kafka-2 kafka-3

# Check broker logs
docker compose logs kafka-1

# Verify bootstrap servers in settings
echo $KAFKA_BOOTSTRAP_SERVERS
```

#### 2. "NOT_ENOUGH_REPLICAS"

**Cause:** `min.insync.replicas` > available replicas for the topic.

**Solution:**
```bash
# Check topic replication factor
docker compose exec kafka-1 kafka-topics \
    --bootstrap-server kafka-1:9092 \
    --describe \
    --topic notifications.otp

# If RF=1 but min.insync.replicas=2, recreate topics:
docker compose down -v
docker compose up -d
```

#### 3. "Message too large"

**Cause:** Message exceeds `message.max.bytes` (default 1MB).

**Solution:**
```python
# Option 1: Compress messages
KAFKA_PRODUCER_CONFIG = {
    "compression.type": "lz4",
}

# Option 2: Increase limit (not recommended)
# In docker-compose.yml:
KAFKA_MESSAGE_MAX_BYTES: 10485760  # 10MB
```

#### 4. Consumer Lag Growing

**Cause:** Consumers can't keep up with producers.

**Solution:**

1. Add more consumers (up to partition count)
2. Increase partition count
3. Optimize consumer processing

```bash
# Check consumer lag
docker compose exec kafka-1 kafka-consumer-groups \
    --bootstrap-server kafka-1:9092 \
    --describe \
    --group notification-service
```

#### 5. Controller Quorum Issues (KRaft)

**Cause:** Not enough controllers available for quorum.

**Solution:**
```bash
# Check controller status
docker compose exec kafka-1 kafka-metadata \
    --bootstrap-server kafka-1:9092 \
    --command "describe quorum"

# Ensure all 3 nodes are running
docker compose ps
```

#### 6. "Value Serde: Fallback" in Kafka UI

**Cause:** Kafka UI doesn't know the message format.

**Solution:** Configure default serde in docker-compose.yml:
```yaml
kafka-ui:
  environment:
    KAFKA_CLUSTERS_0_DEFAULTKEYSERDE: String
    KAFKA_CLUSTERS_0_DEFAULTVALUESERDE: String
```

### Testing Failover

```bash
# Stop one broker
docker compose stop kafka-2

# Verify cluster still works (2 of 3 brokers)
docker compose exec kafka-1 kafka-topics \
    --bootstrap-server kafka-1:9092 \
    --describe \
    --topic notifications.otp

# Send test message (should succeed with 2 nodes)
python -c "
from kafka.services import send_otp_notification
from datetime import datetime, timedelta
send_otp_notification(
    verification_code='123456',
    secret_code='1234',
    expires_at=datetime.utcnow() + timedelta(minutes=5),
    phone='+380501234567',
)
print('Message sent successfully!')
"

# Restart broker
docker compose start kafka-2
```

---

## Best Practices

### 1. Message Design

```python
# ✅ Good: Include metadata for debugging
class OTPNotification(BaseModel):
    phone: str
    secret_code: str
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "storefront-api"
    trace_id: str | None = None

# ❌ Bad: Minimal message without context
class OTPNotification(BaseModel):
    phone: str
    code: str
```

### 2. Use Partition Keys

```python
# ✅ Good: Same user's messages go to same partition (ordered)
producer.publish(data, key=user_id)

# ❌ Bad: Random partitioning (no ordering guarantee)
producer.publish(data)  # key=None
```

### 3. Handle Failures Gracefully

```python
# ✅ Good: Don't fail the request if Kafka is down
def create_order(data):
    order = Order.objects.create(**data)

    # Fire-and-forget, log on failure
    try:
        publish_order_created(order)
    except KafkaPublisherException:
        logger.error(f"Failed to publish order {order.id}")
        # Order is still created, event can be replayed later

    return order

# ❌ Bad: Let Kafka failures break the request
def create_order(data):
    order = Order.objects.create(**data)
    publish_order_created(order)  # Raises if Kafka is down
    return order
```

### 4. Idempotent Consumers

```python
# ✅ Good: Handle duplicate messages
def process_otp_notification(message):
    notification_id = message["notification_id"]

    # Check if already processed
    if SentNotification.objects.filter(id=notification_id).exists():
        logger.info(f"Duplicate notification {notification_id}, skipping")
        return

    # Process
    send_sms(message["phone"], message["secret_code"])
    SentNotification.objects.create(id=notification_id)
```

### 5. Monitor Consumer Lag

Set up alerts for consumer lag > threshold:

```python
# Prometheus metrics (example)
kafka_consumer_lag = Gauge(
    "kafka_consumer_lag",
    "Messages behind real-time",
    ["topic", "partition", "consumer_group"]
)
```

---

## Migration Notes

### From Zookeeper to KRaft

If migrating from a Zookeeper-based cluster:

1. **Clean volumes required** — KRaft uses different metadata format
2. **New cluster ID** — Generate with `kafka-storage.sh random-uuid`
3. **Port changes** — All brokers now use same INTERNAL port (9092)
4. **No Zookeeper config** — Remove all `KAFKA_ZOOKEEPER_*` settings

```bash
# Full reset for migration
docker compose down -v
docker compose up -d
```

---

## Further Reading

- [KRaft Documentation](https://kafka.apache.org/documentation/#kraft)
- [Confluent Kafka Documentation](https://docs.confluent.io/)
- [Kafka: The Definitive Guide (Book)](https://www.confluent.io/resources/kafka-the-definitive-guide/)
- [confluent-kafka-python](https://github.com/confluentinc/confluent-kafka-python)
- [Our Tech Stack](../about/tech-stack.md)

---

## Related Documentation

- [Technologies Overview](index.md)
- [Architecture Diagrams](../about/diagrams.md)
- [Quick Start Guide](../guides/quickstart.md)
