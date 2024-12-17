from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session, sessionmaker
from app import models
from app.database import engine
import redis
from app.auth import get_current_user
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
router = APIRouter()

SCHEDULER_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL", 60)) 

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)
async def schedule_deployments():
    db = SessionLocal()  # Create a session manually
    try:
        # getting pending deployments
        pending_deployments = redis_client.zrange("deployment_queue", 0, -1, withscores=True)
        # print(f"Processing deployments: {pending_deployments}")
        
        for deployment_id, priority in pending_deployments:
            deployment = db.query(models.Deployment).filter(models.Deployment.id == int(deployment_id)).first()
            # print(f"priorty depoloyment {deployment}, {priority}")
            if not deployment:
                print(f"No deployment found for {deployment_id}, removing from queue")
                redis_client.zrem("deployment_queue", deployment_id)  # Clean up invalid entries
                continue

            cluster = db.query(models.Cluster).filter(models.Cluster.id == deployment.cluster_id).first()
            if not cluster:
                print(f"No cluster found for deployment {deployment_id}")
                continue

            # Check resource availability
            if (cluster.available_ram >= deployment.required_ram and
                cluster.available_cpu >= deployment.required_cpu and
                cluster.available_gpu >= deployment.required_gpu):
                
                # Allocate resources
                cluster.available_ram -= deployment.required_ram
                cluster.available_cpu -= deployment.required_cpu
                cluster.available_gpu -= deployment.required_gpu

                # Update deployment status
                deployment.status = "running"

                # Remove from Redis queue
                redis_client.zrem("deployment_queue", deployment_id)

                print(f"[SUCCESS]: Deployment {deployment_id} got scheduled ")
            else:
                print(f"Insufficient resources for deployment {deployment_id}")

        db.commit()
    except Exception as e:
        print(f"Error during scheduling: {e}")
    finally:
        db.close()


@router.post("/trigger-scheduler")
async def trigger_scheduler(current_user: models.User = Depends(get_current_user)):
    await schedule_deployments()
    return { "success": True, "message": "Scheduler triggered successfully"}


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(schedule_deployments, 'interval', seconds=SCHEDULER_INTERVAL)
    scheduler.start()
    print("Scheduler started!")

