# Architecture Diagrams

Visual representation of the system architecture and flows.

---

## High-Level System Overview

```mermaid
flowchart LR
    Partners["🏪 Partners<br/>(Cafes/Restaurants)"]
    Monolith["🏛️ Django Monolith<br/>Integrator"]
    Users["👤 Customers"]
    Payment["💳 Payment<br/>Gateway"]
    Delivery["🚚 Delivery<br/>Service"]
    Accounting["📊 Accounting"]

    Partners -->|"Menu sync"| Monolith
    Users -->|"Orders"| Monolith
    Monolith -->|"Payment redirect"| Payment
    Payment -->|"Confirmation"| Monolith
    Monolith -->|"Order details"| Partners
    Monolith -->|"Delivery request"| Delivery
    Delivery -->|"Deliver to"| Users
    Monolith -->|"Settlements"| Accounting
    Accounting -->|"Payouts"| Partners
    Accounting -->|"Payouts/Collection"| Delivery
```

---

## Detailed Component Architecture

```mermaid
flowchart TB
    subgraph Partners["PARTNERS"]
        Cafe1["Cafe 1"]
        Cafe2["Restaurant 1"]
        CafeN["Cafe N"]
    end

    subgraph Monolith["DJANGO MONOLITH"]
        API["REST API"]
        MenuCatalog["Menu Catalog"]
        OrderMgmt["Order Management"]
        BalanceCtrl["Balance Control"]
        Commission["Commission Accounting"]
    end

    subgraph Temporal["TEMPORAL.IO WORKFLOWS"]
        OrderWF["Order Workflow"]
        PaymentWF["Payment Workflow"]
        DeliveryWF["Delivery Workflow"]
        SettlementWF["Settlement Workflow"]
    end

    Cafe1 --> MenuCatalog
    Cafe2 --> MenuCatalog
    CafeN --> MenuCatalog

    API --> OrderMgmt
    OrderMgmt --> OrderWF
    OrderWF --> PaymentWF
    PaymentWF --> DeliveryWF
    DeliveryWF --> SettlementWF

    PaymentWF --> BalanceCtrl
    BalanceCtrl --> Commission
    Commission --> SettlementWF
```

---

## Order Flow Sequence

```mermaid
sequenceDiagram
    autonumber
    participant U as Customer
    participant M as Monolith
    participant T as Temporal
    participant P as Payment Gateway
    participant C as Cafe
    participant D as Delivery Service
    participant A as Accounting

    U->>M: Create order
    M->>T: Start Order Workflow
    T->>P: Redirect to payment
    P->>U: Payment page
    U->>P: Pay online
    P->>T: Payment callback (success)
    T->>M: Update balance
    T->>C: Send order details
    C->>C: Prepare order
    T->>D: Request courier (ETA based)
    D->>C: Pickup order
    D->>U: Deliver order
    alt Cash payment
        U->>D: Pay cash
        D->>M: Report cash received
    end
    M->>A: Settlement data
    A->>C: Payout (minus commission)
    A->>D: Payout or cash collection
```

---

## Financial Flow

```mermaid
flowchart LR
    subgraph Income["INCOME"]
        Online["Online Payments"]
        Cash["Cash from Couriers"]
    end

    subgraph Monolith["MONOLITH"]
        Balance["Balance Control"]
        Comm["Commission Calculator"]
    end

    subgraph Outflow["OUTFLOW"]
        CafePay["Cafe Payouts"]
        DeliveryPay["Delivery Payouts"]
        Platform["Platform Revenue"]
    end

    Online --> Balance
    Cash --> Balance
    Balance --> Comm
    Comm --> CafePay
    Comm --> DeliveryPay
    Comm --> Platform
```

---

## Order State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Customer places order
    Created --> PaymentPending: Awaiting payment
    PaymentPending --> Paid: Payment successful
    PaymentPending --> Cancelled: Payment failed/timeout
    Paid --> Preparing: Sent to restaurant
    Preparing --> ReadyForPickup: Food ready
    ReadyForPickup --> InDelivery: Courier picked up
    InDelivery --> Delivered: Customer received
    Delivered --> [*]

    Paid --> Cancelled: Customer cancels
    Preparing --> Cancelled: Restaurant cancels
```

---

## Microservices Architecture (Target)

```mermaid
flowchart TB
    subgraph Clients["CLIENT APPS"]
        Web["🌐 Web App"]
        Mobile["📱 Mobile App"]
        Partner["🏪 Partner Portal"]
        Courier["🚴 Courier App"]
    end

    subgraph Gateway["API GATEWAY"]
        Nginx["Nginx / Kong"]
    end

    subgraph Services["MICROSERVICES"]
        Storefront["Storefront Service"]
        Orders["Order Service"]
        Payments["Payment Service"]
        Delivery["Delivery Service"]
        Notifications["Notification Service"]
    end

    subgraph Messaging["MESSAGE BROKER"]
        Kafka["Apache Kafka"]
    end

    subgraph Data["DATA STORES"]
        Postgres[(PostgreSQL)]
        Redis[(Redis)]
        S3[(S3 Storage)]
    end

    subgraph Orchestration["WORKFLOW"]
        Temporal["Temporal.io"]
    end

    Clients --> Gateway
    Gateway --> Services
    Services <--> Messaging
    Services --> Data
    Services <--> Orchestration
```

---

## Infrastructure Overview

```mermaid
flowchart TB
    subgraph Cloud["CLOUD / ON-PREMISE"]
        subgraph K8s["Kubernetes Cluster"]
            Ingress["Ingress Controller"]

            subgraph Apps["Application Pods"]
                API["API Servers"]
                Workers["Background Workers"]
            end
        end

        subgraph Managed["Managed Services"]
            RDS[(PostgreSQL RDS)]
            ElastiCache[(Redis)]
            MSK["Kafka MSK"]
        end

        subgraph Monitoring["OBSERVABILITY"]
            Prometheus["Prometheus"]
            Grafana["Grafana"]
            Sentry["Sentry"]
        end
    end

    Internet["Internet"] --> Ingress
    Ingress --> Apps
    Apps --> Managed
    Apps --> Monitoring
```

---

## Database Schema (Simplified)

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER ||--o| PARTNER : owns
    USER ||--o| COURIER : is

    PARTNER ||--o{ MENU_ITEM : offers
    PARTNER ||--o{ ORDER : receives

    ORDER ||--|{ ORDER_ITEM : contains
    ORDER ||--o| COURIER : delivered_by
    ORDER ||--o| PAYMENT : has

    COURIER ||--o{ DELIVERY : makes
```

---

## Related Documentation

- [Project Overview](overview.md)
- [Tech Stack](tech-stack.md)
