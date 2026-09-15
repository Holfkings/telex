import warnings

def test_clean_execution():
    with warnings.catch_warnings(record=True) as record:
        val = 100
    assert len(record) == 0
