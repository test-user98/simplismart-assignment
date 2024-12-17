import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # i tested it using my local psql db
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def authenticated_user():
    client.post("/register", json={"username": "testuser", "password": "testpassword"})
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    return response.json()["access_token"]

@pytest.fixture
def cluster_id(authenticated_user):
    response = client.post("/clusters", 
                           json={"name": "TestCluster", "total_ram": 16384, "total_cpu": 8, "total_gpu": 2},
                           headers={"Authorization": f"Bearer {authenticated_user}"})
    return response.json()["id"]

def test_create_deployment(authenticated_user, cluster_id):
    response = client.post("/deployments", 
                           json={
                               "cluster_id": cluster_id,
                               "docker_image": "nginx:latest",
                               "required_ram": 1024,
                               "required_cpu": 2,
                               "required_gpu": 0,
                               "priority": 1
                           },
                           headers={"Authorization": f"Bearer {authenticated_user}"})
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

def test_get_deployment(authenticated_user, cluster_id):
    create_response = client.post("/deployments", 
                                  json={
                                      "cluster_id": cluster_id,
                                      "docker_image": "nginx:latest",
                                      "required_ram": 1024,
                                      "required_cpu": 2,
                                      "required_gpu": 0,
                                      "priority": 1
                                  },
                                  headers={"Authorization": f"Bearer {authenticated_user}"})
    deployment_id = create_response.json()["id"]
    
    response = client.get(f"/deployments/{deployment_id}", headers={"Authorization": f"Bearer {authenticated_user}"})
    assert response.status_code == 200
    assert response.json()["docker_image"] == "nginx:latest"

def test_get_cluster_deployments(authenticated_user, cluster_id):
    client.post("/deployments", 
                json={
                    "cluster_id": cluster_id,
                    "docker_image": "nginx:latest",
                    "required_ram": 1024,
                    "required_cpu": 2,
                    "required_gpu": 0,
                    "priority": 1
                },
                headers={"Authorization": f"Bearer {authenticated_user}"})
    
    response = client.get(f"/clusters/{cluster_id}/deployments", headers={"Authorization": f"Bearer {authenticated_user}"})
    assert response.status_code == 200
    assert len(response.json()) == 1