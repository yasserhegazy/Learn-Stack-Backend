# LearnStack API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

Most endpoints also require the tenant context via header:
```
X-Tenant: <tenant_subdomain>
```

---

## Authentication Endpoints

### 1. Register New Tenant (Organization Signup)

Creates a new tenant organization with an admin user.

**Endpoint:** `POST /users/tenants/register/`

**Authentication:** None (Public endpoint)

**Request Headers:**
```json
Content-Type: application/json
```

**Request Body:**
```json
{
  "organization_name": "Acme University",
  "subdomain": "acmeuniv",
  "username": "admin",
  "email": "admin@acmeuniv.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "subscription_plan": "free"
}
```

**Response:** `201 Created`
```json
{
  "message": "Tenant created successfully",
  "tenant": {
    "id": 1,
    "name": "Acme University",
    "subdomain": "acmeuniv",
    "is_active": true,
    "subscription_plan": "free",
    "created_at": "2026-01-21T10:30:00Z",
    "updated_at": "2026-01-21T10:30:00Z"
  },
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@acmeuniv.com",
    "first_name": "John",
    "last_name": "Doe",
    "tenant_name": "Acme University",
    "is_active": true,
    "is_verified": false,
    "date_joined": "2026-01-21T10:30:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**Validation Rules:**
- `subdomain`: Lowercase alphanumeric with hyphens, 3-63 characters, unique
- `username`: Required, unique per tenant
- `email`: Required, valid email format, unique per tenant
- `password`: Minimum 8 characters
- `subscription_plan`: One of: `free`, `basic`, `professional`, `enterprise`

---

### 2. Login (Obtain JWT Token)

Authenticates a user and returns JWT tokens.

**Endpoint:** `POST /users/auth/login/`

**Authentication:** None (Public endpoint)

**Request Headers:**
```json
Content-Type: application/json
X-Tenant: acmeuniv
```

**Request Body:**
```json
{
  "username": "admin",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@acmeuniv.com",
    "tenant_id": 1,
    "tenant_name": "Acme University"
  }
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "No active account found with the given credentials"
}
```

---

### 3. Refresh Token

Obtains a new access token using a refresh token.

**Endpoint:** `POST /users/auth/refresh/`

**Authentication:** None

**Request Headers:**
```json
Content-Type: application/json
X-Tenant: acmeuniv
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 4. Logout (Blacklist Token)

Invalidates a refresh token.

**Endpoint:** `POST /users/auth/logout/`

**Authentication:** None

**Request Headers:**
```json
Content-Type: application/json
X-Tenant: acmeuniv
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "detail": "Token blacklisted successfully"
}
```

---

## User Management Endpoints

### 5. Get Current User Profile

Retrieves the authenticated user's profile.

**Endpoint:** `GET /users/me/`

**Authentication:** Required

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "first_name": "John",
  "last_name": "Doe",
  "avatar": null,
  "bio": "",
  "tenant": {
    "id": 1,
    "name": "Acme University",
    "subdomain": "acmeuniv",
    "is_active": true,
    "subscription_plan": "free",
    "created_at": "2026-01-21T10:30:00Z",
    "updated_at": "2026-01-21T10:30:00Z"
  },
  "user_roles": [
    {
      "id": 1,
      "user": 1,
      "role": 1,
      "role_name": "Admin",
      "assigned_by": null,
      "assigned_by_username": null,
      "created_at": "2026-01-21T10:30:00Z"
    }
  ],
  "date_joined": "2026-01-21T10:30:00Z"
}
```

---

### 6. List Users

Retrieves all users in the current tenant.

**Endpoint:** `GET /users/`

**Authentication:** Required (Tenant Member)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Query Parameters:**
- `role`: Filter by role name (e.g., `admin`, `instructor`, `student`)
- `is_active`: Filter by active status (`true` or `false`)
- `search`: Search in username, email, first_name, last_name
- `page`: Page number for pagination
- `page_size`: Number of results per page (default: 20)

**Example Request:**
```
GET /users/?role=instructor&is_active=true&page=1
```

**Response:** `200 OK`
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 2,
      "username": "johndoe",
      "email": "john@acmeuniv.com",
      "first_name": "John",
      "last_name": "Doe",
      "tenant_name": "Acme University",
      "roles": ["instructor"],
      "is_active": true,
      "is_verified": true,
      "date_joined": "2026-01-20T15:30:00Z"
    },
    {
      "id": 3,
      "username": "janedoe",
      "email": "jane@acmeuniv.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "tenant_name": "Acme University",
      "roles": ["instructor", "admin"],
      "is_active": true,
      "is_verified": true,
      "date_joined": "2026-01-19T09:15:00Z"
    }
  ]
}
```

---

### 7. Get User Details

Retrieves details of a specific user.

**Endpoint:** `GET /users/{user_id}/`

