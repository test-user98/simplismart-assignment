from fastapi import FastAPI
from app import auth, cluster, deployment, scheduler
from app.database import engine, Base

app = FastAPI()

# Create db tables
Base.metadata.create_all(bind=engine)

# incliding all routers
app.include_router(auth.router)
app.include_router(cluster.router)
app.include_router(deployment.router)

# Start scheduler
@app.on_event("startup")
async def startup_event():
    scheduler.start_scheduler()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)