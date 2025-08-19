# AuthX Authentication Implementation

This project now uses **AuthX** for production-grade JWT authentication with refresh token rotation.

## Features

- ✅ **JWT Access & Refresh Tokens**: Secure token-based authentication
- ✅ **Automatic Token Refresh**: Built-in refresh token rotation
- ✅ **Cookie & Header Support**: Tokens can be sent via cookies or Authorization headers
- ✅ **Password Hashing**: Secure bcrypt password hashing
- ✅ **User Management**: Complete user registration, login, and profile management
- ✅ **Protected Routes**: Easy dependency injection for authenticated endpoints

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
cd backend
python run_server.py
```

The API will be available at `http://localhost:8000`

### 3. Test the Authentication

Use the provided test files:
- `authx_tests.http` - HTTP requests for VS Code REST Client
- `test_authx.py` - Python test script

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and get tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `POST` | `/auth/logout` | Logout (clear cookies) |
| `GET` | `/auth/me` | Get current user info |
| `POST` | `/auth/change-password` | Change user password |
| `GET` | `/auth/verify-token` | Verify token validity |

### Protected Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/protected` | Example protected endpoint |
| `GET` | `/health` | Health check (public) |

## Usage Examples

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 3. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Configuration

AuthX settings are configured in `app/core/config.py`:

```python
# AuthX Configuration
AUTHX_SECRET_KEY: str = secrets.token_urlsafe(32)
AUTHX_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
AUTHX_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
AUTHX_JWT_ALGORITHM: str = "HS256"
```

## Project Structure

```
backend/
├── app/
│   ├── auth/
│   │   ├── authx_config.py          # AuthX configuration
│   ├── core/
│   │   ├── config.py                # Application settings
│   │   └── database.py              # Database setup
│   ├── models/
│   │   └── user.py                  # User model
│   ├── routers/
│   │   └── auth.py                  # Authentication routes
│   ├── schemas/
│   │   ├── auth.py                  # Auth schemas
│   │   └── user.py                  # User schemas
│   ├── services/
│   │   └── auth_service.py          # Authentication service
│   └── main.py                      # FastAPI application
├── authx_tests.http                 # HTTP test requests
├── test_authx.py                    # Python test script
└── requirements.txt                 # Dependencies
```

## Security Features

### Token Management
- **Access Tokens**: Short-lived (30 minutes) for API access
- **Refresh Tokens**: Long-lived (7 days) for token renewal
- **Automatic Rotation**: New refresh token issued on each refresh

### Password Security
- **Bcrypt Hashing**: Industry-standard password hashing
- **Salt Generation**: Automatic salt generation for each password

### Cookie Security
- **HttpOnly**: Prevents XSS attacks
- **Secure**: HTTPS-only transmission (configurable)
- **SameSite**: CSRF protection

## Development

### Adding Protected Routes

To protect a route, simply add the `get_current_user` dependency:

```python
from app.services.auth_service import get_current_user
from app.models.user import User

@app.get("/my-protected-route")
async def my_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}!"}
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
AUTHX_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./mydatabase.db
DEBUG=True
```

## Migration from FastAPI-Users

The AuthX implementation replaces the previous FastAPI-Users setup with:
- Simplified configuration
- Better performance
- More flexibility
- Production-ready token rotation
- Enhanced security features

## Testing

Run the test script to verify everything works:

```bash
cd backend
python test_authx.py
```

Or use the HTTP test file with VS Code REST Client extension.
