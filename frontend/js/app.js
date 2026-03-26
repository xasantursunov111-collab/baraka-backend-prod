/* ============================================
   BARAKA — API Client & Application Logic
   ============================================ */

const API_BASE = '/api/v1';

// ==================== API Client ====================

const api = {
  async request(url, options = {}) {
    try {
      const token = localStorage.getItem('baraka_token');
      const headers = { ...options.headers };
      if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = headers['Content-Type'] || 'application/json';
      }
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const res = await fetch(`${API_BASE}${url}`, {
        headers,
        ...options,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let msg = err.detail || `Xatolik: ${res.status}`;
        if (Array.isArray(err.detail)) msg = err.detail.map(e => e.msg).join(', ');
        else if (typeof err.detail === 'object') msg = JSON.stringify(err.detail);
        throw new Error(msg);
      }
      return await res.json();
    } catch (e) {
      showToast(e.message, 'error');
      throw e;
    }
  },

  // Users
  createUser(data) { return this.request('/users/', { method: 'POST', body: JSON.stringify(data) }); },
  getUsers(role = '') { return this.request(`/users/?role=${role}`); },
  getUser(id) { return this.request(`/users/${id}`); },
  updateMyProfile(data) { return this.request(`/users/me`, { method: 'PUT', body: JSON.stringify(data) }); },

  // Master Profile
  getMasterProfile(id) { return this.request(`/masters/${id}/profile`); },
  getMasterStats(id) { return this.request(`/masters/${id}/stats`); },

  // Guilds
  createGuild(data) { return this.request('/guilds/', { method: 'POST', body: JSON.stringify(data) }); },
  getGuilds() { return this.request('/guilds/'); },
  joinGuild(data) { return this.request('/guilds/join', { method: 'POST', body: JSON.stringify(data) }); },
  getGuildMembers(id) { return this.request(`/guilds/${id}/members`); },

  // Apprenticeships
  createApprenticeship(data) { return this.request('/apprenticeships/', { method: 'POST', body: JSON.stringify(data) }); },
  getApprentices(masterId) { return this.request(`/apprenticeships/master/${masterId}`); },
  getJamoaDashboard() { return this.request('/ustoz-shogird/dashboard'); },

  // Duolar
  createDuo(data) { return this.request('/duolar/', { method: 'POST', body: JSON.stringify(data) }); },
  getUserDuolar(userId) { return this.request(`/duolar/user/${userId}`); },
  getDuolarGlobal() { return this.request('/duolar/'); },

  // Orders
  createOrder(data) { return this.request('/orders/', { method: 'POST', body: JSON.stringify(data) }); },
  getOrders(status) { return this.request(`/orders/${status ? '?status=' + status : ''}`); },
  getOrder(id) { return this.request(`/orders/${id}`); },
  acceptOrder(id, data) { return this.request(`/orders/${id}/accept`, { method: 'PUT', body: JSON.stringify(data) }); },
  startOrder(id) { return this.request(`/orders/${id}/start`, { method: 'PUT' }); },
  extendDeadline(id, data) { return this.request(`/orders/${id}/extend`, { method: 'PUT', body: JSON.stringify(data) }); },
  completeOrder(id) { return this.request(`/orders/${id}/complete`, { method: 'PUT' }); },
  giveRizolik(id, data) { return this.request(`/orders/${id}/rizolik`, { method: 'PUT', body: JSON.stringify(data) }); },
  requestSOS(id) { return this.request(`/orders/${id}/sos`, { method: 'PUT' }); },
  acceptSOS(id, data) { return this.request(`/orders/${id}/sos/accept`, { method: 'PUT', body: JSON.stringify(data) }); },
  createEstimate(id, data) { return this.request(`/orders/${id}/estimate`, { method: 'POST', body: JSON.stringify(data) }); },
  acceptEstimate(id) { return this.request(`/orders/${id}/estimate/accept`, { method: 'PUT' }); },
  getOrderMessages(id) { return this.request(`/orders/${id}/messages`); },
  sendMessage(id, data) { return this.request(`/orders/${id}/messages`, { method: 'POST', body: JSON.stringify(data) }); },
  uploadFile(file) {
    const fd = new FormData();
    fd.append('file', file);
    return this.request('/uploads/', { method: 'POST', body: fd });
  },

  // Academy
  createCourse(data) { return this.request('/courses/', { method: 'POST', body: JSON.stringify(data) }); },
  getCourses() { return this.request('/courses/'); },
  getCourseDetails(id) { return this.request(`/courses/${id}`); },
  addLesson(courseId, data) { return this.request(`/courses/${courseId}/lessons`, { method: 'POST', body: JSON.stringify(data) }); },
  
  // Market
  getMaterials() { return this.request('/market/materials'); },
  createMaterialRequest(data) { return this.request('/market/requests', { method: 'POST', body: JSON.stringify(data) }); },
  getMyMaterialRequests() { return this.request('/market/requests/me'); },

  // Sadaqa
  createDonation(data) { return this.request('/sadaqa/donations', { method: 'POST', body: JSON.stringify(data) }); },
  getTotalDonations() { return this.request('/sadaqa/total'); },

  // Suppliers (Do'konlar)
  getSupplierProducts(q = '', cat = '') {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (cat) params.set('category', cat);
    return this.request(`/suppliers/products?${params}`);
  },
  getSupplierFeed() { return this.request('/suppliers/feed'); },
  createSupplierProduct(data) { return this.request('/suppliers/products', { method: 'POST', body: JSON.stringify(data) }); },
  getMySupplierProducts() { return this.request('/suppliers/products/me'); },
  updateSupplierProduct(id, data) { return this.request(`/suppliers/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }); },
  deleteSupplierProduct(id) { return this.request(`/suppliers/products/${id}`, { method: 'DELETE' }); },
  getSupplierReviews(supplierId) { return this.request(`/suppliers/${supplierId}/reviews`); },
  createSupplierReview(supplierId, data) { return this.request(`/suppliers/${supplierId}/reviews`, { method: 'POST', body: JSON.stringify(data) }); },
  getTopSuppliers() { return this.request('/suppliers/top'); },

  // Auth
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let msg = err.detail || 'Kirishda xatolik';
        if (Array.isArray(err.detail)) msg = err.detail.map(e => e.msg).join(', ');
        else if (typeof err.detail === 'object') msg = JSON.stringify(err.detail);
        throw new Error(msg);
    }
    
    const data = await res.json();
    localStorage.setItem('baraka_token', data.access_token);
    const user = await this.request('/users/me');
    localStorage.setItem('baraka_user', JSON.stringify(user));
    return { access_token: data.access_token, user: user };
  },

  // ==================== YANGI FUNKSIYALAR ====================

  // Dashboard
  getDashboard() { return this._authGet('/dashboard'); },

  // Bildirishnomalar
  getNotifications() { return this._authGet('/notifications'); },
  getUnreadCount() { return this._authGet('/notifications/unread-count'); },
  markAllRead() { return this._authReq('/notifications/read-all', 'PUT'); },

  // Sertifikatlar
  issueCertificate(courseId) { return this._authReq(`/certificates/${courseId}`, 'POST'); },
  getMyCertificates() { return this._authGet('/certificates/me'); },

  // Kalendar
  getSchedule(userId, month, year) {
    let url = `/schedule/${userId}`;
    if (month && year) url += `?month=${month}&year=${year}`;
    return this._get(url);
  },
  addScheduleSlot(data) { return this._authReq('/schedule', 'POST', data); },
  deleteScheduleSlot(id) { return this._authReq(`/schedule/${id}`, 'DELETE'); },

  // Qidiruv va tavsiyalar
  searchMasters(q, sort, minRating) {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (sort) params.set('sort', sort);
    if (minRating) params.set('min_rating', minRating);
    return this._get(`/search/masters?${params}`);
  },
  getNearbyMasters(lat, lng, radius) {
    return this._get(`/nearby-masters?lat=${lat}&lng=${lng}&radius=${radius || 10}`);
  },
  getRecommendations(q, lat, lng) {
    let url = `/recommend?q=${encodeURIComponent(q)}`;
    if (lat && lng) url += `&lat=${lat}&lng=${lng}`;
    return this._get(url);
  },

  // Fayl yuklash
  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('baraka_token')}` },
      body: formData
    });
    if (!res.ok) throw new Error('Rasm yuklashda xatolik');
    return await res.json();
  },

  // AI Chat
  aiChat(history, new_message) {
    const user = getAuthUser();
    return fetch(`${API_BASE}/ai-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        history, 
        new_message, 
        user_name: user ? user.full_name : null 
      })
    }).then(r => r.json());
  },

  // Helper methods
  _get(path) { return fetch(`${API_BASE}${path}`).then(r => r.json()); },
  _authGet(path) {
    return fetch(`${API_BASE}${path}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('baraka_token')}` }
    }).then(r => r.json());
  },
  _authReq(path, method, body) {
    const opts = {
      method,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('baraka_token')}`,
        'Content-Type': 'application/json',
      },
    };
    if (body) opts.body = JSON.stringify(body);
    return fetch(`${API_BASE}${path}`, opts).then(r => r.json());
  },
};


