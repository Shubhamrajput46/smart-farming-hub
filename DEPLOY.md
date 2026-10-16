# GitHub se Render par deploy (step-by-step)

## 1. Pehle check karein (apne computer par)
- `.env` aur `venv/` GitHub par **nahi** jaane chahiye (naya `.gitignore` inhe rokta hai).
- `.env` me kabhi asli keys (OPENAI_API_KEY, secret key) GitHub par push na karein.

## 2. GitHub par daalein
```
git init
git add .
git status          # check: .env, venv, db.sqlite3 list me NA ho
git commit -m "AgroSmart: production ready"
git branch -M main
git remote add origin https://github.com/<aapka-username>/<repo-name>.git
git push -u origin main
```

## 3. Render par
1. https://render.com par GitHub se login karein.
2. **New -> Blueprint** -> apna repo chunein. `render.yaml` apne aap web service + PostgreSQL bana dega.
3. Poochhe gaye environment variables bharein:
   - `OPENAI_API_KEY` (AI assistant ke liye, optional)
   - `DATA_GOV_API_KEY` (live mandi bhav ke liye, optional)
   - `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` (admin panel /admin/ ke liye)
4. **Apply** dabayein. Build me 3-5 minute lagte hain.
5. Deploy hone par `https://<app-name>.onrender.com/` khulega (index.html).

## 4. Deploy ke baad
- `/healthz/` -> `{"status": "ok"}` aana chahiye.
- Signup karke test karein, phir logout (index par aana chahiye).
- Mandi bhav: Mandi page par "Sync Live Bhav" dabayein.
- Apna domain: Render > Settings > Custom Domains. Phir env me `ALLOWED_HOSTS` aur `CSRF_TRUSTED_ORIGINS=https://yourdomain.com` daalein.

## Free plan ki limits (zaroor padhein)
- 15 min koi use na kare to site so jaati hai; pehli request 30-60 sec leti hai.
- Free PostgreSQL ~30 din baad expire ho jata hai (data ke liye paid plan ya baad me export karein).
- **Upload ki hui files (profile photo, documents) restart par delete ho jaati hain.** Asli use ke liye Render Disk (paid) ya Cloudinary/S3 lagana padega.
