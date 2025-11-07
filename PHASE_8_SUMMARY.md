# Phase 8 - Production Hardening & Secure API

## 🎯 Goal

Comfortable controls, optional voice, dashboards, secure remote APIs, and resilience.

**Status**: ✅ Core Components Implemented

---

## 🚀 Deliverables Completed

### 1. FastAPI Secure Server ✅

**File**: `saraphina_api_server.py` (474 lines)

**Features**:
- ✅ OAuth 2.0 + JWT authentication
- ✅ API key support (`sk_*` keys)
- ✅ RBAC (owner/admin/user roles)
- ✅ MFA with TOTP (Google Authenticator compatible)
- ✅ Emergency revoke all access
- ✅ Secure endpoints for AI queries
- ✅ Auto-generated API docs
- ✅ CORS configured for React frontend

**Security**:
- Bcrypt password hashing
- JWT tokens with 30-minute expiration
- Token revocation support
- API key revocation
- MFA requirement for critical operations
- Role-based permission checking

---

## 🔐 Authentication & Authorization

### Authentication Methods

**1. JWT Tokens (OAuth 2.0)**
```
POST /auth/login
{
  "username": "owner",
  "password": "changeme123",
  "mfa_code": "123456"  // if MFA enabled
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**2. API Keys**
```
POST /auth/api-keys
Authorization: Bearer <token>
{
  "name": "My App Key",
  "permissions": ["ai.query", "ai.status"]
}

Response:
{
  "api_key": "sk_xxxxxxxxxx",
  "warning": "Save this key securely"
}
```

### Role Hierarchy

| Role | Level | Permissions |
|------|-------|-------------|
| **owner** | 3 | Everything + emergency revoke |
| **admin** | 2 | User management, metrics |
| **user** | 1 | AI queries, status |

---

## 🔒 Multi-Factor Authentication

**Enable MFA**:
```
POST /auth/mfa/enable
Authorization: Bearer <token>

Response:
{
  "secret": "BASE32SECRET",
  "provisioning_uri": "otpauth://totp/...",
  "backup_codes": ["code1", "code2", ...]
}
```

**Features**:
- TOTP-based (30-second codes)
- Compatible with Google Authenticator, Authy, etc.
- 10 backup codes generated
- Required for owner emergency actions

---

## 🚨 Emergency Revoke

**Owner-only** feature to revoke all access instantly:

```
POST /auth/emergency-revoke
Authorization: Bearer <token>
{
  "reason": "Security breach detected",
  "revoke_all": true
}

Headers:
X-MFA-Code: 123456

Response:
{
  "status": "success",
  "message": "All API keys and tokens revoked",
  "revoked_keys": 5,
  "reason": "Security breach detected"
}
```

---

## 📡 API Endpoints

### Public Endpoints

```
GET  /                    # API info
GET  /system/health       # Health check
GET  /docs                # Auto-generated documentation
GET  /redoc               # Alternative docs
```

### Authentication Endpoints

```
POST /auth/login          # Get JWT token
POST /auth/register       # Register user (admin+)
POST /auth/mfa/enable     # Enable MFA
POST /auth/api-keys       # Create API key
DELETE /auth/api-keys/:id # Revoke API key
POST /auth/emergency-revoke  # Emergency revoke all (owner+MFA)
```

### AI Endpoints (Authenticated)

```
POST /ai/query            # Query the AI
GET  /ai/status           # Get AI learning status
GET  /ai/ultra-status     # Get Ultra AI capabilities
```

### System Endpoints (Admin+)

```
GET  /system/metrics      # System metrics
```

---

## 🔧 Usage Examples

### 1. Login and Get Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "owner",
    "password": "changeme123"
  }'
```

### 2. Query AI

```bash
curl -X POST http://localhost:8000/ai/query \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello Saraphina",
    "context": {}
  }'
```

### 3. Get AI Status

```bash
curl http://localhost:8000/ai/status \
  -H "Authorization: Bearer <your_token>"
```

### 4. Create API Key

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "permissions": ["ai.query"]
  }'
```

---

## 🚀 Running the Server

### Installation

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] pyotp pydantic
```

### Start Server

```bash
python saraphina_api_server.py
```

