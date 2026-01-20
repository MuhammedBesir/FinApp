"""
Test configuration and fixtures
"""
import pytest
import os

# Set test environment
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32chars"
