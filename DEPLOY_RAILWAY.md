# GitHub se Railway par deploy

## 1. GitHub par push (pehle `.env` aur `venv/` check karein - `git status` me na dikhein)
```
git init
git add .
git commit -m "AgroSmart production ready"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

## 2. Railway par project banayein
1. https://railway.com -> GitHub se login -> **New Project -> Deploy from GitHub repo** -> apna repo chunein.
2. Same project me **+ New -> Database -> Add PostgreSQL**.

## 3. Web service ke Variables (service -> Variables)
| Variable | Value |
|---|---|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | lamba random text (https://djecrety.ir se bana lein) |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Postgres service ka naam alag ho to wahi likhein) |
| `MEDIA_ROOT` | `/data/media` (neeche Volume wale step ke baad) |
| `OPENAI_API_KEY` | optional (AI assistant) |
| `DATA_GOV_API_KEY` | optional (live mandi bhav) |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | optional (admin panel ke liye) |

## 4. Public URL aur Volume
- Service -> **Settings -> Networking -> Generate Domain**. Domain apne aap ALLOWED_HOSTS/CSRF me add ho jata hai (`RAILWAY_PUBLIC_DOMAIN`).
- Uploaded files bachane ke liye: service par right-click / **+ Add Volume**, mount path `/data`. Phir `MEDIA_ROOT=/data/media`.

## 5. Check
- `https://<domain>/healthz/` -> `{"status": "ok"}`
- `/` par index.html, signup, login, logout (index par aana chahiye).

## Common errors
- **Healthcheck fail / 400 Bad Request:** `DEBUG=False` ke saath `DJANGO_SECRET_KEY` set honi chahiye, warna app start hi nahi hoti. Deploy logs dekhein.
- **DisallowedHost:** Generate Domain karna bhoole, ya custom domain ke liye `ALLOWED_HOSTS=yourdomain.com` aur `CSRF_TRUSTED_ORIGINS=https://yourdomain.com` daalein.
- **Site bina CSS ke:** deploy logs me `collectstatic` ka error dekhein.
- **Data/photos gayab:** Volume mount nahi kiya, ya `MEDIA_ROOT` set nahi.

## Cost
Railway ka permanent free plan nahi hai: trial credit milta hai, uske baad Hobby plan (~$5/month usage-based).
