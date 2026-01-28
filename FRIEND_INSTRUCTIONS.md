# Instructions for Your Friend (Non-Technical)

**You do all the tech work.** Your friend only needs to open a link and log in.

---

## What You Do (Tech Work)

1. **Deploy the app** (you) — e.g. Railway or ngrok, per `HOW_TO_DEPLOY_FOR_REVIEW.md`
2. **Seed the database** (you) — create test users
3. **Get the live URL** (you) — e.g. `https://yourapp.up.railway.app`
4. **Send your friend** (you):
   - The **link** (URL)
   - **Login email and password**
   - The **short instructions** below (copy-paste into email/message)

---

## What to Send Your Friend (Copy-Paste)

Copy the text below, replace the placeholders, and send it to your friend.

---

**Subject: Quick test of Student Counsellor app**

Hi,

Could you try the app and tell me what you think? No setup needed—just use the link and log in.

**1. Open this link in your browser:**  
`https://YOUR-FRONTEND-URL-HERE`

**2. Log in with:**
- **Email:** `admin@stateuniversity.edu`
- **Password:** `Admin123!`

**3. Try these (optional):**
- Look around the dashboard
- Open **Messages** and **Appointments**
- Go to **Admin Panel** (in the menu) and see the user list
- If you want, create a test student or counsellor via **Add User**

**4. Reply with:**
- What worked well
- Anything confusing or broken
- Any ideas to improve it

No need to install anything or do any technical steps. Just use the link and log in.

Thanks!

---

## Alternative: Simpler Version

If you prefer shorter instructions:

---

**Link:** `https://YOUR-FRONTEND-URL-HERE`  
**Login:** Email `admin@stateuniversity.edu` / Password `Admin123!`

Please open the link, log in, click around, and tell me what you think. No setup required.

---

## Customize Before Sending

- **URL:** Replace `https://YOUR-FRONTEND-URL-HERE` with your real frontend URL (e.g. from Railway or ngrok).
- **Credentials:** Use the admin account above, or create a separate test user (e.g. `reviewer@test.com`) in Admin Panel and send those instead.
- **Tone:** Adjust the wording to match how you usually write to your friend.

---

## If You Create a Dedicated Reviewer Account

1. Deploy the app and log in as admin.
2. In **Admin Panel** → **Add User** → create e.g. `friend@example.com` as **Admin** (or **Counsellor** if you prefer).
3. Use **Reset password** to set a simple password (e.g. `Reviewer123!`).
4. Send your friend:
   - **Link:** your frontend URL  
   - **Email:** `friend@example.com`  
   - **Password:** `Reviewer123!`  
   - **Instructions:** same as above (open link, log in, try the app, share feedback).

---

## Summary

| Who | What |
|-----|------|
| **You** | Deploy, configure, seed DB, get URL, send link + login + instructions |
| **Your friend** | Open link → Log in → Use app → Share feedback |

Your friend does **no** tech work—only uses the app in their browser.
