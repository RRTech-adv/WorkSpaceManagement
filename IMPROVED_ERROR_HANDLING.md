# Improved Error Handling - Better Error Codes for Frontend

## 🎯 Problem

The global exception handler was returning generic "INTERNAL_SERVER_ERROR" for many cases, making it difficult for the frontend to distinguish between different types of errors.

## ✅ Solution

Enhanced the global exception handler to categorize exceptions and return specific error codes that the frontend can easily handle.

---

## 📋 Error Categories

The exception handler now categorizes errors into specific types:

### 1. **Request Validation Errors** (422)
- **Error Code:** `VALIDATION_ERROR`
- **When:** Pydantic validation fails
- **Response:** Detailed field-level errors

### 2. **Client Errors** (400-404)
- **Error Code:** `INVALID_REQUEST`, `MISSING_REQUIRED_FIELD`, `RESOURCE_NOT_FOUND`
- **When:** Invalid input, missing fields, resources not found
- **HTTP Status:** 400, 404

### 3. **Database Errors** (500, 503)
- **Error Code:** `DATABASE_ERROR`, `DATABASE_CONNECTION_ERROR`
- **When:** Database query failures, connection issues
- **HTTP Status:** 500 (query errors), 503 (connection errors)

### 4. **Network Errors** (503, 504)
- **Error Code:** `NETWORK_ERROR`, `REQUEST_TIMEOUT`
- **When:** Connection failures, timeouts
- **HTTP Status:** 503, 504

### 5. **External Service Errors** (502)
- **Error Code:** `EXTERNAL_SERVICE_ERROR`
- **When:** External API failures (Jira, ADO, etc.)
- **HTTP Status:** 502

### 6. **Storage Errors** (500)
- **Error Code:** `STORAGE_ERROR`
- **When:** Blob storage failures
- **HTTP Status:** 500

### 7. **Permission Errors** (403)
- **Error Code:** `PERMISSION_DENIED`
- **When:** User lacks required permissions
- **HTTP Status:** 403

---

## 🔍 Exception Categorization

The handler uses multiple strategies to categorize exceptions:

### 1. **Type-Based Detection**
```python
# Checks the exception type directly
isinstance(exc, ValueError)  # → INVALID_REQUEST
isinstance(exc, KeyError)    # → MISSING_REQUIRED_FIELD
isinstance(exc, FileNotFoundError)  # → RESOURCE_NOT_FOUND
```

### 2. **Message-Based Detection**
```python
# Analyzes exception message for keywords
"database" in exc_message and "connection" in exc_message
  → DATABASE_CONNECTION_ERROR
  
"not found" in exc_message
  → RESOURCE_NOT_FOUND
```

### 3. **Library-Specific Detection**
```python
# Checks for specific library exceptions
isinstance(exc, requests.exceptions.ConnectionError)
  → NETWORK_ERROR
```

---

## 📊 Error Response Format

All errors follow a consistent format:

```json
{
    "error_code": "ERROR_CODE_NAME",
    "message": "Human-readable error message"
}
```

### Example Responses

**Database Connection Error:**
```json
{
    "error_code": "DATABASE_CONNECTION_ERROR",
    "message": "Unable to connect to the database. Please try again later."
}
```

**Validation Error:**
```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "name: field required; email: invalid email format",
    "details": [...]
}
```

**Resource Not Found:**
```json
{
    "error_code": "RESOURCE_NOT_FOUND",
    "message": "Workspace not found"
}
```

---

## 🔧 How It Works

1. **HTTPException Handler** - Handles all `HTTPException` instances
   - If already formatted → Returns as-is
   - If dict format → Wraps in standard format
   - If string → Converts to standard format

2. **Validation Error Handler** - Handles Pydantic validation errors
   - Extracts field-level errors
   - Formats as `VALIDATION_ERROR` with details

3. **Global Exception Handler** - Catches all other exceptions
   - Categorizes exception type
   - Maps to appropriate error code
   - Returns user-friendly message
   - Logs full exception for debugging

---

## 📝 Logging

**Full exception details are always logged** for debugging:
```python
logger.error(f"Unhandled exception at {request.method} {request.url.path}: {exc_type}: {exc}", exc_info=True)
```

This includes:
- Request method and path
- Exception type and message
- Full stack trace (`exc_info=True`)

---

## 🎯 Frontend Benefits

### Before:
```json
{
    "error_code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred: ..."
}
```
❌ Frontend can't distinguish error types
❌ Hard to show appropriate user messages
❌ Can't retry appropriately

### After:
```json
{
    "error_code": "DATABASE_CONNECTION_ERROR",
    "message": "Unable to connect to the database. Please try again later."
}
```
✅ Frontend knows it's a connection error
✅ Can show "Retry" button
✅ Can differentiate from validation errors

---

## 📋 Error Code Reference

| Error Code | HTTP Status | When It Occurs |
|------------|-------------|----------------|
| `VALIDATION_ERROR` | 422 | Input validation fails |
| `INVALID_REQUEST` | 400 | Invalid request format |
| `MISSING_REQUIRED_FIELD` | 400 | Required field missing |
| `RESOURCE_NOT_FOUND` | 404 | Resource doesn't exist |
| `PERMISSION_DENIED` | 403 | User lacks permission |
| `DATABASE_ERROR` | 500 | Database query/operation error |
| `DATABASE_CONNECTION_ERROR` | 503 | Can't connect to database |
| `NETWORK_ERROR` | 503 | Network connection failed |
| `REQUEST_TIMEOUT` | 504 | Request timed out |
| `EXTERNAL_SERVICE_ERROR` | 502 | External API error |
| `STORAGE_ERROR` | 500 | Blob storage error |
| `INTERNAL_SERVER_ERROR` | 500 | Unknown/unhandled error |

---

## 💡 Best Practices for API Endpoints

When raising exceptions in your endpoints, use the standard format:

```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={
        "error_code": "WORKSPACE_NOT_FOUND",
        "message": "Workspace with the specified ID was not found."
    }
)
```

This ensures:
- ✅ Consistent error format
- ✅ Frontend can easily parse
- ✅ Appropriate HTTP status codes
- ✅ Clear error codes for handling

---

## 🔄 Error Handling Flow

```
Request → Endpoint
    ↓
Exception Raised
    ↓
┌─────────────────────────────┐
│ Exception Handler Chain     │
├─────────────────────────────┤
│ 1. HTTPException Handler    │ → Returns formatted error
│ 2. Validation Error Handler │ → Returns validation details
│ 3. Global Exception Handler │ → Categorizes & returns
└─────────────────────────────┘
    ↓
JSON Response to Frontend
    ↓
Frontend handles based on error_code
```

---

**The frontend can now easily distinguish between different error types and handle them appropriately!** 🚀

