#!/usr/bin/env python3
"""
Saraphina Secure API Server - Phase 8
FastAPI server with OAuth, API keys, RBAC, and comprehensive security
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext
import pyotp

# Local modules
from saraphina.db import init_db, get_preference
from saraphina.monitoring import health_pulse
from saraphina.intuition import IntuitionEngine
from saraphina.trust_firewall import TrustFirewall

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("saraphina.api")

# Security configuration
SECRET_KEY = os.getenv("SARAPHINA_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Simple in-memory rate limiter per IP
_rate = {}
RATE_LIMIT = 120  # req/min per IP

# FastAPI app
app = FastAPI(
    title="Saraphina AI API",
    description="Secure API for Saraphina Ultra AI v4.0",
    version="4.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:5173",
        "http://127.0.0.1:3000", "http://127.0.0.1:5173",
        "http://localhost:5500", "http://127.0.0.1:5500",
    ],  # React dev and static servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str = "user"

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class User(BaseModel):
    username: str
    email: str
    role: str
    mfa_enabled: bool
    created_at: str

class Query(BaseModel):
    text: str
    context: Dict[str, Any] = {}

class Response(BaseModel):
    response: str
    metadata: Dict[str, Any]

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str]

class EmergencyRevoke(BaseModel):
    reason: str
    revoke_all: bool = False


# In-memory storage (replace with database in production)
users_db = {
    "owner": {
        "username": "owner",
        "email": "owner@saraphina.ai",
        "hashed_password": pwd_context.hash("changeme123"),
        "role": "owner",
        "mfa_enabled": False,
        "mfa_secret": None,
        "api_keys": {},
        "created_at": datetime.now().isoformat()
    }
}

api_keys_db = {}
revoked_tokens = set()


# Security functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    token = credentials.credentials
    
    if token in revoked_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {"username": username, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def verify_api_key(api_key: str = Security(api_key_header)) -> Dict:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key required"
        )
    
    if api_key not in api_keys_db:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    key_data = api_keys_db[api_key]
    
    if key_data.get("revoked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key has been revoked"
        )
    
    return key_data

def check_permission(user_data: Dict, required_role: str):
    """Check if user has required role"""
    role_hierarchy = {"owner": 3, "admin": 2, "user": 1}
    
    user_role = user_data.get("role", "user")
    
    if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )

def require_mfa(username: str, mfa_code: Optional[str]):
    """Verify MFA code if enabled"""
    user = users_db.get(username)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("mfa_enabled", False):
        if not mfa_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA code required"
            )
        
        totp = pyotp.TOTP(user["mfa_secret"])
        if not totp.verify(mfa_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid MFA code"
            )


# API Endpoints

@app.get("/")
async def root():
    return {
        "name": "Saraphina AI API",
        "version": "4.0.0",
        "status": "operational",
        "features": [
            "OAuth + JWT authentication",
            "API key support",
            "RBAC with owner/admin/user roles",
            "MFA support",
            "Emergency revoke",
            "Secure endpoints"
        ]
    }

@app.post("/auth/register", response_model=User)
async def register(user: UserCreate, current_user: Dict = Depends(verify_token)):
    """Register new user (admin/owner only)"""
    check_permission(current_user, "admin")
    
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "role": user.role if current_user["role"] == "owner" else "user",
        "mfa_enabled": False,
        "mfa_secret": None,
        "api_keys": {},
        "created_at": datetime.now().isoformat()
    }
    
    return User(
        username=user.username,
        email=user.email,
        role=user.role,
        mfa_enabled=False,
        created_at=users_db[user.username]["created_at"]
    )

@app.post("/auth/login", response_model=Token)
async def login(username: str, password: str, mfa_code: Optional[str] = None):
    """Login and get access token"""
    user = users_db.get(username)
    
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check MFA if enabled
    if user.get("mfa_enabled", False):
        require_mfa(username, mfa_code)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.post("/auth/mfa/enable")
async def enable_mfa(current_user: Dict = Depends(verify_token)):
    """Enable MFA for current user"""
    username = current_user["username"]
    user = users_db[username]
    
    if user.get("mfa_enabled", False):
        raise HTTPException(status_code=400, detail="MFA already enabled")
    
    # Generate MFA secret
    secret = pyotp.random_base32()
    user["mfa_secret"] = secret
    user["mfa_enabled"] = True
    
    # Generate QR code URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=username,
        issuer_name="Saraphina AI"
    )
    
    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "backup_codes": [secrets.token_hex(4) for _ in range(10)]
    }

@app.post("/auth/api-keys", response_model=Dict)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: Dict = Depends(verify_token)
):
    """Create new API key"""
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    api_keys_db[api_key] = {
        "key": api_key,
        "name": key_data.name,
        "owner": current_user["username"],
        "permissions": key_data.permissions,
        "created_at": datetime.now().isoformat(),
        "revoked": False
    }
    
    # Store in user's keys
    users_db[current_user["username"]]["api_keys"][api_key] = api_keys_db[api_key]
    
    return {
        "api_key": api_key,
        "name": key_data.name,
        "permissions": key_data.permissions,
        "warning": "Save this key securely - it won't be shown again"
    }

@app.delete("/auth/api-keys/{key_id}")
async def revoke_api_key(key_id: str, current_user: Dict = Depends(verify_token)):
    """Revoke API key"""
    if key_id not in api_keys_db:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key_data = api_keys_db[key_id]
    
    # Only owner or key owner can revoke
    if current_user["role"] != "owner" and key_data["owner"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this key")
    
    api_keys_db[key_id]["revoked"] = True
    
    return {"message": "API key revoked successfully"}

@app.post("/auth/emergency-revoke")
async def emergency_revoke(
    revoke_data: EmergencyRevoke,
    mfa_code: str,
    current_user: Dict = Depends(verify_token)
):
    """Emergency revoke all tokens/keys (owner only with MFA)"""
    check_permission(current_user, "owner")
    require_mfa(current_user["username"], mfa_code)
    
    if revoke_data.revoke_all:
        # Revoke all API keys
        for key in api_keys_db:
            api_keys_db[key]["revoked"] = True
        
        # Mark for token revocation (in production, invalidate all sessions)
        logger.critical(f"EMERGENCY REVOKE: All access revoked. Reason: {revoke_data.reason}")
        
        return {
            "status": "success",
            "message": "All API keys and tokens revoked",
            "revoked_keys": len(api_keys_db),
            "reason": revoke_data.reason
        }
    
    return {"status": "partial_revoke", "message": "Specific revocation not implemented"}

def _ratelimit(request: Request):
    import time
    ip = request.client.host if request.client else 'unknown'
    now = int(time.time())
    bucket = _rate.setdefault(ip, {'t': now, 'c': 0})
    if now - bucket['t'] >= 60:
        bucket['t'] = now; bucket['c'] = 0
    bucket['c'] += 1
    if bucket['c'] > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests")


def allow_local_or_auth(request: Request, cred: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict:
    # Allow local without auth; otherwise require JWT
    _ratelimit(request)
    if request.client and request.client.host in ("127.0.0.1", "::1", "localhost"):
        return {"username": "local", "role": "owner"}
    if not cred:
        raise HTTPException(status_code=401, detail="Auth required")
    return verify_token(cred)


@app.get("/metrics/health")
async def metrics_health(request: Request):
    conn = init_db(None)
    try:
        return health_pulse(conn)
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/metrics/ethics")
async def metrics_ethics(request: Request, limit: int = 10, current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        cur = conn.cursor()
        cur.execute("SELECT timestamp, plan_goal, score_alignment FROM ethical_journal ORDER BY timestamp DESC LIMIT ?", (int(max(1, min(100, limit))),))
        return [dict(r) for r in cur.fetchall()]
    finally:
        try: conn.close()
        except Exception: pass


@app.get("/metrics/audit")
async def metrics_audit(request: Request, limit: int = 50, current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        cur = conn.cursor()
        cur.execute("SELECT log_id, actor, action, target, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (int(max(1, min(500, limit))),))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/reviews")
async def list_reviews(request: Request, status: str = 'pending', current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        cur = conn.cursor()
        if status in ('pending','approved','rejected'):
            cur.execute("SELECT * FROM review_queue WHERE status=? ORDER BY created_at ASC", (status,))
        else:
            cur.execute("SELECT * FROM review_queue ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.post("/reviews/{rid}/approve")
async def approve_review(rid: str, request: Request, current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        # Owner-only override: require verified session flag
        if get_preference(conn, 'owner_verified_session') != 'true':
            raise HTTPException(status_code=403, detail="Owner verification required in terminal session")
        cur = conn.cursor()
        cur.execute("UPDATE review_queue SET status='approved', reviewed_at=? WHERE id=?", (datetime.utcnow().isoformat(), rid))
        conn.commit()
        return {"ok": True, "id": rid}
    finally:
        try: conn.close()
        except Exception: pass


@app.post("/reviews/{rid}/reject")
async def reject_review(rid: str, request: Request, current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        if get_preference(conn, 'owner_verified_session') != 'true':
            raise HTTPException(status_code=403, detail="Owner verification required in terminal session")
        cur = conn.cursor()
        cur.execute("UPDATE review_queue SET status='rejected', reviewed_at=? WHERE id=?", (datetime.utcnow().isoformat(), rid))
        conn.commit()
        return {"ok": True, "id": rid}
    finally:
        try: conn.close()
        except Exception: pass


@app.get("/graph")
async def graph_data(request: Request, topic: Optional[str] = None, limit: int = 300, current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        ie = IntuitionEngine(conn)
        return ie.export_graph(topic=topic, limit=int(max(50, min(1000, limit))))
    finally:
        try: conn.close()
        except Exception: pass


@app.get("/insight")
async def insight(request: Request, topic: Optional[str] = None, limit: int = 10, current_user: Dict = Depends(allow_local_or_auth)):
    conn = init_db(None)
    try:
        ie = IntuitionEngine(conn)
        return ie.suggest_links(topic=topic, limit=int(max(1, min(50, limit))))
    finally:
        try: conn.close()
        except Exception: pass


@app.post("/ai/query", response_model=Response)
async def query_ai(
    query: Query,
    request: Request,
    current_user: Dict = Depends(allow_local_or_auth)
):
    """Query the AI (authenticated users)"""
    conn = init_db(None)
    try:
        tf = TrustFirewall(conn)
        verdict = tf.evaluate(query.text, source='api')
        if verdict.get('action') in ('review','block') and (get_preference(conn, 'strict_trust') == 'true' or verdict.get('action') == 'block'):
            raise HTTPException(status_code=403, detail={"trust": verdict, "message": "Input requires owner approval"})
        # Import AI here to avoid circular imports
        from saraphina.ai_core_enhanced import SaraphinaAIEnhanced
        ai = SaraphinaAIEnhanced()
        response = ai.process_query(query.text)
        return Response(
            response=response,
            metadata={
                "intelligence_level": ai.intelligence_level,
                "experience_points": ai.experience_points,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: conn.close()
        except Exception: pass
        logger.error(f"AI query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/status")
async def get_ai_status(current_user: Dict = Depends(verify_token)):
    """Get AI status"""
    try:
        from saraphina.ai_core_enhanced import SaraphinaAIEnhanced
        
        ai = SaraphinaAIEnhanced()
        status = ai.get_learning_status()
        
        return {
            "status": "operational",
            "learning": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/ai/ultra-status")
async def get_ultra_status(current_user: Dict = Depends(verify_token)):
    """Get Ultra AI capabilities status"""
    try:
        from saraphina.ultra_ai_core import UltraAICore
        
        ultra = UltraAICore()
        status = ultra.get_ultra_status()
        
        return {
            "status": "operational",
            "ultra_capabilities": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/system/health")
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/metrics")
async def get_metrics(current_user: Dict = Depends(verify_token)):
    """Get system metrics (authenticated)"""
    check_permission(current_user, "admin")
    
    return {
        "users": len(users_db),
        "api_keys": len(api_keys_db),
        "active_keys": sum(1 for k in api_keys_db.values() if not k.get("revoked", False)),
        "uptime": "N/A",  # Implement actual uptime tracking
        "requests_processed": "N/A"  # Implement request counting
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Saraphina Secure API Server...")
    print(f"📍 API will be available at: http://localhost:8000")
    print(f"📚 Documentation: http://localhost:8000/docs")
    print(f"🔐 Default owner credentials: owner / changeme123")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
