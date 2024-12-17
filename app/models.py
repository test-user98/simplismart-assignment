from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    organizations = relationship("UserOrganization", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    invite_code = Column(String, unique=True, index=True)
    users = relationship("UserOrganization", back_populates="organization")
    clusters = relationship("Cluster", back_populates="organization")

class UserOrganization(Base):
    __tablename__ = "user_organizations"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), primary_key=True)
    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="users")

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String, index=True)
    total_ram = Column(Integer)
    total_cpu = Column(Integer)
    total_gpu = Column(Integer)
    available_ram = Column(Integer)
    available_cpu = Column(Integer)
    available_gpu = Column(Integer)
    organization = relationship("Organization", back_populates="clusters")
    deployments = relationship("Deployment", back_populates="cluster")

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"))
    docker_image = Column(String)
    required_ram = Column(Integer)
    required_cpu = Column(Integer)
    required_gpu = Column(Integer)
    priority = Column(Integer)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cluster = relationship("Cluster", back_populates="deployments")