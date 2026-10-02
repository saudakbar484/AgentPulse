import pytest
from app.core.config import get_settings
from app.llm.client import default_llm_client

settings = get_settings()


@pytest.fixture(autouse=True)
def setup_test_environment():
    settings.APP_ENV = "testing"
    default_llm_client.is_mock = True
    yield
    settings.APP_ENV = "development"
    default_llm_client.is_mock = False
