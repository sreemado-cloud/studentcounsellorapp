# How to Start Docker Desktop

## Quick Steps

1. **Open Docker Desktop:**
   - Press `Windows Key` and type "Docker Desktop"
   - Click on "Docker Desktop" app
   - OR look for the Docker whale icon in your system tray (bottom right) and click it

2. **Wait for Docker to Start:**
   - You'll see "Docker Desktop is starting..." 
   - Wait until the tray icon stops animating (usually 30-60 seconds)
   - The icon should be steady (not animated) when ready

3. **Verify Docker is Running:**
   ```powershell
   docker ps
   ```
   If you see a table (even if empty), Docker is running ✅

4. **Start the App:**
   ```powershell
   cd c:\Users\sreej\StudentCounsellorApp
   docker-compose up
   ```
   
   OR use the provided script:
   ```powershell
   .\start-docker.ps1
   ```

## Troubleshooting

### "Docker Desktop failed to start"
- Make sure virtualization is enabled in BIOS
- Check Windows WSL 2 is installed and updated
- Restart your computer and try again

### "Docker Desktop is starting..." (takes too long)
- Check system resources (CPU, RAM)
- Close other heavy applications
- Restart Docker Desktop

### "Cannot connect to Docker daemon"
- Make sure Docker Desktop is fully started (not just launching)
- Try restarting Docker Desktop
- Check if Docker service is running in Services (services.msc)

## After Docker Starts

Once Docker Desktop is running, you can:

1. **Start all services:**
   ```powershell
   docker-compose up
   ```

2. **Seed the database (first time only):**
   ```powershell
   docker-compose exec backend python -m app.seed_data
   ```

3. **Open the app:**
   - Frontend: http://localhost:3000/login
   - Backend API: http://localhost:8000/docs

## Alternative: Use the PowerShell Script

I've created `start-docker.ps1` that will:
- Check if Docker is running
- Give you clear instructions if it's not
- Start the app automatically if Docker is ready

Just run:
```powershell
.\start-docker.ps1
```