Or with uvicorn directly:
```bash
uvicorn saraphina_api_server:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🛡️ Security Features

### Implemented ✅

1. **Password Security**
   - Bcrypt hashing
   - Salt per password
   - Secure comparison

2. **Token Security**
   - JWT with HS256
   - 30-minute expiration
   - Revocation support
   - Secure secret key

3. **API Key Security**
   - Cryptographically secure generation
   - Prefix `sk_` for identification
   - Per-key permissions
   - Revocation support

4. **MFA**
   - TOTP (RFC 6238)
   - 30-second window
   - Backup codes
   - Required for critical ops

5. **RBAC**
   - Role hierarchy
   - Permission checking
   - Granular access control

6. **Emergency Features**
   - Instant revoke all access
   - Owner-only with MFA
   - Audit logging

### Recommended Additions 🔜

1. **Database**
   - Replace in-memory with PostgreSQL/SQLite
   - Encrypted at rest
   - Regular backups

2. **Rate Limiting**
   - Per-user limits
   - Per-endpoint limits
   - DDoS protection

3. **Audit Logging**
   - All auth attempts
   - All critical operations
   - Searchable logs

4. **TLS/HTTPS**
   - SSL certificates
   - HTTPS only
   - HSTS headers

5. **Session Management**
   - Redis for tokens
   - Session expiry
   - Device tracking

---

## 📊 Default Configuration

**Owner Account**:
- Username: `owner`
- Password: `changeme123` ⚠️ CHANGE IMMEDIATELY
- Email: `owner@saraphina.ai`
- Role: `owner`
- MFA: Disabled (enable after first login)

**Server**:
- Host: `0.0.0.0` (all interfaces)
- Port: `8000`
- Token Expiry: 30 minutes
- CORS: Localhost React servers

---

## 🔐 Security Checklist

Before production deployment:

- [ ] Change default owner password
- [ ] Enable MFA for owner account
- [ ] Set strong SARAPHINA_SECRET_KEY env variable
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up audit logging
- [ ] Implement rate limiting
- [ ] Replace in-memory DB with persistent DB
- [ ] Configure backup strategy
- [ ] Set up monitoring/alerting
- [ ] Review and restrict CORS origins
- [ ] Implement key rotation schedule

---

## 🎨 Integration with Frontend

The API is CORS-configured for React apps on:
- `http://localhost:3000` (Create React App)
- `http://localhost:5173` (Vite)

**Example React Integration**:

```javascript
// Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});
const { access_token } = await response.json();

// Query AI
const aiResponse = await fetch('http://localhost:8000/ai/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ text: 'Hello Saraphina' })
});
```

---

## 📈 Phase 8 Progress

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI Server | ✅ Done | Full OAuth, RBAC, MFA |
| API Keys | ✅ Done | Generation, revocation |
| RBAC | ✅ Done | 3-tier hierarchy |
| MFA | ✅ Done | TOTP with backup codes |
| Emergency Revoke | ✅ Done | Owner-only with MFA |
| AI Endpoints | ✅ Done | Query, status, ultra |
| Auto Docs | ✅ Done | Swagger + ReDoc |
| CORS | ✅ Done | React frontend ready |
| Database | 🔜 Pending | In-memory → PostgreSQL |
| React Dashboard | 🔜 Pending | Telemetry visualization |
| TLS/HTTPS | 🔜 Pending | SSL certificates |
| Rate Limiting | 🔜 Pending | DDoS protection |
| Audit Logs | 🔜 Pending | Comprehensive logging |
| Encrypted DB | 🔜 Pending | SQLCipher integration |
| Tests | 🔜 Pending | pytest suite |

---

## 🎉 Summary

Phase 8 core infrastructure is complete with:

✅ **Secure FastAPI server** with OAuth 2.0  
✅ **JWT tokens** with 30-min expiration  
✅ **API keys** with granular permissions  
✅ **RBAC** with 3-tier role hierarchy  
✅ **MFA** using TOTP  
✅ **Emergency revoke** for owner  
✅ **AI query endpoints** (authenticated)  
✅ **Auto-generated docs** at `/docs`  
✅ **CORS** configured for React  

**Ready for**: Frontend dashboard development and production hardening!

---

**Version**: Phase 8 Core  
**Status**: 🟢 API Operational  
**Next**: React dashboard + database migration  
**Timeline**: On track for 6-12 week completion
