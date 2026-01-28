# How to Find Admins (Super Admins vs Regular Admins)

## Where to Find Admins

### In the Admin Panel

1. **Navigate to Admin Panel:**
   - Login as an admin
   - Click on **"Admin Panel"** in the sidebar (or go to `/admin`)

2. **Filter by Admin Role:**
   - In the Admin Panel, you'll see filter buttons: **All**, **Admins**, **Counsellors**, **Students**
   - Click the **"Admins"** button to filter and see only admin users

3. **View Admin List:**
   - The table will show all admins in your institution
   - Each admin row shows:
     - Name and email
     - Role badge (purple "Admin" badge)
     - **Super Admin badge** (amber "Super Admin" badge) - if they are a super admin
     - Institution
     - Status (Active/Inactive)
     - Actions available

## Identifying Super Admins

### Visual Indicators

1. **In the Admin Panel Table:**
   - **Super Admins** have an additional amber badge below the "Admin" badge that says **"Super Admin"** with a shield icon
   - **Regular Admins** only show the purple "Admin" badge

2. **In the Stats Section:**
   - The "Admins" stat card shows total admin count
   - If there are super admins, it shows: **"Admins (X super)"** where X is the number of super admins

### Example

```
┌─────────────────────────────────────┐
│ Admin Panel                        │
├─────────────────────────────────────┤
│ Stats:                              │
│ • Admins: 3 (1 super)              │
├─────────────────────────────────────┤
│ Filter: [All] [Admins] [Counsellors]│
├─────────────────────────────────────┤
│ User Table:                         │
│                                     │
│ John Doe                            │
│ admin@university.edu                │
│ [Admin] ← Regular Admin             │
│                                     │
│ Jane Smith                          │
│ superadmin@university.edu           │
│ [Admin]                             │
│ [Super Admin] ← Super Admin        │
└─────────────────────────────────────┘
```

## Super Admin Configuration

Super admins are configured in the backend `.env` file:

```env
SUPER_ADMIN_EMAILS=admin@stateuniversity.edu,superadmin@system.com
```

- Comma-separated list of email addresses
- Case-insensitive matching
- Users with emails in this list will have `is_super_admin: true`

**Docker:** The backend container loads `backend/.env` via `env_file` in docker-compose. Ensure `SUPER_ADMIN_EMAILS` is set in `backend/.env`. After changing it, restart the backend:  
`docker compose restart backend`

## Super Admin Page

**Only super admins can access this page.**

- **URL:** `/super-admin` (or click **"Super Admin"** in the sidebar — visible only to super admins)
- **Who can open it:** Only users whose email is in `SUPER_ADMIN_EMAILS`
- **What it does:**
  - Lists all admins in your institution (including disabled ones)
  - **Disable** or **Enable** regular admin accounts
  - You cannot disable yourself or other super admins
- **Access control:**
  - Non–super admins are redirected to `/dashboard` if they try to open `/super-admin`
  - The "Super Admin" nav item is hidden for non–super admins

## What Super Admins Can Do

Super admins have additional permissions:

1. **Super Admin Page:**
   - View all admins (including disabled)
   - Disable or enable regular admin accounts

2. **Reassign Institution:**
   - Can reassign **counsellors** between institutions
   - Regular admins can only reassign students
   - The "Reassign Inst." button only appears for super admins

3. **Cross-Tenant Operations:**
   - Can perform operations across institutions (when implemented)

## Quick Steps to Find Regular Admins

1. Go to **Admin Panel** (`/admin`)
2. Click the **"Admins"** filter button
3. Look at the Role column:
   - **Regular Admins**: Only show purple "Admin" badge
   - **Super Admins**: Show purple "Admin" badge + amber "Super Admin" badge

## API Endpoint

You can also query admins via the API:

```bash
GET /api/institutions/current/users?role=admin
```

This returns all admins in your institution, with `is_super_admin` field indicating super admin status.
