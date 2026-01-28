# Troubleshooting Uvicorn Errors

## Common Errors and Solutions

### Error 1: "ModuleNotFoundError: No module named 'app'"

**Cause:** You're not in the `backend` directory, or Python can't find the `app` module.

**Solution:**
```powershell
# Make sure you're in the backend directory
cd C:\Users\sreej\StudentCounsellorApp\backend

# Then run uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Error 2: "ModuleNotFoundError: No module named 'fastapi'"

**Cause:** Dependencies are not installed.

**Solution:**
```powershell
# Make sure you're in the backend directory
cd C:\Users\sreej\StudentCounsellorApp\backend

# Install dependencies
pip install -r requirements.txt

# Then run uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Error 3: "Command 'uvicorn' not found"

**Cause:** Uvicorn is not installed or virtual environment is not activated.

**Solution A: Install uvicorn globally:**
```powershell
pip install uvicorn[standard]
```

**Solution B: Activate virtual environment first:**
```powershell
cd C:\Users\sreej\StudentCounsellorApp\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Then run uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Error 4: "Address already in use" or "Port 8000 is already in use"

**Cause:** Another process is using port 8000.

**Solution:**
```powershell
# Kill all Python processes
taskkill /F /IM python.exe

# Wait a few seconds, then try again
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Alternative:** Use a different port:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

### Error 5: "ImportError: cannot import name 'X' from 'app.core.Y'"

**Cause:** Missing import or circular import issue.

**Solution:**
1. Check if the file exists: `backend\app\core\Y.py`
2. Check if the import is correct in the file
3. Restart the server after fixing imports

---

### Error 6: "PermissionError" or "Access Denied"

**Cause:** Windows permissions issue.

**Solution:**
1. Run PowerShell as Administrator
2. Or use a different port (like 8001)

---

### Error 7: "SyntaxError" or "IndentationError"

**Cause:** Python syntax error in code.

**Solution:**
1. Check the error message - it will tell you which file and line
2. Fix the syntax error
3. The server will auto-reload after you save

---

## Step-by-Step Setup (If Nothing Works)

### 1. Navigate to Backend Directory
```powershell
cd C:\Users\sreej\StudentCounsellorApp\backend
```

### 2. Verify You're in the Right Place
```powershell
# Should show: C:\Users\sreej\StudentCounsellorApp\backend
pwd

# Should show app\main.py exists
dir app\main.py
```

### 3. Activate Virtual Environment (If You Have One)
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install/Update Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Verify Uvicorn is Installed
```powershell
uvicorn --version
```

### 6. Run the Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Quick Diagnostic Commands

Run these to check your setup:

```powershell
# Check current directory
pwd

# Check if app/main.py exists
Test-Path app\main.py

# Check Python version
python --version

# Check if uvicorn is installed
uvicorn --version

# Check if FastAPI is installed
python -c "import fastapi; print(fastapi.__version__)"
```

---

## Still Having Issues?

**Please share:**
1. The **exact error message** you're seeing
2. Your **current directory** (run `pwd`)
3. Whether you have a **virtual environment** activated
4. Your **Python version** (run `python --version`)

This will help me provide a more specific solution!