**Authentication:** Required (Tenant Member)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "avatar": "https://example.com/avatars/john.jpg",
  "bio": "Experienced instructor in mathematics",
  "tenant": {
    "id": 1,
    "name": "Acme University",
    "subdomain": "acmeuniv",
    "is_active": true,
    "subscription_plan": "free"
  },
  "user_roles": [
    {
      "id": 2,
      "role": 2,
      "role_name": "Instructor",
      "assigned_by_username": "admin",
      "created_at": "2026-01-20T15:30:00Z"
    }
  ],
  "date_joined": "2026-01-20T15:30:00Z"
}
```

---

### 8. Create User

Creates a new user in the current tenant.

**Endpoint:** `POST /users/`

**Authentication:** Required (Can Manage Users permission)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@acmeuniv.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "New",
  "last_name": "User"
}
```

**Response:** `201 Created`
```json
{
  "id": 4,
  "username": "newuser",
  "email": "newuser@acmeuniv.com",
  "first_name": "New",
  "last_name": "User",
  "tenant_name": "Acme University",
  "is_active": true,
  "is_verified": false,
  "date_joined": "2026-01-21T12:00:00Z"
}
```

**Validation Errors:** `400 Bad Request`
```json
{
  "username": ["A user with that username already exists in this tenant."],
  "password": ["Passwords do not match"]
}
```

---

### 9. Update User

Updates user information.

**Endpoint:** `PATCH /users/{user_id}/`

**Authentication:** Required (Owner or Admin)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
Content-Type: application/json
```

**Request Body:**
```json
{
  "first_name": "Updated",
  "last_name": "Name",
  "bio": "New bio text",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "johndoe",
  "email": "john@acmeuniv.com",
  "first_name": "Updated",
  "last_name": "Name",
  "bio": "New bio text",
  "avatar": "https://example.com/new-avatar.jpg",
  "tenant_name": "Acme University",
  "is_active": true,
  "date_joined": "2026-01-20T15:30:00Z"
}
```

---

### 10. Deactivate User

Deactivates a user account (soft delete).

**Endpoint:** `DELETE /users/{user_id}/`

**Authentication:** Required (Admin role)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Response:** `204 No Content`

---

### 11. Change Password

Changes the authenticated user's password.

**Endpoint:** `POST /users/change_password/`

**Authentication:** Required

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
Content-Type: application/json
```

**Request Body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!",
  "new_password_confirm": "NewPass456!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "old_password": ["Old password is incorrect"],
  "new_password_confirm": ["New passwords do not match"]
}
```

---

### 12. Assign Role to User

Assigns a role to a user.

**Endpoint:** `POST /users/{user_id}/assign_role/`

**Authentication:** Required (Can Manage Roles permission)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
Content-Type: application/json
```

**Request Body:**
```json
{
  "role_id": 2
}
```

**Response:** `201 Created`
```json
{
  "id": 5,
  "user": 4,
  "role": 2,
  "role_name": "Instructor",
  "assigned_by": 1,
  "assigned_by_username": "admin",
  "created_at": "2026-01-21T12:15:00Z"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "error": "Role not found"
}
```

---

### 13. Remove Role from User

Removes a role from a user.

**Endpoint:** `POST /users/{user_id}/remove_role/`

**Authentication:** Required (Can Manage Roles permission)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
Content-Type: application/json
```

**Request Body:**
```json
{
  "role_id": 2
}
```

**Response:** `204 No Content`

**Error Response:** `404 Not Found`
```json
{
  "error": "Role assignment not found"
}
```

---

## Role Management Endpoints

### 14. List Roles

Retrieves all roles in the current tenant.

**Endpoint:** `GET /users/roles/`

**Authentication:** Required (Tenant Member)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Response:** `200 OK`
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "admin",
      "description": "Full access to tenant resources",
      "permissions": [
        "manage_users",
        "manage_roles",
        "manage_courses",
        "manage_assessments",
        "view_analytics",
        "manage_settings"
      ],
      "is_system_role": true,
      "created_at": "2026-01-21T10:30:00Z"
    },
    {
      "id": 2,
      "name": "instructor",
      "description": "Create and manage courses",
      "permissions": [
        "create_courses",
        "manage_own_courses",
        "create_assessments",
        "grade_submissions",
        "view_student_progress",
        "issue_certificates"
      ],
      "is_system_role": true,
      "created_at": "2026-01-21T10:30:00Z"
    },
    {
      "id": 3,
      "name": "student",
      "description": "Enroll in courses",
      "permissions": [
        "enroll_courses",
        "view_courses",
        "submit_assessments",
        "view_own_progress",
        "view_certificates"
      ],
      "is_system_role": true,
      "created_at": "2026-01-21T10:30:00Z"
    }
  ]
}
```

---

### 15. Get Role Details

Retrieves details of a specific role.

**Endpoint:** `GET /users/roles/{role_id}/`

**Authentication:** Required (Tenant Member)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Response:** `200 OK`
```json
{
  "id": 2,
  "name": "instructor",
  "description": "Create and manage courses",
  "permissions": [
    "create_courses",
    "manage_own_courses",
    "create_assessments",
    "grade_submissions",
    "view_student_progress",
    "issue_certificates"
  ],
  "is_system_role": true,
  "created_at": "2026-01-21T10:30:00Z"
}
```

