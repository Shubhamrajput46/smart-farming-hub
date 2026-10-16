# Smart Farming (Django)

## Chalane ke steps
```
python -m venv venv
venv\Scripts\activate          (Windows)   |   source venv/bin/activate  (Linux/Mac)
pip install -r requirements.txt
copy .env.example .env         (MySQL chahiye to DB_* uncomment karein, nayi khaali database banayein)
python manage.py migrate
python manage.py seed_demo     (optional: demo user  demo / demo12345 + sample data)
python manage.py runserver
```
Project start hote hi **http://127.0.0.1:8000/** par `index.html` (landing page) khulta hai.
Login: /accounts/login/ | Signup: /accounts/signup/ | Dashboard: /dashboard/

## Flow (asli kheti jaisa)
Signup -> Khet (Land) -> Fasal (Buwai) -> Kheti Kaam (majdoor/paani/khad/spray, kharcha apne-aap ledger me)
-> Stage update -> Katayi/Utpadan darj -> Godown stock -> Bikri (stock se zyada nahi bik sakta, partial payment, "Paisa Mila")
-> Kharcha (udhaar track) -> Reports (fasal-wise munafa, CSV, print) -> Soochnayein + Yaad-dihani.

## Notifications
- Turant: fasal register, stage change, utpadan darj, bikri, udhaar.
- Time-based (dashboard khulne par 30 min me ek baar): katayi nazdeek/late, sinchai due (12 din), pehli khad, paisa baaki,
  udhaar chukana, yaad-dihani (aaj/kal/late), document expiry.
- Cron/Task Scheduler me roz: `python manage.py generate_alerts`

## Structure
accounts/ (login, signup, profile, documents) | farms/ (land, crop, operations, dashboard)
finance/ (expense, sale, reports) | notifications/ (alerts + reminders) | ai_services/ (mandi, yojana; AI pest scan baad me)
templates/ static/css/style.css static/js/app.js

Tests: `python manage.py test`


## Auto-logout (website chhodne par)
- Tab/window band hone par browser `/accounts/leaving/` ko beacon bhejta hai (`static/js/app.js`).
- Server `SITE_LEAVE_GRACE_SECONDS` (default 15 sec) tak wait karta hai; user wapas nahi aaya to logout (`accounts/middleware.py`).
- Reload ya ek page se doosre page par jaane par logout nahi hota. Doosra tab khula ho to bhi nahi.
- `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` se browser band hone par cookie bhi delete ho jaati hai.

## Frontend <-> API
`static/js/api.js` (`AgroAPI`) same-origin session + CSRF se REST API call karta hai.
- AI Pest page: `/api/ai/assistant/` (OPENAI_API_KEY `.env` me chahiye)
- Mandi page: "API se refresh" -> `/api/services/mandi-prices/`
- Swagger docs: /api/docs/
