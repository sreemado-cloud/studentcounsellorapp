# How to Deploy for Friend Review - Quick Start

**Goal:** Deploy the Student Counsellor app so your friend can test it.

**Your friend does no tech work.** You handle all setup (deploy, seed, configure). They only open a link, log in with the credentials you send, and use the app.

---

## What You Do vs What Your Friend Does

| You | Your friend |
|-----|-------------|
| Deploy (Railway, ngrok, etc.) | — |
| Seed database, set up test users | — |
| Get the live app URL | — |
| Send them: **link** + **login** + **short instructions** | Open link → Log in → Use app → Tell you what they think |

**📋 Copy-paste instructions to send:** See [FRIEND_INSTRUCTIONS.md](FRIEND_INSTRUCTIONS.md). Use the ready-made text there—replace the URL and credentials, then send it (email, message, etc.). Your friend needs nothing else.

---

## 🎯 Recommended: Railway.app (15 minutes)

**Why Railway?**
- ✅ Easiest setup
- ✅ Free tier (500 hours/month)
- ✅ Automatic HTTPS
- ✅ Persistent URLs
- ✅ GitHub integration
- ✅ Perfect for testing/demos

**Time:** ~15 minutes  
**Cost:** Free (or ~$5-10/month if you exceed free tier)

### Quick Steps:

1. **Push code to GitHub** (if not already)
2. **Sign up:** https://railway.app (GitHub login)
3. **Create 3 services:**
   - MongoDB (database)
   - Backend (Python)
   - Frontend (Node.js)
4. **Set environment variables** (see guide)
5. **Seed database**
6. **Share frontend URL** with friend

**📘 Full guide:** See [QUICK_DEPLOY_RAILWAY.md](QUICK_DEPLOY_RAILWAY.md)

---

## ⚡ Alternative: ngrok (2 minutes)

**Best for:** Instant sharing, no cloud setup

1. Start app locally: `docker compose up -d`
2. Install ngrok: https://ngrok.com/download
3. Run: `ngrok http 3000`
4. Share the ngrok URL

**Note:** Your computer must stay on, and free URLs change on restart.

**📘 Details:** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#option-1-ngrok-share-local-instance--fastest)

---

## 📋 Other Options

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:
- Render.com (free tier, persistent URLs)
- Fly.io (global edge, free tier)
- DigitalOcean (simple, paid)
- AWS EKS (production, complex)
- VPS (full control, cost-effective)

---

## ✅ Pre-Deployment Checklist

Before deploying, check:

- [ ] Code pushed to GitHub
- [ ] `SECRET_KEY` generated (use `generate-secret-key.ps1`)
- [ ] `SUPER_ADMIN_EMAILS` includes your email and friend's email
- [ ] Test credentials ready (see `LOGIN_CREDENTIALS.md`)

**📋 Full checklist:** See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## 🚀 Quick Start Commands

### Generate SECRET_KEY:
```powershell
.\generate-secret-key.ps1
```

### Start locally (for ngrok):
```powershell
docker compose up -d
```

### Seed database (after deployment):
```bash
# Railway CLI
railway run python -m app.seed_data

# Or via Railway dashboard shell
python -m app.seed_data
```

---

## 📞 After Deployment

1. **Test the app yourself:**
   - Open frontend URL
   - Log in with test credentials
   - Confirm key features work

2. **Send your friend (no tech work for them):**
   - **Link:** your frontend URL
   - **Login:** email + password (e.g. `admin@stateuniversity.edu` / `Admin123!`)
   - **Instructions:** use the copy-paste text in [FRIEND_INSTRUCTIONS.md](FRIEND_INSTRUCTIONS.md)

   They just open the link, log in, click around, and tell you what they think.

3. **Test credentials:**
   - See [LOGIN_CREDENTIALS.md](LOGIN_CREDENTIALS.md) for the full list
   - Or create a dedicated reviewer user (e.g. `friend@example.com`) in Admin Panel and send those credentials instead

---

## 🆘 Troubleshooting

**"Cannot connect to backend"**
- Check `VITE_API_URL` in frontend environment variables
- Verify backend URL is correct

**"Database connection failed"**
- Verify `MONGODB_URL` format
- Check MongoDB service is running

**"Login doesn't work"**
- Ensure database is seeded
- Try resetting password via Admin Panel

**📘 More help:** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 📚 Documentation

- **[FRIEND_INSTRUCTIONS.md](FRIEND_INSTRUCTIONS.md)** - Copy-paste text to send your friend (no tech)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - All deployment options
- **[QUICK_DEPLOY_RAILWAY.md](QUICK_DEPLOY_RAILWAY.md)** - Railway step-by-step
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[LOGIN_CREDENTIALS.md](LOGIN_CREDENTIALS.md)** - Test credentials

---

## 💡 Recommendation

**For friend review/testing:** Use **Railway.app**
- Fastest setup
- Free tier
- Professional URLs
- Easy to update

**For quick demo:** Use **ngrok**
- Instant
- No cloud account needed
- Your computer must stay on

**For production:** Use **AWS EKS** or **VPS**
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details
