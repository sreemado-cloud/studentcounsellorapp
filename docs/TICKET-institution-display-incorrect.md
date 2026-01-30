# Ticket: Institution displays incorrectly (e.g. "State University" for wrong user)

## Summary
When logged in as **Christina** (email: `sreejeshkm@gmail.com`), her **institution** is shown as **"State University"** in the Dashboard, Layout, and Admin panel even though that is incorrect for her. The issue is **not limited to the Admin panel**; it affects **auth-level** user data (login response, `/auth/me`), which feeds the dashboard and rest of the app.

## Steps to reproduce
1. Ensure DB is seeded (institutions: State University, City Community College, Tech High School; users per institution).
2. Create or use a user whose **actual** institution is **not** State University (e.g. Christina / `sreejeshkm@gmail.com` belongs to City Community College or another institution).
3. Log in as that user.
4. Open **Dashboard** and **Layout** (sidebar). Check **Admin panel** user table if applicable.
5. **Observed:** Institution displays as "State University" (or another wrong institution).
6. **Expected:** Institution displays as the user’s actual institution (e.g. City Community College).

## Environment
- **App:** Student Counsellor App (FastAPI backend, React frontend, MongoDB).
- **Run:** Docker Compose (MongoDB, backend, frontend).
- **Tenancy:** Row-level (shared DB) or db-per-tenant; institutions collection in shared/default DB.

## What we've already tried (no fix)
- **List users API (`GET /api/institutions/current/users`):** Resolve `institution_name` per user from `user.institution_id`; batch-fetch institutions from **shared (default) DB**; normalize `institution_id` (str vs ObjectId). Split Institution vs Assigned Counsellor columns in Admin panel.
- **Auth login:** Fetch institution by `user.institution_id` from **`get_default_database().institutions`** (shared DB); use `ObjectId(str(institution_id))`.
- **Auth `/me`:** Same — resolve institution from **`get_default_database().institutions`** using `current_user["institution_id"]`.
- **Users API:** `PUT /me` and `GET /users/{id}` — institution fetch switched to **`get_default_database().institutions`**.
- **Assign-counsellor:** Accept `counsellor_id` from JSON body (was query-only); store string; refetch users after assign. Assigned Counsellor column now works.

## Suspected area
- **Institution resolution:** Either we’re still using the wrong DB/collection for institutions, or `user.institution_id` / `current_user["institution_id"]` is wrong or overwritten somewhere (e.g. tenant context, middleware, or user fetch).
- **Data:** Confirm in MongoDB that the user document for Christina (`sreejeshkm@gmail.com`) has the correct `institution_id` and that the corresponding institution document has the expected `name`.

## Request
- **Cursor team:** Please treat this as a known, unresolved bug. Debug why institution still resolves incorrectly for the logged-in user (login, `/me`, dashboard) despite using the shared DB for institutions and the user’s `institution_id`.
- **Next steps:** Inspect tenant vs user `institution_id` usage; verify MongoDB contents for the affected user and institutions; trace institution resolution in auth and user APIs.

---
*Generated for tracking. Last updated: 2026-01-26.*
