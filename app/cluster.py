from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import get_current_user
from typing import List

router = APIRouter()

@router.post("/clusters", response_model=schemas.Cluster)
def create_cluster(cluster: schemas.ClusterCreate, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user belongs to an organization
    user_org = db.query(models.UserOrganization).filter(models.UserOrganization.user_id == current_user.id).first()
    if not user_org:
        raise HTTPException(status_code=400, detail="User does not belong to any organization")

    db_cluster = models.Cluster(
        **cluster.dict(),
        organization_id=user_org.organization_id,
        available_ram=cluster.total_ram,
        available_cpu=cluster.total_cpu,
        available_gpu=cluster.total_gpu
    )
    db.add(db_cluster)
    db.commit()
    db.refresh(db_cluster)
    return db_cluster


@router.get("/clusters", response_model=List[schemas.Cluster])
def get_all_clusters(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch all clusters for the user’s organization
    user_org = db.query(models.UserOrganization).filter(models.UserOrganization.user_id == current_user.id).first()
    if not user_org:
        raise HTTPException(status_code=400, detail="User does not belong to any organization")

    clusters = db.query(models.Cluster).filter(models.Cluster.organization_id == user_org.organization_id).all()
    
    return clusters



@router.get("/clusters/{cluster_id}", response_model=schemas.Cluster)
def get_cluster(cluster_id: int, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    cluster = db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Check if user has access to the cluster
    user_org = db.query(models.UserOrganization).filter(
        models.UserOrganization.user_id == current_user.id,
        models.UserOrganization.organization_id == cluster.organization_id
    ).first()
    if not user_org:
        raise HTTPException(status_code=403, detail="User does not have access to this cluster")
    
    return cluster