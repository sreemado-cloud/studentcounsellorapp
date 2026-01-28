# Quick Deploy to Railway.app - Step by Step

This guide walks you through deploying the Student Counsellor app to Railway.app in ~15 minutes.

## Prerequisites

- GitHub account
- Railway.app account (free signup at https://railway.app)
- Your code pushed to a GitHub repository

---

## Step 1: Prepare Your Repository

1. **Push your code to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Note your repository URL** (e.g., `https://github.com/yourusername/StudentCounsellorApp`)

---

## Step 2: Sign Up for Railway

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign in with GitHub (recommended)

---

## Step 3: Create MongoDB Service

1. In Railway dashboard, click **"+ New"**
2. Select **"Database"** → **"MongoDB"**
3. Railway will create a MongoDB instance
4. **Copy the connection string:**
   - Click on the MongoDB service
   - Go to "Variables" tab
   - Copy `MONGO_URL` value (looks like: `mongodb://mongo:password@containers-us-west-xxx.railway.app:xxxxx`)

---

## Step 4: Deploy Backend

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your `StudentCounsellorApp` repository
3. Railway will detect it's a Python app

4. **Configure the service:**
   - **Root Directory:** `backend`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variables:**
   - Click "Variables" tab
   - Add these variables:
     ```
     MONGODB_URL=<paste the MONGO_URL from MongoDB service>
     DATABASE_NAME=student_counsellor
     SECRET_KEY=<generate: openssl rand -hex 32>
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     SUPER_ADMIN_EMAILS=admin@stateuniversity.edu,your-email@example.com
     ```
   - **Generate SECRET_KEY:**
     - Windows PowerShell: `[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))`
     - Or use: https://generate-secret.vercel.app/32

6. **Deploy:**
   - Railway will automatically build and deploy
   - Wait for "Deploy Successful"
   - **Copy the public URL** (e.g., `https://backend-production-xxxx.up.railway.app`)

---

## Step 5: Deploy Frontend

1. Click **"+ New"** → **"GitHub Repo"**
2. Select the same repository (`StudentCounsellorApp`)
3. Railway will detect it's a Node.js app

4. **Configure the service:**
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npx serve -s dist -l $PORT`
   - Or use Railway's auto-detected static site settings

5. **Add Environment Variable:**
   - Click "Variables" tab
   - Add:
     ```
     VITE_API_URL=https://<your-backend-url>/api
     ```
   - Replace `<your-backend-url>` with your backend's Railway URL (without `/api`)

6. **Deploy:**
   - Railway will build and deploy
   - Wait for "Deploy Successful"
   - **Copy the public URL** (e.g., `https://frontend-production-xxxx.up.railway.app`)

---

## Step 6: Seed the Database

1. **Option A: Using Railway CLI** (recommended):
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login
   railway login
   
   # Link to your project
   railway link
   
   # Run seed script
   cd backend
   railway run python -m app.seed_data
   ```

2. **Option B: Using Railway Dashboard:**
   - Go to Backend service
   - Click "Deployments" → Latest deployment
   - Click "View Logs" → "Shell"
   - Run: `python -m app.seed_data`

---

## Step 7: Test and Share

1. **Test the deployment:**
   - Open your frontend URL in a browser
   - Try logging in with test credentials (see `LOGIN_CREDENTIALS.md`)

2. **Share with your friend (they do no tech work):**
   - Send them the **frontend URL**
   - Send **login:** e.g. `admin@stateuniversity.edu` / `Admin123!`
   - Send **simple instructions:** use the copy-paste text in [FRIEND_INSTRUCTIONS.md](FRIEND_INSTRUCTIONS.md)

   They only open the link, log in, and use the app. No setup, no installs.

---

## Troubleshooting

### Backend not starting:
- Check logs in Railway dashboard
- Verify `MONGODB_URL` is correct
- Ensure `SECRET_KEY` is set

### Frontend can't connect to backend:
- Verify `VITE_API_URL` includes `/api` at the end
- Check backend URL is correct (no trailing slash)
- Check CORS settings in backend (should allow frontend URL)

### Database connection errors:
- Verify `MONGODB_URL` format
- Check MongoDB service is running
- Ensure network connectivity (Railway services can talk to each other)

### Build failures:
- Check build logs in Railway
- Verify all dependencies are in `requirements.txt` (backend) or `package.json` (frontend)
- Ensure root directory is set correctly

---

## Updating Your Deployment

1. **Push changes to GitHub:**
   ```bash
   git add .
   git commit -m "Update feature"
   git push
   ```

2. **Railway auto-deploys:**
   - Railway watches your GitHub repo
   - New deployments trigger automatically
   - Check "Deployments" tab for status

---

## Custom Domain (Optional)

1. Go to Frontend service → "Settings" → "Domains"
2. Add your custom domain
3. Railway provides DNS records to add
4. Update `VITE_API_URL` if needed
5. Update backend `ALLOWED_ORIGINS` to include your domain

---

## Cost

- **Free tier:** 500 hours/month, $5 credit
- **After free tier:** ~$5-10/month for small deployments
- **MongoDB:** Included in free tier (512MB)

---

## Next Steps

- ✅ Test all features
- ✅ Share URL with friend
- ✅ Collect feedback
- ✅ Iterate and redeploy

For other deployment options, see `DEPLOYMENT_GUIDE.md`.
