# Push to GitHub – Fix 403 "Permission denied"

## ⚠️ IMPORTANT: Revoke your exposed token

**You pasted your Personal Access Token in chat. It is compromised.**

1. Open **https://github.com/settings/tokens**
2. Find the token you used (e.g. "StudentCounsellorApp")
3. Click **Delete** or **Revoke**
4. Create a **new** token and use that for pushing. **Never paste tokens in chat, email, or screenshots.**

---

## Quick fix: Use SSH instead of HTTPS (recommended)

HTTPS + PAT often gives 403 even with correct token. **Use SSH** instead:

```powershell
cd c:\Users\sreej\StudentCounsellorApp
.\push-via-ssh.ps1
```

**If you don’t have an SSH key yet:**

1. **Create a key:**  
   `ssh-keygen -t ed25519 -C "your@email.com"`  
   (Accept default path, passphrase optional.)

2. **Add the public key to GitHub (as sreemado-cloud):**
   - Open **https://github.com/settings/keys**
   - **New SSH key** → paste contents of `%USERPROFILE%\.ssh\id_ed25519.pub`

3. Run `.\push-via-ssh.ps1` again.

The script switches the remote to SSH and pushes. No PAT needed.

---

## Diagnose first (optional)

Check that your token and repo access are correct:

```powershell
.\diagnose-github.ps1
```

Paste a **Classic** PAT when prompted. It will show token owner, repo access, and push permission.

---

## Why you get "Permission denied to sreemado-cloud"

GitHub returns 403 even when the repo exists and you use a token. Common causes:

### 1. Fine-grained token without repo access (most likely)

If you created a **Fine-grained** token:

- It does **not** get full access to all your repos by default.
- You must add **Repository access** → **Only select repositories** → choose **StudentCounsellorApp**.
- Under **Permissions** → **Repository permissions**, set **Contents** to **Read and write**.

**Simpler fix:** Use a **Classic** token instead (see below).

### 2. Use a Classic token with `repo` scope

1. Go to **https://github.com/settings/tokens**
2. **Generate new token** → **Generate new token (classic)**
3. **Note:** e.g. `StudentCounsellorApp push`
4. **Expiration:** 90 days (or your choice)
5. **Scopes:** check **repo** (full control of private repositories)
6. **Generate token** → copy it (you won’t see it again).
7. **Do not** share this token anywhere.

### 3. Token created with the wrong account

You must be logged into **sreemado-cloud** when you create the token.

- If you have multiple GitHub accounts, use an incognito/private window, log in as **sreemado-cloud**, then create the token.
- The token always acts as the account that created it.

### 4. Org / SSO

If **StudentCounsellorApp** is under an **organization** with SSO:

- After creating the token, go to **https://github.com/settings/tokens**
- Find the token → **Configure SSO** → **Authorize** for that organization.

---

## Push using the new token

### Option A: `push-with-token.ps1` (recommended)

```powershell
cd c:\Users\sreej\StudentCounsellorApp
.\push-with-token.ps1
```

When prompted, paste your **new** token (Classic with `repo`, or fine-grained with access to **StudentCounsellorApp**).  
**Do not paste the token anywhere else** (chat, email, etc.).

### Option B: GitHub CLI

If you use `gh`:

```powershell
gh auth login
# Choose: GitHub.com, HTTPS, Yes (authenticate Git), Login with browser, pick sreemado-cloud

cd c:\Users\sreej\StudentCounsellorApp
git push -u origin main
```

### Option C: SSH

If you use SSH keys with **sreemado-cloud**:

```powershell
cd c:\Users\sreej\StudentCounsellorApp
git remote set-url origin git@github.com:sreemado-cloud/StudentCounsellorApp.git
git push -u origin main
```

---

## Checklist

- [ ] Old token revoked (the one you pasted).
- [ ] New token created while logged in as **sreemado-cloud**.
- [ ] **Classic** token with **repo** scope (or **Fine-grained** with **StudentCounsellorApp** + **Contents: Read and write**).
- [ ] If org uses SSO, token authorized for SSO.
- [ ] Run `.\push-with-token.ps1` and paste **only** the new token when prompted.

---

## If it still fails

- Confirm the repo exists: **https://github.com/sreemado-cloud/StudentCounsellorApp**
- Confirm you’re logged in as **sreemado-cloud** in the browser when creating the token.
- Try **Option B** (GitHub CLI) or **Option C** (SSH) instead of the token script.
