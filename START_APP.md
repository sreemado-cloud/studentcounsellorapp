# How to Start the App (and Fix "localhost:3000/login doesn't work")

The login page only works when the **frontend** and **backend** are running. Use one of the options below.

---

## Option 1: Docker Compose (easiest if you use Docker)

1. **Start Docker Desktop** and wait until it’s fully running.

2. **Start the app:**
   ```powershell
   cd c:\Users\sreej\StudentCounsellorApp
   docker-compose up
   ```
   Wait until all three services (mongodb, backend, frontend) are up.

3. **Seed the database** (first time only):
   ```powershell
   docker-compose exec backend python -m app.seed_data
   ```
   Type `y` when asked to reseed if you’ve run it before.

4. **Open the login page:**  
   http://localhost:3000/login

5. **Login:** e.g. `admin@stateuniversity.edu` / `Admin123!`

---

## Option 2: Run backend + frontend manually (no Docker)

### Prerequisites
- **Node.js** (v18+)
- **Python** 3.11+
- **MongoDB** running locally on port 27017

### Step 1: Start MongoDB
- If installed locally: run `mongod`.
- Or use MongoDB Atlas and set `MONGODB_URL` in `backend\.env`.

### Step 2: Backend

```powershell
cd c:\Users\sreej\StudentCounsellorApp\backend

# Create venv if needed
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Optional: copy .env from example
# copy .env.example .env

uvicorn app.main:app --reload --port 8000
```
Leave this terminal open. You should see something like `Uvicorn running on http://0.0.0.0:8000`.

### Step 3: Frontend (new terminal)

```powershell
cd c:\Users\sreej\StudentCounsellorApp\frontend

npm install
npm run dev
```
When you see **`Local: http://localhost:3000`** (or `http://localhost:5173` if 3000 is busy), use that URL.

### Step 4: Seed the database (first time only)

```powershell
cd c:\Users\sreej\StudentCounsellorApp\backend
.\venv\Scripts\Activate.ps1
python -m app.seed_data
```

### Step 5: Open login

- **http://localhost:3000/login** (or **http://localhost:5173/login** if Vite used 5173)

Login e.g. with `admin@stateuniversity.edu` / `Admin123!`.

---

## Quick checks

| Check | URL | Expected |
|-------|-----|----------|
| Frontend | http://localhost:3000 | App home / redirect to dashboard or login |
| Login page | http://localhost:3000/login | Login form |
| Backend health | http://localhost:8000/health | `{"status":"healthy"}` |
| API docs | http://localhost:8000/docs | Swagger UI |

---

## Still not working?

1. **"Can’t reach localhost:3000"**  
   → Frontend not running. Start it with `npm run dev` in the `frontend` folder (Option 2) or `docker-compose up` (Option 1).

2. **"This site can’t be reached" / connection refused**  
   → Nothing is listening on that port. Confirm the frontend dev server is running and check the port in the terminal (3000 or 5173).

3. **Login page loads but "Login failed"**  
   → Backend or MongoDB issue. Check:
   - Backend: http://localhost:8000/health
   - You’ve run `python -m app.seed_data` and used the exact seeded credentials.

4. **Docker errors**  
   → Ensure Docker Desktop is running, then run `docker-compose up` again.

For more credentials and troubleshooting, see **LOGIN_CREDENTIALS.md**.
