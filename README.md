<<<<<<< Updated upstream
# Smart Farming (Django)

## Flow 
Signup -> Khet (Land) -> Fasal (Buwai) -> Kheti Kaam (majdoor/paani/khad/spray, kharcha apne-aap ledger me)
-> Stage update -> Katayi/Utpadan darj -> Godown stock -> Bikri (stock se zyada nahi bik sakta, partial payment, "Paisa Mila")
-> Kharcha (udhaar track) -> Reports (fasal-wise munafa, CSV, print) -> Soochnayein + Yaad-dihani.

## Notifications
- Turant: fasal register, stage change, utpadan darj, bikri, udhaar.
- Time-based (dashboard khulne par 30 min me ek baar): katayi nazdeek/late, sinchai due (12 din), pehli khad, paisa baaki,
  udhaar chukana, yaad-dihani (aaj/kal/late), document expiry.
- Cron/Task Scheduler me roz: `python manage.py generate_alerts`


## Frontend <-> API
`static/js/api.js` (`AgroAPI`) same-origin session + CSRF se REST API call karta hai.
- AI Pest page: `/api/ai/assistant/` (OPENAI_API_KEY `.env` me chahiye)
- Mandi page: "API se refresh" -> `/api/services/mandi-prices/`
- Swagger docs: /api/docs/
=======
>>>>>>> Stashed changes
