# Debugging Forgot Password Feature

## Step-by-Step Instructions

### 1. Browser Developer Tools (Network Tab & Console)

#### How to Open:
1. **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
2. **Firefox**: Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)

#### Access Network Tab:
1. In the Developer Tools window, click the **"Network"** tab
2. Make sure the filter is set to **"All"** or **"XHR"** (for API calls)
3. **Clear the network log** (click the 🚫 icon) before testing
4. Submit the forgot password form
5. Look for a request named **`forgot-password`** or **`/api/auth/forgot-password`**

#### What to Check in Network Tab:
- **Status Code**: Should be `200` (success) or `429` (rate limited) or `500` (server error)
- **Response**: Click on the request → Click "Response" tab → See the JSON response
- **Headers**: Check if `Content-Type: application/json` is present
- **Timing**: See how long the request took

#### Access Console Tab:
1. In Developer Tools, click the **"Console"** tab
2. You should see:
   - `Sending forgot password request for: [email]`
   - `Forgot password response: {message: "..."}`
   - Or error messages if something fails

---

### 2. Backend Logs (Terminal/Command Prompt)

#### Where to Look:
The backend logs appear in the **terminal/command prompt** where you started the FastAPI server.

#### What You Should See:
When you submit the forgot password form, you should see logs like:
```
INFO:     Forgot password request received for: user@example.com
INFO:     User found, generating reset token for: user@example.com
INFO:     Reset token stored for user: user@example.com
INFO:     Attempting to send password reset email to: user@example.com
INFO:     Password reset email sent successfully to: user@example.com
INFO:     Returning success response for forgot password request: user@example.com
```

#### If Backend is Not Running:
1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```
2. Activate virtual environment (if using one):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Start the server:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

### 3. Test the Endpoint Directly (Using PowerShell)

You can test the API endpoint directly without the frontend:

```powershell
# Test forgot password endpoint
$body = @{
    email = "your-email@example.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/auth/forgot-password" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"
```

**Expected Response:**
```json
{
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

---

### 4. Common Issues & Solutions

#### Issue: Request shows "pending" or hangs
- **Check**: Backend server is running on port 8000
- **Check**: CORS is configured correctly
- **Solution**: Restart backend server

#### Issue: Status 429 (Too Many Requests)
- **Cause**: Rate limiter is blocking requests
- **Solution**: Wait a few minutes or check rate limit settings

#### Issue: Status 500 (Server Error)
- **Check**: Backend terminal for error messages
- **Check**: MongoDB is running and accessible
- **Check**: Email configuration (SMTP settings)

#### Issue: CORS Error
- **Check**: Frontend URL is in `ALLOWED_ORIGINS` or default localhost list
- **Check**: Backend CORS middleware is configured

---

### 5. Quick Test Checklist

- [ ] Backend server is running (check terminal)
- [ ] Frontend is running (check browser shows the page)
- [ ] Network tab shows the request
- [ ] Console shows log messages
- [ ] Backend terminal shows log messages
- [ ] Response status is 200
- [ ] Response body contains `{"message": "..."}`

---

### 6. Enable More Verbose Logging

If you need more detailed logs, the backend already has logging enabled. Check the terminal where you started `uvicorn`.

For even more verbose logging, you can modify the logging level in `backend/app/main.py` (though this is already configured).
