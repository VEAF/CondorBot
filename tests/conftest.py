import pytest
from unittest.mock import patch
from condor.config import load_config


@pytest.fixture(scope="session", autouse=True)
def mock_config():
    with patch("condor.flight_plan.get_config") as mock_get_config:
        mock_get_config.return_value = load_config("tests/config_test.yaml")
        yield mock_get_config
