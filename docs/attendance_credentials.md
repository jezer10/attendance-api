## Attendance Credentials API

This endpoint lets the frontend store per-user login credentials used by the
attendance marking workflow. The password is stored in Supabase Vault; the API
returns only metadata, never the password.

### Endpoint
`POST /api/v1/attendance/credentials`

### Auth
Send a valid JWT in:
`Authorization: Bearer <token>`

### Request body
```json
{
  "companyId": 7040,
  "userId": 77668171,
  "password": "Milagros1234"
}
```

### Field reference
| Field       | Type   | Required | Notes |
|-------------|--------|----------|-------|
| `companyId` | number | yes      | Maps to `txt_id_empresa` in the marking flow. |
| `userId`    | number | yes      | Maps to `txt_id_usuario` in the marking flow. |
| `password`  | string | yes      | Maps to `txt_pass`; trimmed, cannot be empty. |

### Success response
```json
{
  "success": true,
  "message": "Attendance credentials saved",
  "companyId": 7040,
  "userId": 77668171
}
```

### Error responses
- `400 Bad Request`: validation error (missing fields, invalid values, empty password)
- `401 Unauthorized`: missing/invalid token
- `503 Service Unavailable`: Supabase persistence or Vault error

### Notes
- One credential set per user; repeated calls overwrite the stored password.
- Passwords are stored in Supabase Vault and decrypted only server-side using the
  service role key.

## Fetch stored credentials
Fetch saved credentials metadata without exposing the password.

### Endpoint
`GET /api/v1/attendance/credentials`

### Success response
```json
{
  "companyId": 7040,
  "userId": 77668171,
  "hasPassword": true
}
```

### Error responses
- `401 Unauthorized`: missing/invalid token
- `404 Not Found`: no credentials stored
- `503 Service Unavailable`: Supabase persistence or Vault error

### Example (curl)
```bash
curl -X GET http://localhost:8000/api/v1/attendance/credentials \
  -H "Authorization: Bearer <token>"
```

### Example (curl)
```bash
curl -X POST http://localhost:8000/api/v1/attendance/credentials \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "companyId": 7040,
        "userId": 77668171,
        "password": "Milagros1234"
      }'
```

### Example (fetch)
```js
async function saveAttendanceCredentials({ token, companyId, userId, password }) {
  const response = await fetch(
    "http://localhost:8000/api/v1/attendance/credentials",
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ companyId, userId, password }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to save credentials");
  }

  return response.json();
}
```
