# "localhost refused to connect" / Backend /health not up

## Backend /health not responding ("site can't be reached")

**1. Start backend and verify /health (recommended):**
```powershell
.\run-backend.ps1
```
This brings up MongoDB + backend, waits, then checks http://localhost:8000/health. If it fails, it prints backend and MongoDB logs.

**2. Or run diagnostic only (containers already up):**
```powershell
.\troubleshoot-backend.ps1
```

**3. Manual restart and rebuild:**
```powershell
docker compose down
docker compose up -d --build mongodb backend
```
Wait ~30s, then try http://localhost:8000/health again.

**3. MongoDB password mismatch (backend logs show auth errors):**  
Ensure root `.env` has `MONGO_INITDB_ROOT_PASSWORD` matching your MongoDB.  
To reset DB and use current `.env`:
```powershell
docker compose down -v
docker compose up -d --build
# then seed: docker compose run --rm backend python -m app.seed_data
```

---

## 1. Try DEV mode (often fixes it)

Runs **MongoDB + Backend in Docker** and **Frontend locally** (Vite):

```powershell
cd C:\Users\sreej\StudentCounsellorApp
.\start-dev.ps1
```

Then open **http://localhost:3000**. Stop the dev server with `Ctrl+C` when done.

---

## 2. Full Docker (all in containers)

1. **Start Docker Desktop** and wait until it’s fully up.
2. Run:
   ```powershell
   cd C:\Users\sreej\StudentCounsellorApp
   .\start-docker.ps1
   ```
3. Open **http://localhost:3000** (use `http`, not `https`, port **3000**).

---

## 3. If it still fails

- **Check containers:** `docker compose ps -a`  
  MongoDB, backend, and frontend should be **Up**.

- **View logs:**
  ```powershell
  docker compose logs backend
  docker compose logs frontend
  docker compose logs mongodb
  ```

- **Root `.env`** (same folder as `docker-compose.yml`) must have:
  ```env
  MONGO_INITDB_ROOT_USERNAME=admin
  MONGO_INITDB_ROOT_PASSWORD=Admin1234567890
  ```
  (Use the password that matches your MongoDB.)

- **Clean restart** (deletes DB data):
  ```powershell
  docker compose down -v
  .\start-docker.ps1
  ```
  Then seed: `docker compose run --rm backend python -m app.seed_data`
