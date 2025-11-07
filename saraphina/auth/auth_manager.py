"""
Multi-User Authentication & Role-Based Access Control (RBAC).
Supports JWT tokens, OAuth, device sharing, and team organizations.
"""
import jwt
import hashlib
import secrets
import time
from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum


class Role(Enum):
    """User roles in the system"""
    ADMIN = "admin"  # Full system access
    USER = "user"  # Standard user
    VIEWER = "viewer"  # Read-only access
    GUEST = "guest"  # Limited temporary access


class Permission(Enum):
    """Granular permissions"""
    VIEW_DEVICE = "view_device"
    TRACK_DEVICE = "track_device"
    RECOVER_DEVICE = "recover_device"
    MANAGE_DEVICE = "manage_device"
    DELETE_DEVICE = "delete_device"
    VIEW_TELEMETRY = "view_telemetry"
    VIEW_HISTORY = "view_history"
    MANAGE_USERS = "manage_users"
    MANAGE_ORG = "manage_org"
    ADMIN_ACCESS = "admin_access"


# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.USER: {
        Permission.VIEW_DEVICE,
        Permission.TRACK_DEVICE,
        Permission.RECOVER_DEVICE,
        Permission.MANAGE_DEVICE,
        Permission.VIEW_TELEMETRY,
        Permission.VIEW_HISTORY,
    },
    Role.VIEWER: {
        Permission.VIEW_DEVICE,
        Permission.VIEW_TELEMETRY,
        Permission.VIEW_HISTORY,
    },
    Role.GUEST: {
        Permission.VIEW_DEVICE,
    },
}


@dataclass
class User:
    """User account"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: Role
    org_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class Organization:
    """Team/family organization"""
    org_id: str
    name: str
    owner_user_id: str
    member_user_ids: List[str] = field(default_factory=list)
    shared_device_ids: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class DeviceShare:
    """Device sharing permissions"""
    device_id: str
    owner_user_id: str
    shared_with_user_id: str
    permissions: Set[Permission]
    expires_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)


class AuthManager:
    """Authentication and authorization manager"""
    
    JWT_SECRET = "saraphina-secret-key-change-in-production"  # TODO: Use env var
    JWT_ALGORITHM = "HS256"
    TOKEN_EXPIRY_HOURS = 24
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.organizations: Dict[str, Organization] = {}
        self.device_shares: List[DeviceShare] = []
        self.refresh_tokens: Dict[str, str] = {}  # refresh_token -> user_id
        
        # Create default admin
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_id = "admin-001"
        if admin_id not in self.users:
            self.users[admin_id] = User(
                user_id=admin_id,
                username="admin",
                email="admin@saraphina.local",
                password_hash=self._hash_password("admin123"),
                role=Role.ADMIN
            )
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "saraphina-salt"  # TODO: Use random salt per user
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash
    
    def register_user(self, username: str, email: str, password: str, role: Role = Role.USER) -> User:
        """Register new user"""
        user_id = f"user-{secrets.token_hex(8)}"
        
        # Check uniqueness
        if any(u.username == username for u in self.users.values()):
            raise ValueError("Username already exists")
        if any(u.email == email for u in self.users.values()):
            raise ValueError("Email already exists")
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role=role
        )
        self.users[user_id] = user
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        user = next((u for u in self.users.values() if u.username == username), None)
        if not user or not user.is_active:
            return None
        
        if not self._verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = time.time()
        
        # Generate JWT
        return self._generate_token(user)
    
    def _generate_token(self, user: User) -> str:
        """Generate JWT access token"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRY_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate refresh token"""
        refresh_token = secrets.token_urlsafe(32)
        self.refresh_tokens[refresh_token] = user_id
        return refresh_token
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Get new access token from refresh token"""
        user_id = self.refresh_tokens.get(refresh_token)
        if not user_id or user_id not in self.users:
            return None
        
        user = self.users[user_id]
        return self._generate_token(user)
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        return permission in ROLE_PERMISSIONS.get(user.role, set())
    
    def can_access_device(self, user_id: str, device_id: str, permission: Permission) -> bool:
        """Check if user can access device with given permission"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        # Admin can access everything
        if user.role == Role.ADMIN:
            return True
        
        # Check if user has the base permission
        if not self.has_permission(user_id, permission):
            return False
        
        # Check device ownership (would need device registry integration)
        # For now, check shared devices
        
        # Check explicit device shares
        for share in self.device_shares:
            if share.device_id == device_id and share.shared_with_user_id == user_id:
                # Check expiry
                if share.expires_at and time.time() > share.expires_at:
                    continue
                if permission in share.permissions:
                    return True
        
        # Check organization shares
        if user.org_id:
            org = self.organizations.get(user.org_id)
            if org and device_id in org.shared_device_ids:
                return True
        
        return False
    
    def share_device(self, device_id: str, owner_user_id: str, target_user_id: str, 
                     permissions: List[Permission], expires_in_hours: Optional[int] = None):
        """Share device with another user"""
        expires_at = None
        if expires_in_hours:
            expires_at = time.time() + (expires_in_hours * 3600)
        
        share = DeviceShare(
            device_id=device_id,
            owner_user_id=owner_user_id,
            shared_with_user_id=target_user_id,
            permissions=set(permissions),
            expires_at=expires_at
        )
        self.device_shares.append(share)
        return share
    
    def create_organization(self, name: str, owner_user_id: str) -> Organization:
        """Create new organization"""
        org_id = f"org-{secrets.token_hex(8)}"
        org = Organization(
            org_id=org_id,
            name=name,
            owner_user_id=owner_user_id,
            member_user_ids=[owner_user_id]
        )
        self.organizations[org_id] = org
        
        # Update user
        if owner_user_id in self.users:
            self.users[owner_user_id].org_id = org_id
        
        return org
    
    def add_org_member(self, org_id: str, user_id: str, requester_user_id: str):
        """Add member to organization"""
        org = self.organizations.get(org_id)
        if not org:
            raise ValueError("Organization not found")
        
        # Check permission
        if requester_user_id != org.owner_user_id:
            if not self.has_permission(requester_user_id, Permission.MANAGE_ORG):
                raise PermissionError("Not authorized to add members")
        
        if user_id not in org.member_user_ids:
            org.member_user_ids.append(user_id)
        
        # Update user
        if user_id in self.users:
            self.users[user_id].org_id = org_id
    
    def share_device_with_org(self, org_id: str, device_id: str, owner_user_id: str):
        """Share device with entire organization"""
        org = self.organizations.get(org_id)
        if not org:
            raise ValueError("Organization not found")
        
        if device_id not in org.shared_device_ids:
            org.shared_device_ids.append(device_id)
    
    def get_user_devices(self, user_id: str) -> List[str]:
        """Get all devices user has access to"""
        devices = set()
        
        # Owned devices (would come from device registry)
        # devices.update(device_registry.get_user_devices(user_id))
        
        # Shared devices
        for share in self.device_shares:
            if share.shared_with_user_id == user_id:
                if not share.expires_at or time.time() <= share.expires_at:
                    devices.add(share.device_id)
        
        # Organization devices
        user = self.users.get(user_id)
        if user and user.org_id:
            org = self.organizations.get(user.org_id)
            if org:
                devices.update(org.shared_device_ids)
        
        return list(devices)


# Decorator for FastAPI routes
def require_auth(permission: Optional[Permission] = None):
    """Decorator to require authentication"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract token from request (kwargs would have request object)
            # Verify token and check permission
            # If valid, call func
            # Otherwise raise HTTPException
            return await func(*args, **kwargs)
        return wrapper
    return decorator
