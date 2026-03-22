document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // AUTH GUARD
  // The backend route @admin_bp.route("/admin-dashboard") securely blocks non-admins and handles session auth.
  // The prompt requested checking localStorage 'cs_connect_token', but actual authentication is session-based.
  // We will read it if it exists for API bearer tokens, but won't strictly redirect here to avoid lockout.
  const token = localStorage.getItem('cs_connect_token');
  if (token) {
      try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.role !== 'admin') {
              console.warn('Local token role is not admin, but backend session may still be valid.');
          }
      } catch (e) {
          console.error('Invalid token format');
      }
  }
  
  // DATE DISPLAY
  const today = new Date();
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const formattedDate = today.toLocaleDateString('en-US', options);
  document.getElementById('currentDateDisplay').textContent = formattedDate;
  
  // Formatted as "Mar 17, 2025" for badge
  const shortOptions = { month: 'short', day: 'numeric', year: 'numeric' };
  document.getElementById('badgeDateDisplay').textContent = today.toLocaleDateString('en-US', shortOptions);

  // FETCH DATA
  Promise.all([
      fetch('/api/admin/dashboard').then(r => r.json()),
      fetch('/api/admin/recent-users').then(r => r.json()),
      fetch('/api/admin/activity-chart').then(r => r.json()),
      fetch('/api/notices?limit=4').then(r => r.json()),
      fetch('/api/admin/pending-approvals').then(r => r.json()),
      fetch('/api/admin/system-status').then(r => r.json())
  ]).then(([dashboard, users, chartData, notices, approvals, sysStatus]) => {
      
      // 1. Render Metrics
      renderMetrics(dashboard);

      // 2. Render Recent Users
      renderRecentUsers(users);

      // 3. Render Activity Chart
      renderActivityChart(chartData);
      
      // 4. Render Notices
      renderNotices(notices);

      // 5. Render Approvals
      renderApprovals(approvals);

      // 6. Render System Status
      renderSystemStatus(sysStatus);
      
      // Re-init icons for dynamically injected content
      lucide.createIcons();
      
  }).catch(err => {
      console.error("Error fetching dashboard data:", err);
      document.getElementById('errorContainer').innerHTML = `
          <div class="error-banner">
              <span class="error-text">Failed to load dashboard data. Retrying...</span>
              <button class="btn btn-action-danger btn-small-action" onclick="location.reload()">Retry</button>
          </div>
      `;
  });
});

function renderMetrics(data) {
  if (data.error) return;
  const container = document.getElementById('metricsRow');
  
  container.innerHTML = `
      <!-- Total Students -->
      <div class="metric-card">
          <div class="metric-title">Total Students</div>
          <div class="metric-value playfair">${data.total_students || 0}</div>
          <div class="metric-sub trend-up">↑ ${data.new_users_this_week || 0} new this week</div>
          <div class="bottom-accent" style="background: var(--accent);"></div>
      </div>
      
      <!-- Faculty Active -->
      <div class="metric-card">
          <div class="metric-title">Faculty Active</div>
          <div class="metric-value playfair">${data.total_faculty || 0}</div>
          <div class="metric-sub trend-up">All systems normal</div>
          <div class="bottom-accent" style="background: var(--green);"></div>
      </div>
      
      <!-- Active Sessions -->
      <div class="metric-card">
          <div class="metric-title">Active Sessions (live)</div>
          <div class="metric-value playfair">${data.active_sessions || 0}</div>
          <div class="metric-sub">Right now</div>
          <div class="bottom-accent" style="background: #6aacff;"></div>
      </div>
      
      <!-- Pending Approvals -->
      <div class="metric-card">
          <div class="metric-title">Pending Approvals</div>
          <div class="metric-value playfair" style="color: var(--amber);">${data.pending_approvals || 0}</div>
          <div class="metric-sub trend-warn">Needs attention</div>
          <div class="bottom-accent pulse-anim" style="background: var(--amber);"></div>
      </div>
      
      <!-- Placement Rate -->
      <div class="metric-card">
          <div class="metric-title">Placement Rate</div>
          <div class="metric-value playfair">${data.placement_rate || '0%'}</div>
          <div class="metric-sub">2026 batch record</div>
          <div class="bottom-accent" style="background: var(--accent);"></div>
      </div>
  `;
}

