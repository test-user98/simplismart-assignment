import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.scheduler import schedule_deployments

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

def test_scheduler(authenticated_user, cluster_id):
    # Create multiple deployments
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
    
    client.post("/deployments", 
                json={
                    "cluster_id": cluster_id,
                    "docker_image": "redis:latest",
                    "required_ram": 2048,
                    "required_cpu": 2,
                    "required_gpu": 0,
                    "priority": 2
                },
                headers={"Authorization": f"Bearer {authenticated_user}"})
    
    # Run the scheduler
    schedule_deployments()
    
    # Check the status of deployments
    response = client.get(f"/clusters/{cluster_id}/deployments", headers={"Authorization": f"Bearer {authenticated_user}"})
    deployments = response.json()
    
    assert len(deployments) == 2
    assert deployments[0]["status"] == "running"  # Higher priority deployment should be running
    assert deployments[1]["status"] == "running"  # Lower priority deployment should also be running as there are enough resources

def test_scheduler_resource_constraints(authenticated_user, cluster_id):
    # Create deployments that exceed cluster resources
    client.post("/deployments", 
                json={
                    "cluster_id": cluster_id,
                    "docker_image": "large-app:latest",
                    "required_ram": 8192,
                    "required_cpu": 4,
                    "required_gpu": 1,
                    "priority": 1
                },
                headers={"Authorization": f"Bearer {authenticated_user}"})
    
    client.post("/deployments", 
                json={
                    "cluster_id": cluster_id,
                    "docker_image": "medium-app:latest",
                    "required_ram": 4096,
                    "required_cpu": 2,
                    "required_gpu": 1,
                    "priority": 2
                },
                headers={"Authorization": f"Bearer {authenticated_user}"})
    
    client.post("/deployments", 
                json={
                    "cluster_id": cluster_id,
                    "docker_image": "small-app:latest",
                    "required_ram": 1024,
                    "required_cpu": 1,
                    "required_gpu": 0,
                    "priority": 3
                },
                headers={"Authorization": f"Bearer {authenticated_user}"})
    
    # Run the scheduler
    schedule_deployments()
    
    # Check the status of deployments
    response = client.get(f"/clusters/{cluster_id}/deployments", headers={"Authorization": f"Bearer {authenticated_user}"})
    deployments = response.json()
    
    assert len(deployments) == 3
    assert deployments[0]["status"] == "running"  # Highest priority (large-app) should be running
    assert deployments[1]["status"] == "pending"  # Medium priority should be pending due to lack of resources
    assert deployments[2]["status"] == "running"  # Lowest priority (small-app) should be running as it fits in remaining resources