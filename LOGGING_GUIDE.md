# Logging Guide - How to View Logged Information

## 📋 Current Logging Setup

Your application uses Python's built-in `logging` module configured in `app/main.py`:

```python
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**Log Format:**
```
YYYY-MM-DD HH:MM:SS,mmm - logger_name - LEVEL - message
```

**Example Output:**
```
2024-01-15 10:30:45,123 - app.main - INFO - Starting up...
2024-01-15 10:30:45,456 - app.db.connection - INFO - Database pool initialized
```

---

## 🔍 How to View Logs

### 1. **Console Output (Default - Current Setup)**

When you run your FastAPI application, logs are printed to the **console/terminal** where you started the server.

**View logs:**
- Just look at your terminal/command prompt where the server is running
- Logs appear in real-time as events happen

**To run and see logs:**
```bash
# Option 1: Using Python module
python -m app.main

# Option 2: Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Using uvicorn with log level override
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
```

---

## ⚙️ Log Level Configuration

The log level is controlled by the `LOG_LEVEL` environment variable in your `.env` file.

**Available Levels (from least to most verbose):**
1. `CRITICAL` - Only critical errors
2. `ERROR` - Errors only
3. `WARNING` - Warnings and errors
4. `INFO` - Informational messages (default)
5. `DEBUG` - Very detailed debugging information

**To change log level:**
Add to your `.env` file:
```env
LOG_LEVEL=DEBUG  # For detailed debugging
# or
LOG_LEVEL=WARNING  # Only warnings and errors
# or
LOG_LEVEL=INFO  # Default - informational messages
```

---

## 📊 What Gets Logged

### Application Lifecycle
- ✅ Server startup/shutdown
- ✅ Database connection pool initialization

### Authentication & Authorization
- ✅ Token validation (success/failure)
- ✅ PMA token generation/refresh
- ✅ Role lookups from database
- ✅ Token user mismatches

### Workspace Operations
- ✅ Workspace creation
- ✅ Schema creation for workspaces
- ✅ Integration creation during workspace setup

### Database Operations
- ✅ Database pool initialization
- ✅ Connection errors
- ✅ Query execution errors

### Integration Operations
- ✅ External API calls (Jira, ADO, ServiceNow, SharePoint)
- ✅ Integration fetch errors

### Errors & Exceptions
- ✅ All unhandled exceptions (with stack traces)
- ✅ Database query failures
- ✅ Validation errors
- ✅ Integration failures

---

## 🔧 Enhancing Logging (Optional Improvements)

If you want to save logs to a file instead of (or in addition to) console, you can update the logging configuration:

### Option 1: Save to File

Update `app/main.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

# Create file handler
file_handler = RotatingFileHandler(
    'app.log',  # Log file name
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5  # Keep 5 backup files
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, settings.log_level.upper()))
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)
```

### Option 2: Structured JSON Logging (Production)

For production environments, you might want structured JSON logs:

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Use JSON formatter
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(handlers=[handler], level=logging.INFO)
```

---

## 📝 Log Levels in Your Code

You can see different log levels used throughout your codebase:

- **`logger.info()`** - Normal operation messages
  - "Starting up..."
  - "Database pool initialized"
  - "Workspace created..."

- **`logger.warning()`** - Warning messages
  - "Database not configured"
  - "Token refresh failed"
  - "Blob storage not configured"

- **`logger.error()`** - Error messages
  - "Failed to initialize database pool"
  - "Error fetching Jira projects"
  - "Unhandled exception: ..."

- **`logger.debug()`** - Detailed debugging (not currently used, but available)

---

## 🎯 Quick Reference

### View Logs Now
```bash
# 1. Start your server
python -m app.main

# 2. Watch the terminal output - logs appear in real-time
```

### Change Log Level
```bash
# In .env file
LOG_LEVEL=DEBUG  # See everything
```

### Filter Logs (if saved to file)
```bash
# Linux/Mac
grep ERROR app.log

# Windows PowerShell
Select-String -Path app.log -Pattern "ERROR"
```

---

## 💡 Tips

1. **Development**: Use `LOG_LEVEL=DEBUG` for maximum visibility
2. **Production**: Use `LOG_LEVEL=INFO` or `WARNING` to reduce noise
3. **Troubleshooting**: Check logs when something goes wrong - they show what happened
4. **Real-time Monitoring**: Keep terminal open while developing to see logs as they happen

---

**Your logs are currently displayed in the console/terminal where you run the application!** 🚀

