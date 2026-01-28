# Deployment Checklist

Use this checklist before deploying for friend review or production.

## Pre-Deployment

- [ ] **Code is ready:**
  - [ ] All features tested locally
  - [ ] No console errors
  - [ ] Code pushed to GitHub (if using Git-based deployment)

- [ ] **Environment variables prepared:**
  - [ ] `SECRET_KEY` generated (not default)
  - [ ] `MONGODB_URL` ready (or MongoDB service created)
  - [ ] `SUPER_ADMIN_EMAILS` set (include your email and friend's email)
  - [ ] `VITE_API_URL` set for frontend (if backend is separate)

- [ ] **Security:**
  - [ ] Default passwords changed
  - [ ] `.env` files not committed to Git
  - [ ] CORS configured for production domain
  - [ ] HTTPS enabled (automatic on most platforms)

## Deployment Steps

- [ ] **MongoDB:**
  - [ ] MongoDB service created
  - [ ] Connection string copied
  - [ ] Database accessible from backend

- [ ] **Backend:**
  - [ ] Backend service created
  - [ ] Environment variables set
  - [ ] Build successful
  - [ ] Health check passing (`/health` endpoint)
  - [ ] Public URL obtained

- [ ] **Frontend:**
  - [ ] Frontend service created
  - [ ] `VITE_API_URL` set to backend URL
  - [ ] Build successful
  - [ ] Public URL obtained

- [ ] **Database:**
  - [ ] Database seeded with test data
  - [ ] Test users created
  - [ ] Institutions created

## Post-Deployment Testing

- [ ] **Access:**
  - [ ] Frontend loads at public URL
  - [ ] No CORS errors in browser console
  - [ ] API calls work (check Network tab)

- [ ] **Authentication:**
  - [ ] Can register new user
  - [ ] Can login with test credentials
  - [ ] JWT token received

- [ ] **Features:**
  - [ ] Dashboard loads
  - [ ] Admin Panel accessible (for admins)
  - [ ] Super Admin page accessible (for super admins)
  - [ ] Can create users
  - [ ] Can assign students to counsellors
  - [ ] Messages work
  - [ ] Appointments work

- [ ] **Multi-tenancy:**
  - [ ] Users see only their institution's data
  - [ ] Students can't see other students
  - [ ] Counsellors see only assigned students

## Sharing with Friend (No Tech Work for Them)

- [ ] **Access provided:**
  - [ ] Frontend URL shared
  - [ ] Login (email + password) shared
  - [ ] Short instructions sent — use copy-paste text from [FRIEND_INSTRUCTIONS.md](FRIEND_INSTRUCTIONS.md)

- [ ] **Friend only needs to:**
  - [ ] Open the link
  - [ ] Log in
  - [ ] Use the app and share feedback
  - [ ] No setup, installs, or technical steps

## Monitoring

- [ ] **Logs:**
  - [ ] Know how to view backend logs
  - [ ] Know how to view frontend logs
  - [ ] Know how to view database logs

- [ ] **Alerts:**
  - [ ] Set up monitoring (if platform supports)
  - [ ] Know how to check service health

## Rollback Plan

- [ ] **If something breaks:**
  - [ ] Know how to rollback to previous deployment
  - [ ] Have backup of database (if possible)
  - [ ] Know how to restart services

---

## Quick Test Credentials

After seeding, use these (or create new ones):

**Super Admin:**
- Email: `admin@stateuniversity.edu`
- Password: `Admin123!`

**Regular Admin:**
- Email: `admin-helper@stateuniversity.edu`
- Password: (set via Admin Panel "Reset password")

**Counsellor:**
- Email: `counsellor@stateuniversity.edu`
- Password: `Counsellor123!`

**Student:**
- Email: `student@stateuniversity.edu`
- Password: `Student123!`

See `LOGIN_CREDENTIALS.md` for full list.

---

## Common Issues

### "Cannot connect to backend"
- Check `VITE_API_URL` is correct
- Verify backend is running
- Check CORS settings

### "Database connection failed"
- Verify `MONGODB_URL` format
- Check MongoDB service is running
- Ensure network connectivity

### "Login doesn't work"
- Check database is seeded
- Verify user exists
- Check password (try reset via Admin Panel)

### "CORS errors"
- Add frontend URL to `ALLOWED_ORIGINS` in backend
- Check `VITE_API_URL` doesn't have trailing slash issues

---

## Support

- See `DEPLOYMENT_GUIDE.md` for detailed deployment options
- See `QUICK_DEPLOY_RAILWAY.md` for Railway-specific guide
- Check platform-specific documentation
