import pytest

def test_clean_execution():
    with pytest.warns(None) as record:
        val = 100
    assert len(record) == 0
