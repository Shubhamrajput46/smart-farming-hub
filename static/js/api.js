/* AgroSmart - frontend API client (Django REST API se connect karta hai).
 * Login ke baad browser ka session cookie use hota hai (same-origin) + CSRF token.
 * Bahar ke clients (mobile app, Postman) JWT use kar sakte hain: /api/auth/token/.
 *
 * Use:
 *   AgroAPI.get('/api/services/mandi-prices/?search=wheat').then(data => ...)
 *   AgroAPI.post('/api/ai/assistant/', { prompt: 'Gehu me rust ka ilaj?' })
 */
(function (global) {
    'use strict';

    function csrfToken() {
        var m = document.querySelector('meta[name="csrf-token"]');
        if (m && m.content) return m.content;
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function ApiError(status, data) {
        var msg = (data && (data.detail || data.error)) || ('Request fail hui (' + status + ')');
        if (data && typeof data === 'object' && !data.detail && !data.error) {
            var first = Object.keys(data)[0];
            if (first) msg = first + ': ' + [].concat(data[first]).join(' ');
        }
        var e = new Error(msg);
        e.status = status; e.data = data;
        return e;
    }

    function request(method, url, body) {
        var opts = {
            method: method,
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
        };
        if (method !== 'GET') opts.headers['X-CSRFToken'] = csrfToken();
        if (body !== undefined) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
        return fetch(url, opts).then(function (res) {
            // Session khatam (auto-logout / expiry) -> login page par bhejo
            if ((res.status === 401 || res.status === 403) && global.AGRO && AGRO.loginUrl) {
                return res.json().catch(function () { return {}; }).then(function (data) {
                    if (res.status === 401 || /credentials|authenticat/i.test(data.detail || '')) {
                        window.location.href = AGRO.loginUrl + '?next=' + encodeURIComponent(location.pathname);
                    }
                    throw ApiError(res.status, data);
                });
            }
            if (res.status === 204) return null;
            return res.json().catch(function () { return null; }).then(function (data) {
                if (!res.ok) throw ApiError(res.status, data);
                return data;
            });
        });
    }

    global.AgroAPI = {
        get: function (url) { return request('GET', url); },
        post: function (url, data) { return request('POST', url, data || {}); },
        put: function (url, data) { return request('PUT', url, data || {}); },
        patch: function (url, data) { return request('PATCH', url, data || {}); },
        del: function (url) { return request('DELETE', url); },
        // Ready-made helpers
        mandiPrices: function (q) { return request('GET', '/api/services/mandi-prices/' + (q ? '?search=' + encodeURIComponent(q) : '')); },
        schemes: function () { return request('GET', '/api/services/schemes/'); },
        askAssistant: function (prompt) { return request('POST', '/api/ai/assistant/', { prompt: prompt }); },
        lands: function () { return request('GET', '/api/lands/'); },
        crops: function () { return request('GET', '/api/crops/'); }
    };
})(window);