---

## Tenant Management Endpoints

### 16. Get Current Tenant

Retrieves the authenticated user's tenant information.

**Endpoint:** `GET /users/tenants/`

**Authentication:** Required

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
```

**Response:** `200 OK`
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Acme University",
      "subdomain": "acmeuniv",
      "is_active": true,
      "subscription_plan": "free",
      "created_at": "2026-01-21T10:30:00Z",
      "updated_at": "2026-01-21T10:30:00Z"
    }
  ]
}
```

---

### 17. Update Tenant

Updates tenant information.

**Endpoint:** `PATCH /users/tenants/{tenant_id}/`

**Authentication:** Required (Admin role)

**Request Headers:**
```json
Authorization: Bearer <access_token>
X-Tenant: acmeuniv
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Acme University - Updated",
  "subscription_plan": "professional"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Acme University - Updated",
  "subdomain": "acmeuniv",
  "is_active": true,
  "subscription_plan": "professional",
  "created_at": "2026-01-21T10:30:00Z",
  "updated_at": "2026-01-21T14:30:00Z"
}
```

**Note:** The `subdomain` field cannot be changed after creation.

---

## Common Response Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 OK | Request successful |
| 201 Created | Resource created successfully |
| 204 No Content | Request successful, no content to return |
| 400 Bad Request | Invalid request data or validation error |
| 401 Unauthorized | Authentication required or invalid credentials |
| 403 Forbidden | Insufficient permissions |
| 404 Not Found | Resource not found |
| 500 Internal Server Error | Server error |

---

## Error Response Format

All error responses follow this format:

```json
{
  "field_name": ["Error message"],
  "another_field": ["Another error message"]
}
```

Or for general errors:

```json
{
  "detail": "Error message",
  "error": "Error description"
}
```

---

## Permissions System

### Role Types

1. **Admin** - Full access to all tenant resources
2. **Instructor** - Can create and manage courses, assessments
3. **Student** - Can enroll in courses and submit assessments

### Permission Checks

Endpoints enforce the following permission levels:

- **Public**: No authentication required
- **Authenticated**: Any logged-in user
- **Tenant Member**: User must belong to the tenant
- **Owner or Admin**: User owns the resource OR has admin role
- **Can Manage Users**: User has `manage_users` permission
- **Can Manage Roles**: User has `manage_roles` permission
- **Admin Role**: User has admin role in the tenant

---

## JWT Token Structure

The access token includes the following claims:

```json
{
  "token_type": "access",
  "exp": 1737467400,
  "iat": 1737463800,
  "jti": "abc123...",
  "user_id": 1,
  "username": "admin",
  "email": "admin@acmeuniv.com",
  "tenant_id": 1,
  "tenant_subdomain": "acmeuniv"
}
```

**Token Expiry:**
- Access Token: 60 minutes
- Refresh Token: 7 days

---

## Best Practices for Frontend Integration

### 1. Store Tokens Securely
- Store tokens in httpOnly cookies or secure storage
- Never store tokens in localStorage if possible
- Clear tokens on logout

### 2. Handle Token Refresh
```javascript
// Example: Axios interceptor for token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = getRefreshToken();
      const response = await axios.post('/users/auth/refresh/', {
        refresh: refreshToken
      });
      
      // Update access token
      setAccessToken(response.data.access);
      
      // Retry original request
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);
```

### 3. Include Required Headers
Always include both headers for authenticated requests:
```javascript
{
  'Authorization': `Bearer ${accessToken}`,
  'X-Tenant': tenantSubdomain
}
```

### 4. Handle Validation Errors
```javascript
try {
  await createUser(userData);
} catch (error) {
  if (error.response?.status === 400) {
    // Display field-specific errors
    const errors = error.response.data;
    Object.keys(errors).forEach(field => {
      showError(field, errors[field][0]);
    });
  }
}
```

### 5. Implement Pagination
```javascript
const loadUsers = async (page = 1) => {
  const response = await axios.get(`/users/?page=${page}`);
  return {
    users: response.data.results,
    totalCount: response.data.count,
    hasNext: !!response.data.next,
    hasPrevious: !!response.data.previous
  };
};
```

---

## Testing Endpoints

### Using cURL

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant: acmeuniv" \
  -d '{
    "username": "admin",
    "password": "SecurePass123!"
  }'
```

**Get Current User:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Tenant: acmeuniv"
```

### Using Postman

1. Create a collection for LearnStack API
2. Set base URL as environment variable: `{{base_url}}`
3. Add authentication header at collection level
4. Use pre-request scripts for token management

---

## Rate Limiting

Currently no rate limiting is implemented. This will be added in future versions.

---

## API Versioning

The API uses URL versioning:
- Current version: `/api/v1/`
- Future versions will be: `/api/v2/`, `/api/v3/`, etc.

---

## Support

For API issues or questions, contact: support@learnstack.com