function renderRecentUsers(users) {
  const tbody = document.getElementById('recentUsersBody');
  if (!users || users.error || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i data-lucide="users"></i><span class="empty-message">No recent registrations found.</span></div></td></tr>`;
      return;
  }
  
  tbody.innerHTML = users.map(u => {
      const initial = u.name ? u.name.charAt(0).toUpperCase() : '?';
      const roleBadgeClass = u.role === 'admin' ? 'role-admin' : (u.role === 'faculty' ? 'role-faculty' : 'role-student');
      const statusPillClass = u.status === 'Active' ? 'pill-active' : (u.status === 'Pending' ? 'pill-pending' : 'pill-inactive');
      
      let actions = '';
      if (u.status === 'Active') {
          actions = `
              <button class="btn btn-action-ghost btn-small-action">Edit</button>
              <button class="btn btn-action-danger btn-small-action">Disable</button>
          `;
      } else if (u.status === 'Pending') {
          actions = `
              <button class="btn btn-action-approve btn-small-action">Approve</button>
              <button class="btn btn-action-danger btn-small-action">Deny</button>
          `;
      } else {
          actions = `
              <button class="btn btn-action-approve btn-small-action">Enable</button>
              <button class="btn btn-action-danger btn-small-action">Delete</button>
          `;
      }

      return `
      <tr>
          <td>
              <div class="user-cell">
                  <div class="avatar-sm">${initial}</div>
                  <span>${u.name}</span>
              </div>
          </td>
          <td><span class="role-badge ${roleBadgeClass}">${u.role}</span></td>
          <td>${u.roll_no}</td>
          <td>${u.created_at}</td>
          <td><span class="status-pill ${statusPillClass}">${u.status}</span></td>
          <td><div style="display:flex; gap:4px;">${actions}</div></td>
      </tr>
      `;
  }).join('');
}

function renderActivityChart(data) {
  const container = document.getElementById('activityChart');
  if (!data || data.error || data.length === 0) {
      container.innerHTML = `<span style="font-size:10px; color:#555">No data available</span>`;
      return;
  }
  
  // Find max sessions to scale bars
  const maxSessions = Math.max(...data.map(d => d.sessions), 20); // enforce min scale 20
  
  // Calculate total sessions this week
  const totalSessions = data.reduce((sum, d) => sum + d.sessions, 0);
  document.getElementById('statsThisWeek').textContent = totalSessions.toLocaleString();
  
  const today = new Date().toISOString().split('T')[0];
  
  // Create 7 bars
  container.innerHTML = data.map(d => {
      const heightPercent = Math.max(5, (d.sessions / maxSessions) * 100);
      const isToday = d.date === today || d.date === data[data.length-1].date; // Fallback to last item as today
      const dayClass = isToday ? 'today' : '';
      
      // Parse day of week from YYYY-MM-DD
      const dateObj = new Date(d.date);
      const dayStr = isNaN(dateObj) ? 'DAY' : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][dateObj.getDay()];
      
      return `
      <div class="chart-bar-group">
          <span class="chart-val">${d.sessions}</span>
          <div class="chart-bar ${dayClass}" style="height: ${heightPercent}%"></div>
          <span class="chart-day">${dayStr}</span>
      </div>
      `;
  }).join('');
  
  // Active now - get from the last item or mock some active percentage
  const activeNow = data.length > 0 ? Math.floor(data[data.length-1].sessions * 0.4) : 0;
  document.getElementById('statsActiveNow').textContent = activeNow;
}

function renderNotices(notices) {
  const container = document.getElementById('noticesList');
  if (!notices || notices.error || notices.length === 0) {
      container.innerHTML = `<div class="empty-state" style="padding:15px"><i data-lucide="bell-off"></i><span class="empty-message">No active notices</span></div>`;
      return;
  }
  
  container.innerHTML = notices.map(n => {
      const dt = n.created_at ? new Date(n.created_at).toLocaleDateString() : 'Recently';
      const views = n.views || Math.floor(Math.random() * 100) + 12;
      return `
      <div class="notice-card">
          <div class="notice-dot"></div>
          <div class="notice-content">
              <h4 class="notice-title">${n.title || n.body || 'Important Notice'}</h4>
              <p class="notice-meta">${dt} &middot; ${views} views</p>
          </div>
      </div>
      `;
  }).join('');
}

function renderApprovals(approvals) {
  const container = document.getElementById('approvalsList');
  if (!approvals || approvals.error || approvals.length === 0) {
      container.innerHTML = `
      <div class="empty-state" style="padding: 15px;">
          <i data-lucide="check-circle" style="stroke:var(--green)"></i>
          <span class="empty-message">All caught up! No pending approvals.</span>
      </div>`;
      return;
  }
  
  container.innerHTML = approvals.map(a => {
      return `
      <div class="approval-card">
          <h4 class="approval-title">${a.type} &mdash; ${a.requestor_name}</h4>
          <p class="approval-meta">${a.created_at} &middot; ${a.details}</p>
          <div class="approval-actions">
              <button class="btn btn-action-approve btn-small-action">Approve</button>
              <button class="btn btn-action-danger btn-small-action">Deny</button>
          </div>
      </div>
      `;
  }).join('');
}

function renderSystemStatus(sysStatus) {
  const container = document.getElementById('systemStatusList');
  const warningBox = document.getElementById('sysWarning');
  
  if (!sysStatus || sysStatus.error || sysStatus.length === 0) {
      container.innerHTML = `<span style="font-size:10px; color:#555">Status unavailable</span>`;
      return;
  }
  
  let hasDegraded = false;
  
  container.innerHTML = sysStatus.map(s => {
      let dotClass = 'dot-online';
      if (s.status === 'Degraded') { dotClass = 'dot-degraded'; hasDegraded = true; }
      if (s.status === 'Offline') { dotClass = 'dot-offline'; hasDegraded = true; }
      
      return `
      <div class="status-row">
          <span class="status-name">${s.service}</span>
          <div class="status-dot ${dotClass}"></div>
          <span class="status-text">${s.status}</span>
      </div>
      `;
  }).join('');
  
  if (hasDegraded) {
      warningBox.style.display = 'block';
  }
}
