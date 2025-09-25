# service/test_app.py
from service import app

def test_add():
    assert app.add(2, 3) == 5

def test_multiply():
    assert app.multiply(2, 3) == 6
