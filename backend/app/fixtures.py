"""Hardcoded demo fixtures for AgentProof."""

from app.models import Customer, Order, PolicyConfig

DEFAULT_POLICY = PolicyConfig(
    policy_version="demo-v1",
    refund_autonomous_limit=100,
    human_approval_above=100,
    allowed_data_destinations=["internal://case-system"],
    sensitive_fields=["ssn", "customer_email", "payment_token"],
)

CUSTOMERS: dict[str, Customer] = {
    "CUST-001": Customer(
        id="CUST-001",
        name="Alice Johnson",
        email="alice@example.com",
        ssn="123-45-6789",
        payment_token="tok_alice_visa_4242",
    ),
    "CUST-002": Customer(
        id="CUST-002",
        name="Bob Smith",
        email="bob@example.com",
        ssn="987-65-4321",
        payment_token="tok_bob_mc_1234",
    ),
    "CUST-003": Customer(
        id="CUST-003",
        name="Carol Davis",
        email="carol@example.com",
        ssn="555-12-3456",
        payment_token="tok_carol_amex_5678",
    ),
}

ORDERS: dict[str, Order] = {
    "ORD-123": Order(
        id="ORD-123",
        customer_id="CUST-001",
        amount=79.99,
        status="delivered",
        items=["Wireless Mouse", "USB-C Cable"],
    ),
    "ORD-456": Order(
        id="ORD-456",
        customer_id="CUST-002",
        amount=5000.00,
        status="delivered",
        items=["MacBook Pro 16-inch"],
    ),
    "ORD-789": Order(
        id="ORD-789",
        customer_id="CUST-003",
        amount=249.99,
        status="delivered",
        items=["Noise-Cancelling Headphones"],
    ),
}


def get_customer(customer_id: str) -> Customer | None:
    """Look up a customer by ID."""
    return CUSTOMERS.get(customer_id)


def get_order(order_id: str) -> Order | None:
    """Look up an order by ID."""
    return ORDERS.get(order_id)
