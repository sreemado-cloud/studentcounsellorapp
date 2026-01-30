# Login URL and Credentials

## Get login working (backend already healthy)

1. **Start frontend** (so http://localhost:3000 works):
   ```powershell
   .\run-frontend.ps1
   ```
   Or: `docker compose up -d frontend`

2. **Seed the database** (if not done yet):
   ```powershell
   docker compose run --rm backend python -m app.seed_data
   ```

3. **Open** http://localhost:3000/login and log in with:
   - **Email:** `admin@stateuniversity.edu`
   - **Password:** `Admin123!`

4. **If login still fails:** Open DevTools (F12) → Network → try login → check the `POST .../api/auth/login` request (status and response). Check backend logs: `docker compose logs backend --tail 50`.

### Super admin login

- **Email:** `super@adminsca.com` · **Password:** `SuperAdmin123!` (seeded by `app.seed_data`)
- Set **`SUPER_ADMIN_EMAILS=super@adminsca.com`** in `backend/.env`, then restart backend: `docker compose restart backend`.
- After login you are sent to **Super Admin** (`/super-admin`). If you land on the normal dashboard, `is_super_admin` is false — fix `SUPER_ADMIN_EMAILS` and ensure you use the seeded super admin email.
- Reseed if needed: `docker compose run --rm backend python -m app.seed_data`.

---

## Login URL

### Local Development
- **Frontend (Login Page)**: http://localhost:3000/login
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Docker Compose
- **Frontend (Login Page)**: http://localhost:3000/login
- **Backend API**: http://localhost:8000

## Setting Up Test Credentials

Before logging in, you need to seed the database with sample users. Run the seed script:

```bash
cd backend
python -m app.seed_data
```

Or if using Docker Compose:
```bash
docker-compose exec backend python -m app.seed_data
```

## Test Credentials

After seeding, you can use these credentials to login:

### Super Admin (platform-wide; set `SUPER_ADMIN_EMAILS=super@adminsca.com` in backend/.env)
| Email | Password |
|-------|----------|
| super@adminsca.com | SuperAdmin123! |

### Admin Users (Full Access)
All admin accounts use password: **Admin123!**

| Institution | Email | Password |
|------------|-------|----------|
| State University | admin@stateuniversity.edu | Admin123! |
| City Community College | admin@citycollege.edu | Admin123! |
| Tech High School | admin@techhigh.edu | Admin123! |

### Counsellor Users
All counsellor accounts use password: **Counsellor123!**

| Institution | Email | Password |
|------------|-------|----------|
| State University | dr.sarah.johnson@stateuniversity.edu | Counsellor123! |
| State University | dr.michael.chen@stateuniversity.edu | Counsellor123! |
| City Community College | dr.emily.martinez@citycollege.edu | Counsellor123! |
| Tech High School | dr.james.wilson@techhigh.edu | Counsellor123! |

### Student Users
All student accounts use password: **Student123!**

| Institution | Email | Password |
|------------|-------|----------|
| State University | john.smith@stateuniversity.edu | Student123! |
| State University | jane.doe@stateuniversity.edu | Student123! |
| City Community College | alex.johnson@citycollege.edu | Student123! |
| Tech High School | emma.wilson@techhigh.edu | Student123! |

## Quick Start

1. **Start the application**:
   ```bash
   # Using Docker Compose (recommended)
   docker-compose up
   
   # OR manually:
   # Terminal 1: Start MongoDB
   mongod
   
   # Terminal 2: Start Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   
   # Terminal 3: Start Frontend
   cd frontend
   npm install
   npm run dev
   ```

2. **Seed the database** (if not already done):
   ```bash
   cd backend
   python -m app.seed_data
   ```

3. **Login**:
   - Go to http://localhost:3000/login
   - Use any of the credentials above
   - Example: `admin@stateuniversity.edu` / `Admin123!`

## Role Capabilities

### Admin
- Create and manage users (students, counsellors, admins)
- Assign students to counsellors (max 10 per counsellor)
- Reassign students to different counsellors
- View all data within their institution
- Approve/reject student registrations

### Counsellor
- View messages from assigned students only
- Send messages to assigned students
- View full conversation history (with masked previous counsellor names)
- Create appointments with assigned students

### Student
- View only their own data
- Send messages to assigned counsellor
- Create appointments with assigned counsellor
- Create and manage personal notes

## Troubleshooting

### "http://localhost:3000/login doesn't work"

**1. Start the application first**

The frontend must be running before you can open the login page.

**Option A – Docker Compose (recommended):**
```bash
# From project root
docker-compose up
```
Wait until you see the backend and frontend containers running. Then open http://localhost:3000/login.

**Option B – Manual (dev servers):**
```bash
# Terminal 1: MongoDB (if not already running)
mongod

# Terminal 2: Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```
When Vite shows "Local: http://localhost:3000", open http://localhost:3000/login.

**2. Try these URLs**
- http://localhost:3000/login  
- http://127.0.0.1:3000/login  
- http://localhost:3000 (then go to Login or navigate to /login)

**3. If using Vite dev and port 3000 is in use**  
Vite may use port 5173. Check the terminal for something like `Local: http://localhost:5173` and use http://localhost:5173/login.

**4. Check that services are running**
- Frontend: http://localhost:3000 (or 5173) should load the app.
- Backend: http://localhost:8000/health should return `{"status":"healthy"}`.
- API docs: http://localhost:8000/docs.

### Cannot Login (page loads but login fails)
- Ensure MongoDB is running.
- Ensure backend is running on port 8000.
- Ensure frontend is running on port 3000 (or 5173).
- Run the seed script so test users exist (see below).
- Use the exact seeded credentials (case-sensitive).

### Database Not Seeded
Run the seed script:
```bash
cd backend
python -m app.seed_data
```

Or with Docker:
```bash
docker-compose exec backend python -m app.seed_data
```

### Port Already in Use
- Change ports in `docker-compose.yml`, or
- Stop other apps using ports 3000 or 8000.

### Docker: "connection refused" or blank page
- Run `docker-compose up` and wait for all services to be healthy.
- Ensure nothing else is using ports 3000 or 8000.
- Try http://localhost:3000 and http://localhost:3000/login.
