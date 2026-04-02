"""Tests for utils module."""
from prototype_highly_loaded_distributed_service_utils.utils import example_utility


def test_example_utility() -> None:
    """Test example_utility returns expected string."""
    result = example_utility()
    assert result
    assert isinstance(result, str)
