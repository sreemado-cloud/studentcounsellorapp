# How to Restart the Backend Server

## Quick Steps

### 1. Stop the Current Server

In the terminal where the backend is running, press:
```
Ctrl + C
```

This will stop the uvicorn server.

---

### 2. Start the Server Again

After stopping, run:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Complete Restart Process

### Option A: Using PowerShell

1. **Find the terminal** where the backend is running
2. **Press `Ctrl + C`** to stop the server
3. **Wait for it to stop** (you'll see "Shutting down" messages)
4. **Start it again:**
   ```powershell
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option B: If Server Won't Stop

If `Ctrl + C` doesn't work:

1. **Close the terminal window** (click the X button)
2. **Open a new PowerShell window**
3. **Navigate to backend:**
   ```powershell
   cd C:\Users\sreej\StudentCounsellorApp\backend
   ```
4. **Start the server:**
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option C: Kill the Process (If Port is Busy)

If you get an error like "port 8000 is already in use":

1. **Kill the Python process:**
   ```powershell
   taskkill /F /IM python.exe
   ```
2. **Wait a few seconds**
3. **Start the server again:**
   ```powershell
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## Verify Server is Running

After restarting, you should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Quick Test

Test that the server is working:

```powershell
# In a new terminal
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

You should get:
```json
{
  "status": "healthy",
  "service": "Student Counsellor API"
}
```

---

## Common Issues

### Issue: "Port 8000 is already in use"
**Solution:** Kill the Python process first:
```powershell
taskkill /F /IM python.exe
```

### Issue: "Module not found"
**Solution:** Make sure you're in the `backend` directory and have activated your virtual environment:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: "Command not found: uvicorn"
**Solution:** Install uvicorn or activate virtual environment:
```powershell
pip install uvicorn
# OR
.\venv\Scripts\Activate.ps1
```

---

## Summary

1. **Stop:** Press `Ctrl + C` in the terminal
2. **Start:** Run `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
3. **Verify:** Check for "Uvicorn running" message
4. **Test:** Visit `http://localhost:8000/health`

That's it! The server will restart and pick up any code changes automatically (thanks to `--reload` flag).
