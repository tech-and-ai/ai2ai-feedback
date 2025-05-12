"""
Tests for the billing routes.
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)

@pytest.fixture
def mock_session():
    """Create a mock session with user data."""
    return {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "username": "testuser",
        "subscription_tier": "premium"
    }

@pytest.fixture
def mock_subscription():
    """Create a mock subscription."""
    return {
        "id": "test-subscription-id",
        "user_id": "test-user-id",
        "subscription_tier": "premium",
        "status": "active",
        "papers_limit": 10,
        "papers_used": 2,
        "additional_credits": 5,
        "papers_remaining": 13,
        "end_date": "2025-12-31T00:00:00Z"
    }

@patch("app.utils.get_session_manager")
@patch("app.billing.subscription_service.SubscriptionService.get_user_subscription")
def test_manage_subscription_authenticated(mock_get_subscription, mock_get_session_manager, mock_session, mock_subscription):
    """Test the manage subscription route for authenticated users."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = True
    mock_get_session_manager.return_value = session_manager
    
    # Mock request.session
    def get_session_value(key, default=None):
        return mock_session.get(key, default)
    
    app.dependency_overrides = {
        "request.session.get": get_session_value
    }
    
    # Mock subscription service
    mock_get_subscription.return_value = mock_subscription
    
    # Make request
    response = client.get("/billing/manage")
    
    # Assertions
    assert response.status_code == 200
    assert "Manage Subscription" in response.text
    assert "Premium" in response.text
    assert "£18.00/month" in response.text
    assert "Papers Used" in response.text
    assert "2 / 10" in response.text
    assert "Additional Credits" in response.text
    assert "5" in response.text
    
    # Clean up
    app.dependency_overrides = {}

@patch("app.utils.get_session_manager")
def test_manage_subscription_unauthenticated(mock_get_session_manager):
    """Test the manage subscription route for unauthenticated users."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = False
    mock_get_session_manager.return_value = session_manager
    
    # Make request
    response = client.get("/billing/manage")
    
    # Assertions
    assert response.status_code == 303  # Redirect
    assert response.headers["location"] == "/login"

@patch("app.utils.get_session_manager")
@patch("app.billing.subscription_service.SubscriptionService.get_user_subscription")
def test_manage_subscription_free_tier(mock_get_subscription, mock_get_session_manager, mock_session):
    """Test the manage subscription route for free tier users."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = True
    mock_get_session_manager.return_value = session_manager
    
    # Mock request.session
    mock_session["subscription_tier"] = "free"
    def get_session_value(key, default=None):
        return mock_session.get(key, default)
    
    app.dependency_overrides = {
        "request.session.get": get_session_value
    }
    
    # Mock subscription service
    mock_get_subscription.return_value = None
    
    # Make request
    response = client.get("/billing/manage")
    
    # Assertions
    assert response.status_code == 303  # Redirect
    assert response.headers["location"] == "/subscription"
    
    # Clean up
    app.dependency_overrides = {}

@patch("app.utils.get_session_manager")
@patch("app.billing.stripe_service.StripeService.create_credits_checkout_session")
def test_create_credits_checkout_session(mock_create_checkout, mock_get_session_manager, mock_session):
    """Test the create credits checkout session route."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = True
    mock_get_session_manager.return_value = session_manager
    
    # Mock request.session
    def get_session_value(key, default=None):
        return mock_session.get(key, default)
    
    app.dependency_overrides = {
        "request.session.get": get_session_value
    }
    
    # Mock checkout session
    mock_create_checkout.return_value = {
        "id": "test-session-id",
        "url": "https://checkout.stripe.com/test-session"
    }
    
    # Make request
    response = client.get("/billing/checkout/credits/10")
    
    # Assertions
    assert response.status_code == 303  # Redirect
    assert response.headers["location"] == "https://checkout.stripe.com/test-session"
    mock_create_checkout.assert_called_once_with(
        credits_amount="10",
        customer_email="test@example.com",
        user_id="test-user-id"
    )
    
    # Clean up
    app.dependency_overrides = {}

@patch("app.utils.get_session_manager")
def test_create_credits_checkout_session_invalid_amount(mock_get_session_manager, mock_session):
    """Test the create credits checkout session route with an invalid amount."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = True
    mock_get_session_manager.return_value = session_manager
    
    # Mock request.session
    def get_session_value(key, default=None):
        return mock_session.get(key, default)
    
    app.dependency_overrides = {
        "request.session.get": get_session_value
    }
    
    # Make request
    response = client.get("/billing/checkout/credits/invalid")
    
    # Assertions
    assert response.status_code == 400  # Bad request
    
    # Clean up
    app.dependency_overrides = {}

@patch("app.utils.get_session_manager")
@patch("app.billing.subscription_service.SubscriptionService.cancel_subscription")
def test_cancel_subscription(mock_cancel_subscription, mock_get_session_manager, mock_session):
    """Test the cancel subscription route."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = True
    mock_get_session_manager.return_value = session_manager
    
    # Mock request.session
    def get_session_value(key, default=None):
        return mock_session.get(key, default)
    
    app.dependency_overrides = {
        "request.session.get": get_session_value
    }
    
    # Mock cancel subscription
    mock_cancel_subscription.return_value = True
    
    # Make request
    response = client.get("/billing/cancel-subscription")
    
    # Assertions
    assert response.status_code == 303  # Redirect
    assert response.headers["location"] == "/subscription?canceled=true"
    mock_cancel_subscription.assert_called_once_with("test-user-id")
    
    # Clean up
    app.dependency_overrides = {}

@patch("app.utils.get_session_manager")
def test_subscription_status_authenticated(mock_get_session_manager, mock_session, mock_subscription):
    """Test the subscription status route for authenticated users."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = True
    mock_get_session_manager.return_value = session_manager
    
    # Mock request.session
    def get_session_value(key, default=None):
        return mock_session.get(key, default)
    
    app.dependency_overrides = {
        "request.session.get": get_session_value
    }
    
    # Mock subscription service
    with patch("app.billing.subscription_service.SubscriptionService.get_user_subscription") as mock_get_subscription:
        mock_get_subscription.return_value = mock_subscription
        
        # Make request
        response = client.get("/billing/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "premium"
        assert data["status"] == "active"
        assert data["papers_used"] == 2
        assert data["papers_limit"] == 10
        assert data["papers_remaining"] == 13
        assert data["additional_credits"] == 5
        assert data["is_active"] is True
    
    # Clean up
    app.dependency_overrides = {}

@patch("app.utils.get_session_manager")
def test_subscription_status_unauthenticated(mock_get_session_manager):
    """Test the subscription status route for unauthenticated users."""
    # Set up mocks
    session_manager = MagicMock()
    session_manager.is_authenticated.return_value = False
    mock_get_session_manager.return_value = session_manager
    
    # Make request
    response = client.get("/billing/status")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_authenticated"
