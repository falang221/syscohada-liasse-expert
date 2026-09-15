import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user, db
from unittest.mock import MagicMock, AsyncMock

client = TestClient(app)

# Mock data
class MockUser:
    def __init__(self, id, username, role, cabinetId):
        self.id = id
        self.username = username
        self.role = role
        self.cabinetId = cabinetId

mock_admin = MockUser(id="admin-id", username="admin", role="ADMIN", cabinetId="cab-id")
mock_collab = MockUser(id="collab-id", username="collab", role="COLLABORATOR", cabinetId="cab-id")

@pytest.fixture(autouse=True)
def mock_db():
    # Mock Prisma database calls
    # We use AsyncMock for awaitable methods
    db.user = MagicMock()
    db.user.find_many = AsyncMock(return_value=[])
    db.user.find_unique = AsyncMock(return_value=None)
    
    db.client = MagicMock()
    db.client.find_many = AsyncMock(return_value=[])
    
    yield

@pytest.fixture
def override_admin():
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def override_collab():
    app.dependency_overrides[get_current_user] = lambda: mock_collab
    yield
    app.dependency_overrides.clear()

def test_admin_access_users_list(override_admin):
    response = client.get("/api/users/")
    assert response.status_code == 200
    db.user.find_many.assert_called_once()

def test_collaborator_access_denied_users_list(override_collab):
    response = client.get("/api/users/")
    assert response.status_code == 403
    assert "Seuls les administrateurs" in response.json()["detail"]

def test_collaborator_can_access_clients_list(override_collab):
    response = client.get("/api/clients/")
    assert response.status_code == 200
    db.client.find_many.assert_called_once()

def test_collaborator_can_access_me(override_collab):
    response = client.get("/api/users/me")
    assert response.status_code == 200
    assert response.json()["username"] == "collab"
    assert response.json()["role"] == "COLLABORATOR"

def test_admin_can_access_me(override_admin):
    response = client.get("/api/users/me")
    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["role"] == "ADMIN"

def test_collaborator_can_access_analyze_balances(override_collab):
    # Mock excel processing
    import app.main as main
    import pandas as pd
    pd.read_excel = MagicMock(return_value=None)
    main.parse_balance_df = MagicMock(return_value={})
    main.compute_financial_statements = MagicMock(return_value={})
    
    # Create a dummy excel file
    import io
    file_content = b"dummy content"
    file = io.BytesIO(file_content)
    
    response = client.post(
        "/api/analyze-balances",
        files={"file_n": ("test.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 200

def test_collaborator_can_access_generate_liasse(override_collab):
    # Mock engine and pdf service
    import app.main as main
    import pandas as pd
    pd.read_excel = MagicMock(return_value=None)
    main.parse_balance_df = MagicMock(return_value={"some": "data"})
    main.compute_financial_statements = MagicMock(return_value={})
    main.generate_liasse_pdf = MagicMock(return_value=b"fake pdf")
    
    # Create a dummy excel file
    import io
    file_content = b"dummy content"
    file = io.BytesIO(file_content)
    
    response = client.post(
        "/api/generate-liasse",
        files={"file_n": ("test.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"exercice": "2024"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
