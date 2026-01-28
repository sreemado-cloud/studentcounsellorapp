# How to View Backend Logs

## Quick Answer

**Backend logs appear in the terminal/command prompt where you started the FastAPI server.**

---

## Step-by-Step Instructions

### 1. Find the Terminal Running the Backend

Look for a **PowerShell**, **Command Prompt**, or **Terminal** window that shows output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**This is where your backend logs appear!**

---

### 2. If Backend is Not Running

If you don't see a terminal with the backend running, start it:

#### Option A: Using PowerShell (Recommended)

1. Open a **new PowerShell** window
2. Navigate to the backend directory:
   ```powershell
   cd C:\Users\sreej\StudentCounsellorApp\backend
   ```
3. Activate virtual environment (if you have one):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
4. Start the server:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Option B: Using Command Prompt

1. Open **Command Prompt** (cmd)
2. Navigate to the backend directory:
   ```cmd
   cd C:\Users\sreej\StudentCounsellorApp\backend
   ```
3. Activate virtual environment (if you have one):
   ```cmd
   venv\Scripts\activate
   ```
4. Start the server:
   ```cmd
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

### 3. What You'll See in the Logs

When you submit the forgot password form, you should see logs like:

```
2025-01-25 10:30:45 - app.api.auth - INFO - Forgot password request received for: user@example.com
2025-01-25 10:30:45 - app.api.auth - INFO - User found, generating reset token for: user@example.com
2025-01-25 10:30:45 - app.api.auth - INFO - Reset token stored for user: user@example.com
2025-01-25 10:30:45 - app.api.auth - INFO - Scheduling password reset email to be sent to: user@example.com
2025-01-25 10:30:45 - app.api.auth - INFO - Returning success response for forgot password request: user@example.com
```

**Or if there's an error:**
```
2025-01-25 10:30:45 - app.api.auth - ERROR - Error processing forgot password request for user@example.com: [error message]
```

---

### 4. Log Format

The logs are formatted as:
```
YYYY-MM-DD HH:MM:SS - module.name - LEVEL - message
```

**Log Levels:**
- `INFO` - Normal operations
- `WARNING` - Something unexpected but not critical
- `ERROR` - An error occurred
- `DEBUG` - Detailed debugging information (if enabled)

---

### 5. Enable More Verbose Logging

If you need more detailed logs, you can change the log level in `backend/app/main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

Then restart the backend server.

---

### 6. Common Issues

#### Issue: "No logs appearing"
- **Check**: Is the backend server actually running?
- **Check**: Are you looking at the correct terminal window?
- **Solution**: Start the backend server (see Step 2)

#### Issue: "Logs are too verbose"
- **Solution**: Change log level from `DEBUG` to `INFO` in `backend/app/main.py`

#### Issue: "Can't find the terminal"
- **Solution**: Look for a window titled "PowerShell", "Command Prompt", or "Terminal"
- **Tip**: Check your taskbar for minimized terminal windows

---

### 7. Quick Test

To verify logging is working, you can test the health endpoint:

```powershell
# In a new terminal
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

You should see a log entry in the backend terminal like:
```
INFO:     127.0.0.1:xxxxx - "GET /health HTTP/1.1" 200 OK
```

---

## Summary

1. **Backend logs = Terminal where uvicorn is running**
2. **Look for the terminal showing "Uvicorn running on http://0.0.0.0:8000"**
3. **All API requests will log there automatically**
4. **Logs include timestamps, module names, and log levels**

If you still can't find the logs, share what you see when you try to start the backend server!
