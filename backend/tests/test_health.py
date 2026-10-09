from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

def test_health():
    with patch('app.main.init_pool'):
        c=TestClient(app); assert c.get('/health').json()=={'status':'ok'}
