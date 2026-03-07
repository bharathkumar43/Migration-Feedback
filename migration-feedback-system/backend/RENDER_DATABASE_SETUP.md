# Fix "DATABASE_URL is not set" on Render

If your deploy fails with **DATABASE_URL is not set or points to localhost**, do one of the following.

## Option A: Manual Web Service (you created the service without Blueprint)

1. In **Render Dashboard**, open your **PostgreSQL** service (create one under New → PostgreSQL if needed).
2. Open the **Connect** or **Info** tab and copy the **Internal Database URL**.
3. Open your **Web Service** (the one running this backend, e.g. `migration-feedback-api`).
4. Go to **Environment** in the left sidebar.
5. Click **Add Environment Variable**:
   - **Key:** `DATABASE_URL`
   - **Value:** paste the Internal Database URL you copied.
6. Click **Save Changes**, then trigger a **Manual Deploy** (or push a new commit).

## Option B: Use Render Blueprint (render.yaml)

The repo’s `render.yaml` defines a database and wires `DATABASE_URL` automatically:

1. In Render Dashboard, use **New +** → **Blueprint**.
2. Connect the repo and set the path to the **render.yaml** that defines the web service and database (e.g. `backend/render.yaml` or the one at your repo root that references it).
3. Render will create the PostgreSQL database and the Web Service and set `DATABASE_URL` from the database.
4. Ensure the database name in the blueprint matches (e.g. `migration-feedback-db`).

If your Web Service was created manually (not from this Blueprint), use **Option A** to add `DATABASE_URL` by hand.
