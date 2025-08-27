from datetime import datetime, timedelta
import importlib.util
import pathlib

module_path = (
    pathlib.Path(__file__).resolve().parent.parent
    / "erpnext"
    / "erpnext_integrations"
    / "lenco_subscription.py"
)
spec = importlib.util.spec_from_file_location("lenco_subscription", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
LencoSubscription = module.LencoSubscription
TrialTracker = module.TrialTracker


def test_amount_within_included_users():
    sub = LencoSubscription("monthly", user_count=3)
    assert sub.amount() == 2500


def test_amount_extra_users():
    sub = LencoSubscription("quarterly", user_count=5)
    assert sub.amount() == 7000 + 2 * 1500


def test_trial_expires_by_days():
    tracker = TrialTracker(start=datetime.utcnow() - timedelta(days=11))
    assert tracker.expired


def test_trial_expires_by_transactions():
    tracker = TrialTracker(transaction_count=50)
    assert tracker.expired
