# Secure Authentication Service

A secure authentication service with enhanced security features for managing Azure AD tokens.

## Security Features

### Authentication

- OAuth2 implementation through Azure AD
- Token-based authentication
- Automatic token refresh
- Rate limiting to prevent brute force attacks
- Session management with Redis
- Logout mechanism
- Audit logging

### Authorization

- Role-based access control (RBAC)
- Permission-based access control
- User roles (admin, user)
- Permission decorators for route protection

### Data Protection

- Secure token storage with encryption
- Environment variable configuration
- Secure session management
- HTTPS enforcement
- Security headers
- Input validation
- Audit logging

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:

- Copy `.env.example` to `.env`
- Fill in the required configuration values

3. Start Redis server (required for session management)

4. Run the application:

```bash
python app.py
```

## API Endpoints

### Authentication

- `POST /requesttoken` - Request a new token
- `POST /logout` - Logout and invalidate session
- `GET /health` - Health check endpoint

## Security Best Practices

1. Always use HTTPS in production
2. Keep environment variables secure
3. Regularly rotate secrets and keys
4. Monitor audit logs
5. Keep dependencies updated
6. Use strong password policies
7. Implement rate limiting
8. Enable security headers

## Monitoring

The service includes comprehensive logging:

- Authentication attempts
- Token requests and refreshes
- Security events
- Error logging

Logs are stored in `auth_audit.log`

## Error Handling

The service includes robust error handling:

- Input validation
- Rate limiting
- Token validation
- Session management
- Security event logging

## Dependencies

See `requirements.txt` for a complete list of dependencies.
