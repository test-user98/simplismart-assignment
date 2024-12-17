# Deployment Service

## Overview

## Problem statement: ([url](https://simplismart.notion.site/Backend-Engineering-Assignment-af3b93a1f3df454f87042bbd7cb1a537))
## File Structure

- `app/`
  - `__init__.py`: Initializes the application
  - `main.py`: Entry point of the application, sets up FastAPI and includes routers
  - `models.py`: Defines SQLAlchemy ORM models for database tables
  - `schemas.py`: Defines Pydantic models for request/response validation and serialization
  - `database.py`: Sets up database connection and session
  - `auth.py`: Handles user authentication and authorization
  - `cluster.py`: Manages cluster-related operations
  - `deployment.py`: Manages deployment-related operations
  - `scheduler.py`: Implements the scheduling algorithm for deployments

## Features

1. User Authentication and Organization Management
   - User registration and login, we are using jwt auth, (/token endpoint to get the token, default expiration is 30 mins)
   - Organization creation and joining via invite code

2. Cluster Management
   - Create clusters with specified resources (RAM, CPU, GPU)
   - Track available and allocated resources

3. Deployment Management
   - Create deployments for clusters
   - Queue deployments when resources are unavailable

4. Scheduling Algorithm
   - Prioritize higher priority deployments
   - Efficiently utilize available resources
   - Maximize the number of successful deployments

## Main Endpoints

1. Authentication
   - `POST /register`: Register a new user
   - `POST /token`: Login and receive an access token
   - `POST /join-organization`: Join an organization using an invite code (invite code is passed via query params)

2. Cluster Management
   - `POST /clusters`: Create a new cluster
   - `GET /clusters/{cluster_id}`: Get details of a specific cluster

3. Deployment Management
   - `POST /deployments`: Create a new deployment
   - `GET /deployments/{deployment_id}`: Get details of a specific deployment
   - `GET /clusters/{cluster_id}/deployments`: Get all deployments for a cluster

4. Scheduler
   - `POST /trigger-scheduler`: Manually trigger the scheduling algorithm (this is not required)

## Setup and Running

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your PostgreSQL database and update the `DATABASE_URL` in `app/database.py`.

3. Set up Redis and update the connection details in `app/deployment.py` and `app/scheduler.py`.

4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

5. The API will be available at `http://localhost:8000`.


## Notes

- The scheduler runs automatically at regular intervals to process pending deployments.
- Manual updates to the database may require triggering the scheduler to see immediate effects.
- Ensure proper error handling and input validation in a production environment.
