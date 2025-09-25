import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import test_app

def test_basic_route():
    assert True  # Replace with real test if needed


# service/test_app.py
import test_app

def test_basic_route():
    # call a function from app.py
    result = app.some_function()
    assert result == expected_value

