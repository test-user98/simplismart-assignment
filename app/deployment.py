from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from typing import List
import redis

router = APIRouter()

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@router.post("/deployments", response_model=schemas.Deployment)
def create_deployment(deployment: schemas.DeploymentCreate, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if cluster exists and user has access to it
    cluster = db.query(models.Cluster).filter(models.Cluster.id == deployment.cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.user_id == current_user.id,
        models.UserOrganization.organization_id == cluster.organization_id
    ).first()
    if not user_org:
        raise HTTPException(status_code=403, detail="User does not have access to this cluster")

    db_deployment = models.Deployment(**deployment.dict(), status="pending")
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)

    # Add deployment to Redis queue
    redis_client.zadd("deployment_queue", {db_deployment.id: deployment.priority})

    return db_deployment

@router.get("/deployments/{deployment_id}", response_model=schemas.Deployment)
def get_deployment(deployment_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    deployment = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check if user has access to the deployment's cluster
    cluster = db.query(models.Cluster).filter(models.Cluster.id == deployment.cluster_id).first()
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.user_id == current_user.id,
        models.UserOrganization.organization_id == cluster.organization_id
    ).first()
    if not user_org:
        raise HTTPException(status_code=403, detail="User does not have access to this deployment")
    
    return deployment

@router.get("/clusters/{cluster_id}/deployments", response_model=List[schemas.Deployment])
def get_cluster_deployments(
    cluster_id: int, 
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the cluster exists
    cluster = db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Check if the user has access to this cluster
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.user_id == current_user.id,
        models.UserOrganization.organization_id == cluster.organization_id
    ).first()
    if not user_org:
        raise HTTPException(status_code=403, detail="User does not have access to this cluster")
    
    # Fetch all deployments for the cluster
    deployments = db.query(models.Deployment).filter(models.Deployment.cluster_id == cluster_id).all()
    
    return deployments