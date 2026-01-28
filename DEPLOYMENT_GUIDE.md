# Deployment Guide for Student Counsellor App

This guide provides multiple deployment strategies, from quick testing to production-ready deployments.

## Table of Contents

1. [Quick Testing Options](#quick-testing-options) - Share locally or deploy in minutes
2. [Simple Cloud Deployment](#simple-cloud-deployment) - Easy cloud platforms
3. [Production Deployment](#production-deployment) - AWS EKS, VPS, etc.
4. [Environment Configuration](#environment-configuration)
5. [Security Checklist](#security-checklist)
6. [Cost Estimates](#cost-estimates)

---

## Quick Testing Options

### Option 1: ngrok (Share Local Instance) ⚡ **FASTEST**

**Best for:** Quick testing, demos, friend review  
**Cost:** Free (with limitations)  
**Time:** 2 minutes

#### Steps:

1. **Start your app locally:**
   ```powershell
   # In your project directory
   docker compose up -d
   ```

2. **Install ngrok:**
   - Download from https://ngrok.com/download
   - Or use: `winget install ngrok` (Windows)

3. **Create ngrok tunnel:**
   ```powershell
   ngrok http 3000
   ```

4. **Share the URL:**
   - ngrok will give you a URL like: `https://abc123.ngrok.io`
   - Share this URL with your friend
   - **Note:** Free tier URLs change on restart. Paid plans get fixed domains.

5. **Update frontend API URL (if needed):**
   - If your frontend calls `/api`, it should work automatically
   - If it uses `http://localhost:8000`, create `.env` in `frontend/`:
     ```env
     VITE_API_URL=https://your-ngrok-url.ngrok.io/api
     ```
   - Rebuild frontend: `docker compose build frontend && docker compose up -d frontend`

**Pros:**
- ✅ Instant deployment
- ✅ Free
- ✅ No cloud account needed

**Cons:**
- ❌ URL changes on restart (free tier)
- ❌ Requires your computer to be running
- ❌ Limited bandwidth on free tier

---

### Option 2: Railway.app 🚂 **RECOMMENDED FOR TESTING**

**Best for:** Easy cloud deployment, friend testing  
**Cost:** Free tier (500 hours/month), then ~$5-10/month  
**Time:** 15-20 minutes

#### Steps:

1. **Sign up:** https://railway.app (GitHub login)

2. **Create new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or upload code)

3. **Add services:**
   
   **a) MongoDB:**
   - Click "+ New" → "Database" → "MongoDB"
   - Railway provides connection string automatically

   **b) Backend:**
   - Click "+ New" → "GitHub Repo" → Select your repo
   - Set root directory: `backend`
   - Add environment variables:
     ```
     MONGODB_URL=<from MongoDB service>
     DATABASE_NAME=student_counsellor
     SECRET_KEY=<generate with: openssl rand -hex 32>
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     SUPER_ADMIN_EMAILS=admin@stateuniversity.edu
     ```
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Railway auto-detects port from `$PORT`

   **c) Frontend:**
   - Click "+ New" → "GitHub Repo" → Select your repo
   - Set root directory: `frontend`
   - Add environment variable:
     ```
     VITE_API_URL=<Backend public URL>/api
     ```
   - Railway auto-builds and deploys

4. **Get public URLs:**
   - Each service gets a public URL (e.g., `https://backend-production-xxxx.up.railway.app`)
   - Share the frontend URL with your friend

5. **Seed database:**
   - SSH into backend service or use Railway CLI:
     ```bash
     railway run python -m app.seed_data
     ```

**Pros:**
- ✅ Very easy setup
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ GitHub integration
- ✅ Persistent URLs

**Cons:**
- ❌ Free tier has limits
- ❌ Requires GitHub repo (or manual upload)

---

### Option 3: Render.com 🎨

**Best for:** Free tier with persistent URLs  
**Cost:** Free tier available, then ~$7-15/month  
**Time:** 20-30 minutes

#### Steps:

1. **Sign up:** https://render.com (GitHub login)

2. **Create MongoDB:**
   - New → "MongoDB"
   - Free tier: 512MB storage

3. **Deploy Backend:**
   - New → "Web Service"
   - Connect GitHub repo
   - Settings:
     - **Root Directory:** `backend`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Environment Variables:**
       ```
       MONGODB_URL=<from MongoDB>
       DATABASE_NAME=student_counsellor
       SECRET_KEY=<generate>
       ACCESS_TOKEN_EXPIRE_MINUTES=30
       SUPER_ADMIN_EMAILS=admin@stateuniversity.edu
       ```

4. **Deploy Frontend:**
   - New → "Static Site"
   - Connect GitHub repo
   - Settings:
     - **Root Directory:** `frontend`
     - **Build Command:** `npm install && npm run build`
     - **Publish Directory:** `dist`
     - **Environment Variable:**
       ```
       VITE_API_URL=<Backend URL>/api
       ```

5. **Get URLs:**
   - Backend: `https://your-backend.onrender.com`
   - Frontend: `https://your-frontend.onrender.com`

**Pros:**
- ✅ Free tier
- ✅ Persistent URLs
- ✅ Auto-deploy from GitHub

**Cons:**
- ❌ Free tier services "spin down" after inactivity (slow first request)
- ❌ Limited resources on free tier

---

### Option 4: Fly.io 🪰

**Best for:** Global edge deployment, fast  
**Cost:** Free tier (3 VMs), then pay-as-you-go  
**Time:** 25-30 minutes

#### Steps:

1. **Install Fly CLI:**
   ```powershell
   winget install flyctl
   ```

2. **Sign up:** https://fly.io (or `flyctl auth signup`)

3. **Create apps:**
   ```bash
   # Backend
   cd backend
   flyctl launch
   # Follow prompts, select region
   
   # Frontend
   cd ../frontend
   flyctl launch
   ```

4. **Configure:**
   - Set environment variables in Fly dashboard
   - Update `fly.toml` if needed

5. **Deploy:**
   ```bash
   flyctl deploy
   ```

**Pros:**
- ✅ Global edge network
- ✅ Free tier
- ✅ Fast deployment

**Cons:**
- ❌ Requires CLI setup
- ❌ More complex than Railway/Render

---

## Simple Cloud Deployment

### Option 5: DigitalOcean App Platform 💧

**Best for:** Simple, reliable deployment  
**Cost:** ~$12-25/month  
**Time:** 30 minutes

#### Steps:

1. **Sign up:** https://digitalocean.com

2. **Create App:**
   - Apps → Create App
   - Connect GitHub repo

3. **Add Components:**
   - **Database:** Managed MongoDB ($15/month)
   - **Backend:** Web Service (Python)
   - **Frontend:** Static Site

4. **Configure:**
   - Set environment variables
   - Set build/start commands
   - Deploy

**Pros:**
- ✅ Simple interface
- ✅ Reliable
- ✅ Good documentation

**Cons:**
- ❌ No free tier
- ❌ More expensive than free options

---

### Option 6: AWS Lightsail 💡

**Best for:** Simple AWS deployment  
**Cost:** ~$10-20/month  
**Time:** 45 minutes

#### Steps:

1. **Create Lightsail instance:**
   - Choose "Container" or "Ubuntu" + Docker

2. **Deploy with Docker Compose:**
   ```bash
   # SSH into instance
   git clone <your-repo>
   cd StudentCounsellorApp
   docker compose up -d
   ```

3. **Configure:**
   - Set up static IP
   - Open ports (80, 443, 8000)
   - Set up domain (optional)

**Pros:**
- ✅ Simple AWS option
- ✅ Predictable pricing
- ✅ Full control

**Cons:**
- ❌ Requires server management
- ❌ No free tier

---

## Production Deployment

### Option 7: AWS EKS (Already Documented) ☁️

See `README.md` section "EKS Deployment" for full instructions.

**Best for:** Production, scalability, enterprise  
**Cost:** ~$70-200/month (cluster + nodes)  
**Time:** 2-3 hours

---

### Option 8: VPS (DigitalOcean, Linode, Hetzner) 🖥️

**Best for:** Full control, cost-effective  
**Cost:** ~$6-20/month  
**Time:** 1-2 hours

#### Steps:

1. **Create VPS:**
   - Ubuntu 22.04 LTS
   - 2GB RAM minimum (4GB recommended)
   - Install Docker: `curl -fsSL https://get.docker.com | sh`

2. **Deploy:**
   ```bash
   # Clone repo
   git clone <your-repo>
   cd StudentCounsellorApp
   
   # Copy and configure .env
   cp backend/.env.example backend/.env
   # Edit backend/.env with production values
   
   # Deploy
   docker compose up -d
   ```

3. **Set up reverse proxy (Nginx):**
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   
   # Configure nginx (see nginx.conf.example below)
   sudo certbot --nginx -d yourdomain.com
   ```

4. **Configure firewall:**
   ```bash
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

**Pros:**
- ✅ Full control
- ✅ Cost-effective
- ✅ Can use your domain

**Cons:**
- ❌ Requires server management
- ❌ You handle security updates

---

## Environment Configuration

### Backend Environment Variables

Create `backend/.env` with:

```env
# MongoDB
MONGODB_URL=mongodb://user:password@host:27017
DATABASE_NAME=student_counsellor

# Security
SECRET_KEY=<generate with: openssl rand -hex 32>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Super Admin
SUPER_ADMIN_EMAILS=admin@stateuniversity.edu,your-email@example.com

# Deployment Mode (optional)
DEPLOYMENT_MODE=saas  # or "on_premise"
SAAS_ISOLATION_LEVEL=low  # or "high"

# Email (optional, for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=https://your-frontend-url.com

# CORS (for production)
ALLOWED_ORIGINS=https://your-frontend-url.com,https://www.your-frontend-url.com
```

### Frontend Environment Variables

Create `frontend/.env` or set in deployment platform:

```env
VITE_API_URL=https://your-backend-url.com/api
```

Or if backend is at `/api` (same domain):
```env
VITE_API_URL=/api
```

---

## Security Checklist

Before deploying for review/testing:

- [ ] **Change default passwords:**
  - MongoDB: Use strong password
  - SECRET_KEY: Generate new (not default)

- [ ] **Set SUPER_ADMIN_EMAILS:**
  - Add your email and friend's email for testing

- [ ] **CORS Configuration:**
  - Set `ALLOWED_ORIGINS` to your frontend URL(s)

- [ ] **HTTPS:**
  - Use HTTPS in production (Railway, Render, Fly.io provide automatically)
  - For VPS: Use Let's Encrypt (certbot)

- [ ] **Database Security:**
  - Use MongoDB authentication
  - Don't expose MongoDB port publicly
  - Use connection string with credentials

- [ ] **Environment Variables:**
  - Never commit `.env` files
  - Use platform secrets/environment variables

- [ ] **Rate Limiting:**
  - Already implemented in backend
  - Consider adjusting limits for testing

---

## Cost Estimates

| Option | Monthly Cost | Best For |
|--------|-------------|----------|
| ngrok (free) | $0 | Quick testing |
| Railway (free tier) | $0-10 | Easy testing |
| Render (free tier) | $0-15 | Persistent testing |
| Fly.io (free tier) | $0-20 | Global testing |
| DigitalOcean App | $12-25 | Simple production |
| AWS Lightsail | $10-20 | Simple AWS |
| VPS (DigitalOcean) | $6-20 | Full control |
| AWS EKS | $70-200 | Production scale |

---

## Recommended: Railway.app for Friend Review

**Why Railway:**
1. ✅ Easiest setup (15 minutes)
2. ✅ Free tier sufficient for testing
3. ✅ Automatic HTTPS
4. ✅ Persistent URLs
5. ✅ GitHub integration
6. ✅ Good for demos

**Quick Start:**

1. Push code to GitHub (if not already)
2. Sign up at https://railway.app
3. New Project → Deploy from GitHub
4. Add MongoDB service
5. Add Backend service (configure env vars)
6. Add Frontend service (set `VITE_API_URL`)
7. Share frontend URL with friend
8. Seed database via Railway CLI or SSH

**Time to deploy:** ~15-20 minutes  
**Cost:** Free (or ~$5-10/month if you exceed free tier)

---

## Next Steps

1. **Choose a deployment option** based on your needs
2. **Set up environment variables** (see above)
3. **Deploy and test** locally first
4. **Share URL** with your friend
5. **Collect feedback** and iterate

For detailed instructions on any option, see the platform's documentation or ask for help with a specific deployment method.
