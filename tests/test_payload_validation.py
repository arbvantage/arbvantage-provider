import unittest
from pydantic import ValidationError
from typing import Dict, List
from arbvantage_provider import ProviderResponse
from pydantic import BaseModel, Field

class NotificationSettings(BaseModel):
    email: bool = Field(..., description="Enable email notifications")
    sms: bool = Field(..., description="Enable SMS notifications")

class UserProfile(BaseModel):
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    settings: Dict[str, str] = Field(default_factory=dict, description="User settings")
    notifications: NotificationSettings

class CreateUserPayload(BaseModel):
    username: str = Field(..., min_length=3, description="Username")
    profile: UserProfile
    tags: List[str] = Field(default_factory=list, description="List of tags")

class AccountInfo(BaseModel):
    api_key: str = Field(..., min_length=32, description="API key for authentication")
    permissions: Dict[str, bool] = Field(default_factory=dict, description="Permissions map")

class TestNestedPayloadValidation(unittest.TestCase):
    def test_valid_payload(self):
        payload = {
            "username": "testuser",
            "profile": {
                "first_name": "John",
                "last_name": "Doe",
                "settings": {"theme": "dark"},
                "notifications": {"email": True, "sms": False}
            },
            "tags": ["a", "b"]
        }
        obj = CreateUserPayload(**payload)
        self.assertEqual(obj.username, "testuser")
        self.assertTrue(obj.profile.notifications.email)
        self.assertFalse(obj.profile.notifications.sms)
        self.assertEqual(obj.tags, ["a", "b"])

    def test_missing_nested_field(self):
        payload = {
            "username": "testuser",
            "profile": {
                "first_name": "John",
                "last_name": "Doe",
                "settings": {"theme": "dark"}
                # notifications missing
            },
            "tags": ["a", "b"]
        }
        with self.assertRaises(ValidationError) as ctx:
            CreateUserPayload(**payload)
        self.assertIn("notifications", str(ctx.exception))

    def test_type_error_in_nested_field(self):
        payload = {
            "username": "testuser",
            "profile": {
                "first_name": "John",
                "last_name": "Doe",
                "settings": {"theme": "dark"},
                "notifications": {"email": "yes", "sms": False}  # email should be bool
            },
            "tags": ["a", "b"]
        }
        with self.assertRaises(ValidationError) as ctx:
            CreateUserPayload(**payload)
        self.assertIn("email", str(ctx.exception))

    def test_account_schema(self):
        account = {
            "api_key": "x" * 32,
            "permissions": {"admin": True, "edit": False}
        }
        obj = AccountInfo(**account)
        self.assertEqual(obj.api_key, "x" * 32)
        self.assertTrue(obj.permissions["admin"])
        self.assertFalse(obj.permissions["edit"])

if __name__ == "__main__":
    unittest.main() 