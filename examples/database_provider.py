"""
Database Provider Example

This example demonstrates how to implement a provider with database support using the Arbvantage Provider Framework and explicit Pydantic schemas.
It shows how to:
1. Use SQLAlchemy for database access
2. Register actions for CRUD operations
3. Handle transactions and error handling

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "database-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
- DATABASE_URL: SQLAlchemy database URL (defaults to "sqlite:///example.db")

Why is this important?
-----------------------------------
This example shows how to integrate persistent storage, manage transactions, and structure CRUD actions for real-world use cases.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from arbvantage_provider import Provider, ProviderResponse

# Create base class for models
Base = declarative_base()

class User(Base):
    """User model for database operations."""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Pydantic Schemas ---
class CreateUserPayload(BaseModel):
    name: str = Field(..., min_length=1, description="User name")
    email: str = Field(..., min_length=3, description="User email")

class GetUserPayload(BaseModel):
    user_id: int = Field(..., description="User ID")

class UpdateUserPayload(BaseModel):
    user_id: int = Field(..., description="User ID")
    name: str = Field(..., min_length=1, description="User name")
    email: str = Field(..., min_length=3, description="User email")

class DeleteUserPayload(BaseModel):
    user_id: int = Field(..., description="User ID")

class ListUsersPayload(BaseModel):
    pass

class DatabaseProvider(Provider):
    """
    Provider with database support using explicit Pydantic schemas.
    """
    def __init__(self):
        super().__init__(
            name="database-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        self.engine = create_engine(
            os.getenv("DATABASE_URL", "sqlite:///example.db"),
            echo=True
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._register_database_actions()

    def _register_database_actions(self):
        @self.actions.register(
            name="create_user",
            description="Create a new user",
            payload_schema=CreateUserPayload
        )
        def create_user(payload: CreateUserPayload) -> ProviderResponse:
            session = self.Session()
            try:
                user = User(
                    name=payload.name,
                    email=payload.email
                )
                session.add(user)
                session.commit()
                return ProviderResponse(
                    status="success",
                    message="User created successfully",
                    data={
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "created_at": user.created_at.isoformat()
                    }
                )
            except Exception as e:
                session.rollback()
                self.logger.error("Error creating user", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to create user: {str(e)}"
                )
            finally:
                session.close()

        @self.actions.register(
            name="get_user",
            description="Get user by ID",
            payload_schema=GetUserPayload
        )
        def get_user(payload: GetUserPayload) -> ProviderResponse:
            session = self.Session()
            try:
                user = session.query(User).get(payload.user_id)
                if not user:
                    return ProviderResponse(
                        status="error",
                        message="User not found"
                    )
                return ProviderResponse(
                    status="success",
                    message="User retrieved successfully",
                    data={
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat()
                    }
                )
            except Exception as e:
                self.logger.error("Error getting user", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to get user: {str(e)}"
                )
            finally:
                session.close()

        @self.actions.register(
            name="update_user",
            description="Update user data",
            payload_schema=UpdateUserPayload
        )
        def update_user(payload: UpdateUserPayload) -> ProviderResponse:
            session = self.Session()
            try:
                user = session.query(User).get(payload.user_id)
                if not user:
                    return ProviderResponse(
                        status="error",
                        message="User not found"
                    )
                user.name = payload.name
                user.email = payload.email
                session.commit()
                return ProviderResponse(
                    status="success",
                    message="User updated successfully",
                    data={
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "updated_at": user.updated_at.isoformat()
                    }
                )
            except Exception as e:
                session.rollback()
                self.logger.error("Error updating user", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to update user: {str(e)}"
                )
            finally:
                session.close()

        @self.actions.register(
            name="delete_user",
            description="Delete user",
            payload_schema=DeleteUserPayload
        )
        def delete_user(payload: DeleteUserPayload) -> ProviderResponse:
            session = self.Session()
            try:
                user = session.query(User).get(payload.user_id)
                if not user:
                    return ProviderResponse(
                        status="error",
                        message="User not found"
                    )
                session.delete(user)
                session.commit()
                return ProviderResponse(
                    status="success",
                    message="User deleted successfully",
                    data={"id": payload.user_id}
                )
            except Exception as e:
                session.rollback()
                self.logger.error("Error deleting user", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to delete user: {str(e)}"
                )
            finally:
                session.close()

        @self.actions.register(
            name="list_users",
            description="List all users",
            payload_schema=ListUsersPayload
        )
        def list_users(payload: ListUsersPayload) -> ProviderResponse:
            session = self.Session()
            try:
                users = session.query(User).all()
                user_list = [
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat()
                    }
                    for user in users
                ]
                return ProviderResponse(
                    status="success",
                    message="Users listed successfully",
                    data={"users": user_list}
                )
            except Exception as e:
                self.logger.error("Error listing users", error=str(e))
                return ProviderResponse(
                    status="error",
                    message=f"Failed to list users: {str(e)}"
                )
            finally:
                session.close()

if __name__ == "__main__":
    provider = DatabaseProvider()
    provider.start() 