// ==================== Toast Notifications ====================

function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `${type === 'success' ? '✅' : '⚠️'} ${message}`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3500);
}


// ==================== Global Auth ====================

function getAuthUser() {
  try {
    const user = localStorage.getItem('baraka_user');
    if (!user || user === 'undefined') return null;
    return JSON.parse(user);
  } catch(e) {
    localStorage.removeItem('baraka_user');
    localStorage.removeItem('baraka_token');
    return null;
  }
}

function logout() {
  localStorage.removeItem('baraka_user');
  localStorage.removeItem('baraka_token');
  window.location.href = '/';
}

function initNavbar() {
  const user = getAuthUser();
  const navLinks = document.getElementById('navLinks');
  if (!navLinks) return;

  // Har bir rol uchun ko'rinadigan sahifalar
  const ROLE_NAV = {
    // Mehmon (tizimga kirmagan)
    GUEST: [
      { href: '/', label: 'Bosh sahifa' },
      { href: '/masters', label: 'Ustalar' },
      { href: '/guilds', label: 'Kasabalar' },
      { href: '/academy', label: 'Akademiya' },
      { href: '/shogird', label: 'Ustoz-Shogird' },
      { href: '/market', label: 'Bozor' },
      { href: '/suppliers', label: "Do'konlar" },
      { href: '/orders', label: 'Buyurtmalar' },
    ],
    // Mijoz — buyurtma berish, usta qidirish
    MIJOZ: [
      { href: '/', label: 'Bosh sahifa' },
      { href: '/masters', label: 'Ustalar' },
      { href: '/orders', label: 'Buyurtmalar' },
      { href: '/guilds', label: 'Kasabalar' },
      { href: '/shogird', label: 'Ustoz-Shogird' },
    ],
    // Usta — buyurtmalar, profil, akademiya, shogird, bozor, gildiya
    USTA: [
      { href: '/', label: 'Bosh sahifa' },
      { href: '/orders', label: 'Buyurtmalar' },
      { href: '/guilds', label: 'Kasabalar' },
      { href: '/academy', label: 'Akademiya' },
      { href: '/shogird', label: 'Ustoz-Shogird' },
      { href: '/market', label: 'Bozor' },
      { href: '/suppliers', label: "Do'konlar" },
      { href: '/dashboard', label: 'Dashboard' },
    ],
    // Shogird — akademiyadan o'rganish, ustozi
    SHOGIRD: [
      { href: '/', label: 'Bosh sahifa' },
      { href: '/academy', label: 'Akademiya' },
      { href: '/shogird', label: 'Ustoz-Shogird' },
      { href: '/orders', label: 'Buyurtmalar' },
      { href: '/dashboard', label: 'Dashboard' },
    ],
    // Do'kondor — mahsulot boshqaruvi, do'konlar sahifasi
    DOKONDOR: [
      { href: '/', label: 'Bosh sahifa' },
      { href: '/suppliers', label: "Do'konlar" },
      { href: '/masters', label: 'Ustalar' },
      { href: '/dashboard', label: 'Dashboard' },
    ],
    // Admin — hammasi
    ADMIN: [
      { href: '/', label: 'Bosh sahifa' },
      { href: '/masters', label: 'Ustalar' },
      { href: '/guilds', label: 'Kasabalar' },
      { href: '/academy', label: 'Akademiya' },
      { href: '/shogird', label: 'Ustoz-Shogird' },
      { href: '/duolar', label: 'Duolar' },
      { href: '/market', label: 'Bozor' },
      { href: '/suppliers', label: "Do'konlar" },
      { href: '/orders', label: 'Buyurtmalar' },
      { href: '/dashboard', label: 'Dashboard' },
    ],
  };

  const role = user ? (user.role || 'MIJOZ') : 'GUEST';
  const links = ROLE_NAV[role] || ROLE_NAV.GUEST;
  const currentPath = window.location.pathname;

  let html = links.map(l =>
    `<li><a href="${l.href}" ${l.href === currentPath ? 'class="active"' : ''}>${l.label}</a></li>`
  ).join('\n');

  if (user) {
    // Add notification bell and profile
    html += `
      <li>
        <div style="display:flex;align-items:center;gap:12px; margin-left:8px;">
          ${role !== 'MIJOZ' ? `
          <a href="/dashboard" id="navBellBtn" style="position:relative; font-size:1.2rem; text-decoration:none;" title="Bildirishnomalar">
            🔔<span id="navUnreadBadge" style="display:none; position:absolute; top:-5px; right:-10px; background:red; color:white; border-radius:10px; padding:2px 6px; font-size:0.6rem; font-weight:bold;">0</span>
          </a>` : ''}
          <a href="/profile?id=${user.id}" style="color:var(--brown-800);font-weight:600;">👤 ${user.full_name}</a>
          <span class="badge" style="background:var(--green-100);color:var(--green-800);font-size:0.75rem;">${role}</span>
          <button onclick="logout()" class="btn btn-secondary btn-sm" style="padding:4px 10px;">Chiqish</button>
        </div>
      </li>`;
      
    // Navbar yozilishi shart
    navLinks.innerHTML = html;
      
    // Fetch unread count asynchronously
    setTimeout(() => {
      api.getUnreadCount().then(res => {
        if (res && res.count > 0) {
          const badge = document.getElementById('navUnreadBadge');
          if (badge) {
            badge.textContent = res.count;
            badge.style.display = 'inline-block';
          }
        }
      }).catch(e => console.error(e));
    }, 1000);
  } else {
    html += `<li><a href="/login" class="btn btn-primary btn-sm">Kirish</a></li>`;
  }

  navLinks.innerHTML = html;
}


