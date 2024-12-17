from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    invite_code: str

class Organization(OrganizationBase):
    id: int

    class Config:
        orm_mode = True

class ClusterBase(BaseModel):
    name: str
    total_ram: int
    total_cpu: int
    total_gpu: int

class ClusterCreate(ClusterBase):
    pass

class Cluster(ClusterBase):
    id: int
    organization_id: int
    available_ram: int
    available_cpu: int
    available_gpu: int

    class Config:
        orm_mode = True

class DeploymentBase(BaseModel):
    docker_image: str
    required_ram: int
    required_cpu: int
    required_gpu: int
    priority: int

class DeploymentCreate(DeploymentBase):
    cluster_id: int

class Deployment(DeploymentBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True