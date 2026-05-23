"""Data retention exception registry with owner tracking."""

import datetime
from typing import Dict, List, Optional, Any


class RetentionExceptionError(Exception):
    """Base exception for retention exception errors."""
    pass


class MissingOwnerError(RetentionExceptionError):
    """Raised when a retention exception is missing owner metadata."""
    pass


class ExpiredExceptionError(RetentionExceptionError):
    """Raised when a retention exception has expired."""
    pass


class RetentionException:
    """A single retention exception with governance metadata."""

    def __init__(
        self,
        owner: str,
        reason: str,
        expiration: str,  # ISO 8601 date string
        review_date: str,  # ISO 8601 date string
        category: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if not owner:
            raise MissingOwnerError("Retention exception requires an owner")
        if not reason:
            raise ValueError("Retention exception requires a reason")
        if not expiration:
            raise ValueError("Retention exception requires an expiration date")
        if not review_date:
            raise ValueError("Retention exception requires a review date")

        self.owner = owner
        self.reason = reason
        self.expiration = datetime.date.fromisoformat(expiration)
        self.review_date = datetime.date.fromisoformat(review_date)
        self.category = category
        self.metadata = metadata or {}
        self.created_at = datetime.date.today()

    def is_expired(self) -> bool:
        """Check if this exception has expired."""
        return datetime.date.today() > self.expiration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "reason": self.reason,
            "expiration": self.expiration.isoformat(),
            "review_date": self.review_date.isoformat(),
            "category": self.category,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class RetentionExceptionRegistry:
    """Registry for retention exceptions with governance validation."""

    def __init__(self):
        self._exceptions: List[RetentionException] = []

    def register(
        self,
        owner: str,
        reason: str,
        expiration: str,
        review_date: str,
        category: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RetentionException:
        """Register a new retention exception.

        Args:
            owner: Accountable owner for this exception
            reason: Reason for the exception
            expiration: ISO 8601 date string for expiration
            review_date: ISO 8601 date string for review
            category: Optional category for grouping
            metadata: Optional additional metadata

        Raises:
            MissingOwnerError: If owner is empty
            ValueError: If required fields are missing
        """
        exc = RetentionException(
            owner=owner,
            reason=reason,
            expiration=expiration,
            review_date=review_date,
            category=category,
            metadata=metadata,
        )
        self._exceptions.append(exc)
        return exc

    def validate(self) -> List[RetentionException]:
        """Validate all exceptions, returning expired ones.

        Raises:
            ExpiredExceptionError: If any exceptions are expired
        """
        expired = [e for e in self._exceptions if e.is_expired()]
        if expired:
            raise ExpiredExceptionError(
                f"{len(expired)} retention exception(s) have expired"
            )
        return expired

    def active_exceptions(self) -> List[RetentionException]:
        """Return all non-expired exceptions."""
        return [e for e in self._exceptions if not e.is_expired()]

    def by_owner(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group active exceptions by owner."""
        result: Dict[str, List[Dict[str, Any]]] = {}
        for exc in self.active_exceptions():
            if exc.owner not in result:
                result[exc.owner] = []
            result[exc.owner].append(exc.to_dict())
        return result

    def to_dict(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._exceptions]
