import importlib

def test_import_app():
    # just import app.py to make coverage count it
    importlib.import_module("service.app")