// ==================== Navbar Scroll ====================

window.addEventListener('scroll', () => {
  const nav = document.querySelector('.navbar');
  if (nav) nav.classList.toggle('scrolled', window.scrollY > 10);
});

// Hamburger menu handled inline in HTML


// ==================== Scroll Animations ====================

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
});


// ==================== Modal Helpers ====================

function openModal(id) {
  document.getElementById(id)?.classList.add('active');
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('active');
}
// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});


// ==================== Rizolik Stars ====================

let selectedRizolik = null;
const RIZOLIK_MAP = {
  1: 'NOROZI',
  2: 'YOMON',
  3: 'QONIQARLI',
  4: 'YAXSHI',
  5: 'AJOYIB',
};
const RIZOLIK_LABELS = {
  1: '😞 Norozi',
  2: '😐 Yomon',
  3: '🤔 Qoniqarli',
  4: '😊 Yaxshi',
  5: '🤩 Ajoyib!',
};

function initRizolikStars() {
  const starsContainer = document.querySelector('.rizolik-stars');
  const label = document.querySelector('.rizolik-label');
  if (!starsContainer) return;

  starsContainer.addEventListener('click', (e) => {
    const star = e.target.closest('.rizolik-star');
    if (!star) return;
    const value = parseInt(star.dataset.value);
    selectedRizolik = value;
    starsContainer.querySelectorAll('.rizolik-star').forEach((s, i) => {
      s.classList.toggle('active', i < value);
    });
    if (label) label.textContent = RIZOLIK_LABELS[value];
  });

  starsContainer.addEventListener('mouseover', (e) => {
    const star = e.target.closest('.rizolik-star');
    if (!star) return;
    const value = parseInt(star.dataset.value);
    starsContainer.querySelectorAll('.rizolik-star').forEach((s, i) => {
      s.style.color = i < value ? '#d4a44a' : '';
    });
  });

  starsContainer.addEventListener('mouseleave', () => {
    starsContainer.querySelectorAll('.rizolik-star').forEach((s, i) => {
      s.style.color = '';
    });
  });
}


// ==================== Auth (Login/Register) ====================

function initAuth() {
  const tabs = document.querySelectorAll('.auth-tab');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      if (tab.dataset.tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
      } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
      }
    });
  });

  // Role selector
  document.querySelectorAll('.role-option').forEach(opt => {
    opt.addEventListener('click', () => {
      document.querySelectorAll('.role-option').forEach(o => o.classList.remove('active'));
      opt.classList.add('active');
    });
  });
}


// ==================== Helpers ====================

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('uz-UZ', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
}

function getRankEmoji(rank) {
  const map = { 'Shogird': '🌱', 'Usta': '🔨', 'Sarusta': '⚜️', 'Pir': '👑' };
  return map[rank] || '🌱';
}
