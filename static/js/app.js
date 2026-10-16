/* Smart Farming - common JS: hamburger menu, toasts, notification bell, modals, auto-calc */
(function () {
    'use strict';
    var body = document.body;

    // ---------- Hamburger menu (mobile) ----------
    var toggle = document.getElementById('menuToggle');
    var overlay = document.getElementById('overlay');
    function closeMenu() { body.classList.remove('menu-open'); }
    if (toggle) toggle.addEventListener('click', function () { body.classList.toggle('menu-open'); });
    if (overlay) overlay.addEventListener('click', closeMenu);
    document.querySelectorAll('.sidebar a').forEach(function (a) { a.addEventListener('click', closeMenu); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeMenu(); closeAllModals(); closeNotif(); } });

    // ---------- Toasts ----------
    function dismissToast(t) { t.classList.add('hide'); setTimeout(function () { t.remove(); }, 400); }
    document.querySelectorAll('.toast').forEach(function (t) {
        var btn = t.querySelector('button');
        if (btn) btn.addEventListener('click', function () { dismissToast(t); });
        setTimeout(function () { dismissToast(t); }, 6000);
    });
    function showToast(text, type) {
        var stack = document.getElementById('toastStack');
        if (!stack) return;
        var t = document.createElement('div');
        t.className = 'toast ' + (type || 'info');
        t.innerHTML = '<i class="fa-solid fa-bell"></i><span></span><button type="button">&times;</button>';
        t.querySelector('span').textContent = text;
        t.querySelector('button').addEventListener('click', function () { dismissToast(t); });
        stack.appendChild(t);
        setTimeout(function () { dismissToast(t); }, 7000);
    }

    // ---------- Notification bell ----------
    var bell = document.getElementById('notifBell');
    var menu = document.getElementById('notifMenu');
    function closeNotif() { if (menu) menu.classList.remove('open'); }
    if (bell && menu) {
        bell.addEventListener('click', function (e) { e.stopPropagation(); menu.classList.toggle('open'); });
        document.addEventListener('click', function (e) { if (!menu.contains(e.target)) closeNotif(); });
    }
    var badge = document.getElementById('notifBadge');
    var lastUnread = badge ? parseInt(badge.dataset.count || '0', 10) : 0;
    function setBadge(n) {
        if (!badge) return;
        badge.textContent = n > 99 ? '99+' : n;
        badge.style.display = n > 0 ? 'flex' : 'none';
        document.querySelectorAll('.nav-unread').forEach(function (el) { el.textContent = n; el.style.display = n > 0 ? '' : 'none'; });
    }
    function poll() {
        if (!bell || document.hidden) return;
        fetch(bell.dataset.api, { headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) {
                if (!d) return;
                if (d.unread > lastUnread && d.latest) showToast('Nayi soochna: ' + d.latest.title, d.latest.severity);
                lastUnread = d.unread; setBadge(d.unread);
            }).catch(function () {});
    }
    if (bell) setInterval(poll, 60000);

    // ---------- Modals ----------
    function closeAllModals() { document.querySelectorAll('.modal.open').forEach(function (m) { m.classList.remove('open'); }); }
    document.addEventListener('click', function (e) {
        var opener = e.target.closest('[data-modal-open]');
        if (opener) {
            var m = document.getElementById(opener.dataset.modalOpen);
            if (!m) return;
            var form = m.querySelector('form');
            if (form && opener.dataset.action) form.action = opener.dataset.action;
            var amt = m.querySelector('[name=amount]');
            if (amt && opener.dataset.amount) { amt.value = opener.dataset.amount; amt.max = opener.dataset.amount; }
            var label = m.querySelector('[data-modal-label]');
            if (label && opener.dataset.label) label.textContent = opener.dataset.label;
            m.classList.add('open');
            if (amt) amt.focus();
        }
        if (e.target.closest('[data-modal-close]') || e.target.classList.contains('modal')) closeAllModals();
    });

    // ---------- Disable double-submit ----------
    document.querySelectorAll('form[data-once]').forEach(function (f) {
        f.addEventListener('submit', function () {
            var b = f.querySelector('button[type=submit]');
            if (b) { b.disabled = true; b.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Save ho raha hai...'; }
        });
    });

    // ---------- Auto-submit selects (stage change, filters) ----------
    document.querySelectorAll('select[data-autosubmit]').forEach(function (s) {
        s.addEventListener('change', function () { s.form.submit(); });
    });

    // ---------- Live table search ----------
    var search = document.getElementById('liveSearch');
    if (search) {
        search.addEventListener('input', function () {
            var q = search.value.toLowerCase();
            document.querySelectorAll('[data-searchable] tbody tr').forEach(function (tr) {
                tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
            });
        });
    }

    // ---------- Auto-calc totals on forms ----------
    function num(name) { var el = document.querySelector('[name="' + name + '"]'); return el ? parseFloat(el.value) || 0 : 0; }
    function fmt(n) { return '\u20B9' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 }); }
    var calc = document.querySelector('[data-calc]');
    if (calc) {
        var out = document.getElementById('calcOut'), type = calc.dataset.calc;
        var costEl = document.querySelector('[name=total_cost]');
        var userEditedCost = costEl && costEl.value !== '' && parseFloat(costEl.value) > 0;
        if (costEl) costEl.addEventListener('input', function () { userEditedCost = true; update(); });
        function update() {
            if (type === 'operation') {
                var auto = num('labour_count') * num('labour_cost_per_person');
                var total = userEditedCost && num('total_cost') > 0 ? num('total_cost') : auto;
                out.textContent = fmt(total);
            } else if (type === 'sale') {
                var gross = num('quantity_quintals') * num('price_per_quintal');
                var net = gross - num('deductions');
                out.textContent = fmt(net);
                var bal = document.getElementById('calcBalance');
                if (bal) bal.textContent = fmt(Math.max(0, net - num('amount_received')));
            }
        }
        document.querySelectorAll('form input, form select').forEach(function (i) { i.addEventListener('input', update); });
        update();
    }

    // ---------- Premium UX: topbar shadow, scroll-to-top, bottom menu, swipe, reveal ----------
    var topbar = document.querySelector('.topbar'), toTop = document.getElementById('toTop');
    var ticking = false;
    function onScroll() {
        var y = window.scrollY || 0;
        if (topbar) topbar.classList.toggle('scrolled', y > 8);
        if (toTop) toTop.classList.toggle('show', y > 500);
        ticking = false;
    }
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
    onScroll();
    if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

    var bottomMenu = document.getElementById('bottomMenu');
    if (bottomMenu) bottomMenu.addEventListener('click', function () { body.classList.toggle('menu-open'); });

    // Sidebar ko left swipe se band karo (mobile)
    var sidebar = document.querySelector('.sidebar'), sx = null;
    if (sidebar) {
        sidebar.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; }, { passive: true });
        sidebar.addEventListener('touchend', function (e) {
            if (sx !== null && sx - e.changedTouches[0].clientX > 60) closeMenu();
            sx = null;
        }, { passive: true });
    }

    // Cards ko scroll par smooth reveal (stagger ke saath)
    var revealEls = document.querySelectorAll('.main-layout .glass-card, .main-layout .stat-box, .main-layout .notif-page-item');
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if ('IntersectionObserver' in window && !reduce) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
        revealEls.forEach(function (el, i) {
            if (el.closest('.modal')) return;
            el.classList.add('reveal');
            el.style.setProperty('--d', Math.min(i % 6, 5) * 0.06 + 's');
            io.observe(el);
        });
    }

    // Progress bars 0 se animate hon
    document.querySelectorAll('.progress > span').forEach(function (bar) {
        var w = bar.style.width; if (!w) return;
        bar.style.width = '0';
        requestAnimationFrame(function () { requestAnimationFrame(function () { bar.style.width = w; }); });
    });

    // Submit buttons par loading state (data-once ke alawa bhi)
    document.querySelectorAll('form:not([data-once])').forEach(function (f) {
        f.addEventListener('submit', function () {
            var b = f.querySelector('button.btn-primary-glow[type=submit], button.btn-primary[type=submit]');
            if (b) b.classList.add('is-loading');
        });
    });

    // ---------- Auto-logout jab user website chhod de ----------
    // Tab/window band hone par server ko beacon jaata hai. Server 15 sec tak wait karta hai;
    // agar user wapas nahi aaya to logout. Reload / page-to-page navigation me nayi request
    // turant aa jaati hai, isliye logout nahi hota. Doosra tab khula ho to bhi logout nahi hota.
    (function () {
        if (!window.AGRO || !AGRO.leavingUrl) return;
        var KEY = 'agro_open_tabs', TTL = 90000;
        var tabId = Math.random().toString(36).slice(2);
        function csrf() {
            var m = document.querySelector('meta[name="csrf-token"]');
            return m ? m.content : '';
        }
        function readTabs() {
            try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; }
        }
        function writeTabs(t) { try { localStorage.setItem(KEY, JSON.stringify(t)); } catch (e) {} }
        function touch() {
            var t = readTabs(), now = Date.now();
            Object.keys(t).forEach(function (k) { if (now - t[k] > TTL) delete t[k]; });
            t[tabId] = now; writeTabs(t);
        }
        function send(action) {
            var fd = new FormData();
            fd.append('csrfmiddlewaretoken', csrf());
            fd.append('action', action);
            if (navigator.sendBeacon) { navigator.sendBeacon(AGRO.leavingUrl, fd); }
            else { fetch(AGRO.leavingUrl, { method: 'POST', body: fd, credentials: 'same-origin', keepalive: true }); }
        }
        touch();
        send('stay');                      // naya page khula = user site par hi hai
        setInterval(touch, 5000);
        window.addEventListener('pageshow', function (e) { if (e.persisted) { touch(); send('stay'); } });
        window.addEventListener('pagehide', function () {
            var t = readTabs(), now = Date.now();
            delete t[tabId]; writeTabs(t);
            var others = Object.keys(t).filter(function (k) { return now - t[k] <= TTL; });
            if (others.length === 0) send('leave');
        });
    })();

    // ---------- Monthly chart (reports) ----------
    function initChart() {
    var chartEl = document.getElementById('monthlyChart');
    var dataEl = document.getElementById('chartData');
    if (chartEl && dataEl && window.Chart) {
        var d = JSON.parse(dataEl.textContent);
        new Chart(chartEl, {
            type: 'bar',
            data: { labels: d.labels, datasets: [
                { label: 'Bikri (Income)', data: d.income, backgroundColor: '#22c55e', borderRadius: 6 },
                { label: 'Kharcha (Expense)', data: d.expense, backgroundColor: '#ef4444', borderRadius: 6 } ] },
            options: { responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1' } } },
                scales: { x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.06)' } } } }
        });
    }
    }
    window.__initChart = initChart;
})();
