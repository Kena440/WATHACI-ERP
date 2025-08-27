import os
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests

# Lenco API configuration
LENCO_BASE_URL = os.environ.get("LENCO_BASE_URL", "https://api.lenco.co/access/v2")
LENCO_SECRET_KEY = os.environ.get("LENCO_SECRET_KEY", "725867721a5e2717b4619606b04465cad02788915a90963d03fabb5dbc3757b9")
LENCO_PUBLIC_KEY = os.environ.get("LENCO_PUBLIC_KEY", "pub-f3d19a14ad9bd820fc5c0239dd6957fb14b0223bd6d15525")
LENCO_WEBHOOK_SIGNATURE_KEY = os.environ.get(
    "LENCO_WEBHOOK_SIGNATURE_KEY",
    "7133d6bce4299a56439089294785c0624dca56b6c77159237020503ce77589e8",
)


@dataclass
class LencoSubscription:
    """Handle subscription payments via Lenco."""

    plan: str
    user_count: int = 1

    BASE_PLAN_PRICES = {
        "monthly": 2500,
        "quarterly": 7000,
        "yearly": 35000,
    }
    USERS_INCLUDED = 3
    EXTRA_USER_PRICE = 1500
    ALLOWED_METHODS = {"mobile_money", "bank_transfer", "card"}

    def amount(self) -> int:
        base = self.BASE_PLAN_PRICES[self.plan]
        extra_users = max(0, self.user_count - self.USERS_INCLUDED)
        return base + extra_users * self.EXTRA_USER_PRICE

    def create_payment(self, payment_method: str, customer_name: str) -> dict:
        """Create a payment session on Lenco."""
        if payment_method not in self.ALLOWED_METHODS:
            raise ValueError("Unsupported payment method")
        payload = {
            "amount": self.amount(),
            "currency": "ZMW",
            "payment_method": payment_method,
            "customer_name": customer_name,
        }
        headers = {"Authorization": f"Bearer {LENCO_SECRET_KEY}"}
        response = requests.post(
            f"{LENCO_BASE_URL}/payments", json=payload, headers=headers, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def verify_payment(self, payment_id: str) -> dict:
        """Verify payment status before enabling subscription."""
        headers = {"Authorization": f"Bearer {LENCO_SECRET_KEY}"}
        response = requests.get(
            f"{LENCO_BASE_URL}/payments/{payment_id}", headers=headers, timeout=10
        )
        response.raise_for_status()
        return response.json()


class TrialTracker:
    """Track trial usage limited by days or number of transactions."""

    MAX_DAYS = 10
    MAX_TRANSACTIONS = 50

    def __init__(self, start: datetime | None = None, transaction_count: int = 0):
        self.start = start or datetime.utcnow()
        self.transaction_count = transaction_count

    def record_transaction(self) -> None:
        self.transaction_count += 1

    @property
    def expired(self) -> bool:
        if datetime.utcnow() - self.start >= timedelta(days=self.MAX_DAYS):
            return True
        return self.transaction_count >= self.MAX_TRANSACTIONS
