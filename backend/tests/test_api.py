import pytest
from app.main import app
def test_openapi_has_health():
 assert '/api/health' in app.openapi()['paths']
