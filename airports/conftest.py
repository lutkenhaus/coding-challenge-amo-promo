import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings

# Test cache settings for consistent testing
TEST_CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database.
    """
    pass

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test"""
    cache.clear()
    yield
    cache.clear()

@pytest.fixture
def use_test_cache_settings():
    """Override cache settings for tests"""
    with override_settings(CACHES=TEST_CACHE_SETTINGS):
        yield