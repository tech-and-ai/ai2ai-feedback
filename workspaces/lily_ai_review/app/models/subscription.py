"""
Subscription models for Lily AI.

This module provides data models for subscriptions.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Subscription(BaseModel):
    """Subscription model."""

    id: Optional[str] = None
    user_id: str
    subscription_tier: str = "free"
    status: str = "active"
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    papers_limit: int = 0
    papers_used: int = 0
    papers_remaining: int = 0
    additional_credits: int = 0
    subscription_papers_remaining: int = 0
    additional_papers_remaining: int = 0
    total_papers_remaining: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_verified: Optional[datetime] = None

    @classmethod
    def from_db_record(cls, record: Dict[str, Any]) -> "Subscription":
        """
        Create a Subscription instance from a database record.

        Args:
            record: The database record

        Returns:
            A Subscription instance
        """
        # Calculate papers remaining
        papers_limit = record.get("papers_limit", 0)
        papers_used = record.get("papers_used", 0)
        papers_remaining = max(0, papers_limit - papers_used)

        # Get subscription papers remaining and additional papers remaining
        subscription_papers_remaining = record.get("subscription_papers_remaining", papers_remaining)
        additional_papers_remaining = record.get("additional_papers_remaining", record.get("additional_credits", 0))

        # Calculate total papers remaining
        total_papers_remaining = record.get("total_papers_remaining",
                                           subscription_papers_remaining + additional_papers_remaining)

        # Create subscription
        return cls(
            id=record.get("id"),
            user_id=record.get("user_id"),
            subscription_tier=record.get("subscription_tier", "free"),
            status=record.get("status", "active"),
            stripe_subscription_id=record.get("stripe_subscription_id"),
            stripe_customer_id=record.get("stripe_customer_id"),
            papers_limit=papers_limit,
            papers_used=papers_used,
            papers_remaining=papers_remaining,
            additional_credits=record.get("additional_credits", 0),
            subscription_papers_remaining=subscription_papers_remaining,
            additional_papers_remaining=additional_papers_remaining,
            total_papers_remaining=total_papers_remaining,
            start_date=record.get("start_date"),
            end_date=record.get("end_date"),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
            last_verified=record.get("last_verified")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the subscription to a dictionary.

        Returns:
            A dictionary representation of the subscription
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subscription_tier": self.subscription_tier,
            "status": self.status,
            "stripe_subscription_id": self.stripe_subscription_id,
            "stripe_customer_id": self.stripe_customer_id,
            "papers_limit": self.papers_limit,
            "papers_used": self.papers_used,
            "papers_remaining": self.papers_remaining,
            "additional_credits": self.additional_credits,
            "subscription_papers_remaining": self.subscription_papers_remaining,
            "additional_papers_remaining": self.additional_papers_remaining,
            "total_papers_remaining": self.total_papers_remaining,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None
        }

    def is_active(self) -> bool:
        """
        Check if the subscription is active.

        Returns:
            True if active, False otherwise
        """
        return self.status == "active"

    def can_create_paper(self) -> bool:
        """
        Check if the user can create a paper.

        Returns:
            True if the user can create a paper, False otherwise
        """
        if not self.is_active():
            return False

        return self.papers_remaining > 0 or self.additional_credits > 0


class Payment(BaseModel):
    """Payment model."""

    id: Optional[str] = None
    user_id: str
    subscription_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    amount: int
    currency: str = "usd"
    status: str
    payment_method: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_record(cls, record: Dict[str, Any]) -> "Payment":
        """
        Create a Payment instance from a database record.

        Args:
            record: The database record

        Returns:
            A Payment instance
        """
        return cls(
            id=record.get("id"),
            user_id=record.get("user_id"),
            subscription_id=record.get("subscription_id"),
            stripe_payment_intent_id=record.get("stripe_payment_intent_id"),
            stripe_invoice_id=record.get("stripe_invoice_id"),
            amount=record.get("amount"),
            currency=record.get("currency", "usd"),
            status=record.get("status"),
            payment_method=record.get("payment_method"),
            description=record.get("description"),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at")
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the payment to a dictionary.

        Returns:
            A dictionary representation of the payment
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "stripe_invoice_id": self.stripe_invoice_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "payment_method": self.payment_method,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
