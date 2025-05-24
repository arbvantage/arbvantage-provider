"""
Database Provider Example

This example demonstrates how to implement a provider with database support using the Arbvantage Provider Framework.
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
from typing import Dict, Any, List, Optional
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

class DatabaseProvider(Provider):
    """
    Provider with database support.
    
    This provider demonstrates how to implement database operations.
    It uses SQLAlchemy for database access and provides CRUD operations.
    
    Why is this important?
    -----------------------------------
    Shows how to persist data, manage transactions, and structure actions for real-world business logic.
    """
    
    def __init__(self):
        super().__init__(
            name="database-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Initialize database connection
        self.engine = create_engine(
            os.getenv("DATABASE_URL", "sqlite:///example.db"),
            echo=True
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
        # Register database actions
        self._register_database_actions()
        
    def _register_database_actions(self):
        """Register database actions."""
        
        @self.actions.register(
            name="create_user",
            description="Create a new user",
            payload_schema={"name": str, "email": str}
        )
        def create_user(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Create a new user in the database.
            
            Args:
                payload (dict): Must contain 'name' and 'email'.
            Returns:
                ProviderResponse: status 'success' and created user data, or 'error' on failure.
            Why is this important?
            -----------------------------------
            Shows how to insert data and handle unique constraints and errors.
            """
            session = self.Session()
            try:
                user = User(
                    name=payload["name"],
                    email=payload["email"]
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
            payload_schema={"user_id": int}
        )
        def get_user(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Get user by ID from the database.
            
            Args:
                payload (dict): Must contain 'user_id'.
            Returns:
                ProviderResponse: status 'success' and user data, or 'error' if not found.
            Why is this important?
            -----------------------------------
            Shows how to retrieve data and handle missing records.
            """
            session = self.Session()
            try:
                user = session.query(User).get(payload["user_id"])
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
            payload_schema={"user_id": int, "name": str, "email": str}
        )
        def update_user(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Update user data in the database.
            
            Args:
                payload (dict): Must contain 'user_id', 'name', and 'email'.
            Returns:
                ProviderResponse: status 'success' and updated user data, or 'error' if not found.
            Why is this important?
            -----------------------------------
            Shows how to update records and handle errors/rollbacks.
            """
            session = self.Session()
            try:
                user = session.query(User).get(payload["user_id"])
                if not user:
                    return ProviderResponse(
                        status="error",
                        message="User not found"
                    )
                    
                user.name = payload["name"]
                user.email = payload["email"]
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
            payload_schema={"user_id": int}
        )
        def delete_user(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Delete user from the database.
            
            Args:
                payload (dict): Must contain 'user_id'.
            Returns:
                ProviderResponse: status 'success' or 'error' if not found.
            Why is this important?
            -----------------------------------
            Shows how to delete records and handle errors/rollbacks.
            """
            session = self.Session()
            try:
                user = session.query(User).get(payload["user_id"])
                if not user:
                    return ProviderResponse(
                        status="error",
                        message="User not found"
                    )
                    
                session.delete(user)
                session.commit()
                
                return ProviderResponse(
                    status="success",
                    message="User deleted successfully"
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
            payload_schema={}
        )
        def list_users(payload: Dict[str, Any]) -> ProviderResponse:
            """
            List all users from the database.
            
            Args:
                payload (dict): Not used for this action.
            Returns:
                ProviderResponse: status 'success' and list of users.
            Why is this important?
            -----------------------------------
            Shows how to return collections of records.
            """
            session = self.Session()
            try:
                users = session.query(User).all()
                data = [
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
                    data=data
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
    """
    Run the provider if this script is executed directly.
    
    Why is this important?
    -----------------------------------
    This allows you to test database actions and persistence before integrating with the hub.
    """
    provider = DatabaseProvider()
    provider.start() 