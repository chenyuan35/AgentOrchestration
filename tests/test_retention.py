import datetime
import pytest
from src.common.retention import (
    RetentionException,
    RetentionExceptionRegistry,
    MissingOwnerError,
    ExpiredExceptionError,
)


class TestRetentionException:
    def test_create_valid_exception(self):
        exc = RetentionException(
            owner="alice@example.com",
            reason="Legal hold for litigation",
            expiration="2027-01-01",
            review_date="2026-07-01",
        )
        assert exc.owner == "alice@example.com"
        assert exc.reason == "Legal hold for litigation"
        assert exc.is_expired() is False

    def test_missing_owner_raises(self):
        with pytest.raises(MissingOwnerError):
            RetentionException(
                owner="",
                reason="Some reason",
                expiration="2027-01-01",
                review_date="2026-07-01",
            )

    def test_missing_reason_raises(self):
        with pytest.raises(ValueError):
            RetentionException(
                owner="alice@example.com",
                reason="",
                expiration="2027-01-01",
                review_date="2026-07-01",
            )

    def test_missing_expiration_raises(self):
        with pytest.raises(ValueError):
            RetentionException(
                owner="alice@example.com",
                reason="Some reason",
                expiration="",
                review_date="2026-07-01",
            )

    def test_missing_review_date_raises(self):
        with pytest.raises(ValueError):
            RetentionException(
                owner="alice@example.com",
                reason="Some reason",
                expiration="2027-01-01",
                review_date="",
            )

    def test_expired_exception(self):
        past = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        exc = RetentionException(
            owner="alice@example.com",
            reason="Old exception",
            expiration=past,
            review_date=past,
        )
        assert exc.is_expired() is True

    def test_to_dict(self):
        exc = RetentionException(
            owner="alice@example.com",
            reason="Legal hold",
            expiration="2027-01-01",
            review_date="2026-07-01",
            category="litigation",
        )
        data = exc.to_dict()
        assert data["owner"] == "alice@example.com"
        assert data["reason"] == "Legal hold"
        assert data["expiration"] == "2027-01-01"
        assert data["review_date"] == "2026-07-01"
        assert data["category"] == "litigation"


class TestRetentionExceptionRegistry:
    def test_register_and_retrieve(self):
        registry = RetentionExceptionRegistry()
        registry.register(
            owner="alice@example.com",
            reason="Legal hold",
            expiration="2027-01-01",
            review_date="2026-07-01",
        )
        assert len(registry.active_exceptions()) == 1

    def test_register_requires_owner(self):
        registry = RetentionExceptionRegistry()
        with pytest.raises(MissingOwnerError):
            registry.register(
                owner="",
                reason="No owner",
                expiration="2027-01-01",
                review_date="2026-07-01",
            )

    def test_validate_raises_on_expired(self):
        registry = RetentionExceptionRegistry()
        past = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        registry.register(
            owner="alice@example.com",
            reason="Expired",
            expiration=past,
            review_date=past,
        )
        with pytest.raises(ExpiredExceptionError):
            registry.validate()

    def test_validate_passes_when_all_active(self):
        registry = RetentionExceptionRegistry()
        registry.register(
            owner="alice@example.com",
            reason="Active",
            expiration="2027-01-01",
            review_date="2026-07-01",
        )
        expired = registry.validate()
        assert len(expired) == 0

    def test_by_owner_groups_correctly(self):
        registry = RetentionExceptionRegistry()
        registry.register(
            owner="alice@example.com",
            reason="Legal hold",
            expiration="2027-01-01",
            review_date="2026-07-01",
        )
        registry.register(
            owner="alice@example.com",
            reason="Compliance",
            expiration="2027-06-01",
            review_date="2026-12-01",
        )
        registry.register(
            owner="bob@example.com",
            reason="Audit",
            expiration="2027-03-01",
            review_date="2026-09-01",
        )
        by_owner = registry.by_owner()
        assert len(by_owner["alice@example.com"]) == 2
        assert len(by_owner["bob@example.com"]) == 1

    def test_active_excludes_expired(self):
        registry = RetentionExceptionRegistry()
        past = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        future = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
        registry.register(
            owner="alice@example.com",
            reason="Expired",
            expiration=past,
            review_date=past,
        )
        registry.register(
            owner="bob@example.com",
            reason="Active",
            expiration=future,
            review_date=future,
        )
        active = registry.active_exceptions()
        assert len(active) == 1
        assert active[0].owner == "bob@example.com"

    def test_to_dict(self):
        registry = RetentionExceptionRegistry()
        registry.register(
            owner="alice@example.com",
            reason="Legal hold",
            expiration="2027-01-01",
            review_date="2026-07-01",
        )
        data = registry.to_dict()
        assert len(data) == 1
        assert data[0]["owner"] == "alice@example.com"
