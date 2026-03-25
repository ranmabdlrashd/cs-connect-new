document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();

  // DATE DISPLAY
  const today = new Date();
  const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  document.getElementById('currentDateDisplay').textContent = today.toLocaleDateString('en-US', opts);
  document.getElementById('badgeDateDisplay').textContent = today.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  // Fetch all dashboard data in parallel
  loadDashboard();

  // Export Report
  document.getElementById('exportBtn')?.addEventListener('click', () => {
    window.location.href = '/api/admin/users/export';
  });

  // Add Notice button opens modal
  document.getElementById('addNoticeBtn')?.addEventListener('click', () => {
    openNoticeModal();
  });
});

function loadDashboard() {
  Promise.all([
    fetch('/api/admin/dashboard').then(r => r.json()),
    fetch('/api/admin/recent-users').then(r => r.json()),
    fetch('/api/admin/activity-chart').then(r => r.json()),
    fetch('/api/notices?limit=4').then(r => r.json()),
    fetch('/api/admin/pending-approvals').then(r => r.json()),
    fetch('/api/admin/system-status').then(r => r.json()),
    fetch('/api/admin/library-requests').then(r => r.json()).catch(() => [])
  ]).then(([dashboard, users, chartData, notices, approvals, sysStatus, libRequests]) => {
    renderMetrics(dashboard);
    renderRecentUsers(users);
    renderActivityChart(chartData);
    renderNotices(notices);
    renderApprovals(approvals, libRequests);
    renderSystemStatus(sysStatus);
    lucide.createIcons();
  }).catch(err => {
    console.error("Error fetching dashboard data:", err);
    document.getElementById('errorContainer').innerHTML = `
      <div class="error-banner">
        <span class="error-text">Failed to load dashboard data.</span>
        <button class="btn btn-action-danger btn-small-action" onclick="loadDashboard()">Retry</button>
      </div>`;
  });
}

function renderMetrics(data) {
  if (data.error) return;
  const container = document.getElementById('metricsRow');
  container.innerHTML = `
    <div class="metric-card">
      <div class="metric-title">Total Students</div>
      <div class="metric-value playfair">${data.total_students || 0}</div>
      <div class="metric-sub trend-up">↑ ${data.new_users_this_week || 0} new this week</div>
      <div class="bottom-accent" style="background:var(--accent)"></div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Faculty Active</div>
      <div class="metric-value playfair">${data.total_faculty || 0}</div>
      <div class="metric-sub trend-up">All systems normal</div>
      <div class="bottom-accent" style="background:var(--green)"></div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Active Sessions (live)</div>
      <div class="metric-value playfair">${data.active_sessions || 0}</div>
      <div class="metric-sub">Right now</div>
      <div class="bottom-accent" style="background:#6aacff"></div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Pending Approvals</div>
      <a href="/admin/library" style="text-decoration:none">
        <div class="metric-value playfair" style="color:var(--amber)">${data.pending_approvals || 0}</div>
      </a>
      <div class="metric-sub trend-warn">Needs attention</div>
      <div class="bottom-accent pulse-anim" style="background:var(--amber)"></div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Placement Rate</div>
      <div class="metric-value playfair">${data.placement_rate || '0%'}</div>
      <div class="metric-sub">2026 batch record</div>
      <div class="bottom-accent" style="background:var(--accent)"></div>
    </div>`;
}

function renderRecentUsers(users) {
  const tbody = document.getElementById('recentUsersBody');
  if (!users || users.error || users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i data-lucide="users"></i><span class="empty-message">No recent registrations found.</span></div></td></tr>`;
    return;
  }
  tbody.innerHTML = users.map(u => {
    const initial = (u.name || '?').charAt(0).toUpperCase();
    const roleBadge = u.role === 'admin' ? 'role-admin' : (u.role === 'faculty' ? 'role-faculty' : 'role-student');
    const statusPill = u.status === 'Active' ? 'pill-active' : (u.status === 'Pending' ? 'pill-pending' : 'pill-inactive');
    let actions = '';
    if (u.status === 'Active') {
      actions = `<button class="btn btn-action-ghost btn-small-action" onclick="editUser(${u.id})">Edit</button>
                 <button class="btn btn-action-danger btn-small-action" onclick="setUserStatus(${u.id},'Inactive',this)">Disable</button>`;
    } else if (u.status === 'Pending') {
      actions = `<button class="btn btn-action-approve btn-small-action" onclick="setUserStatus(${u.id},'Active',this)">Approve</button>
                 <button class="btn btn-action-danger btn-small-action" onclick="setUserStatus(${u.id},'Inactive',this)">Deny</button>`;
    } else {
      actions = `<button class="btn btn-action-approve btn-small-action" onclick="setUserStatus(${u.id},'Active',this)">Enable</button>
                 <button class="btn btn-action-danger btn-small-action" onclick="deleteUser(${u.id},this)">Delete</button>`;
    }
    return `<tr id="user-row-${u.id}">
      <td><div class="user-cell"><div class="avatar-sm">${initial}</div><span>${u.name}</span></div></td>
      <td><span class="role-badge ${roleBadge}">${u.role}</span></td>
      <td>${u.roll_no || 'N/A'}</td>
      <td>${u.created_at || 'Recently'}</td>
      <td><span class="status-pill ${statusPill}" id="status-${u.id}">${u.status}</span></td>
      <td><div style="display:flex;gap:4px;" id="actions-${u.id}">${actions}</div></td>
    </tr>`;
  }).join('');
}

function setUserStatus(userId, newStatus, btn) {
  btn.disabled = true;
  btn.textContent = '...';
  fetch(`/api/admin/users/${userId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: newStatus })
  }).then(r => r.json()).then(data => {
    if (data.success) {
      showToast(`User ${newStatus === 'Active' ? 'approved' : 'disabled'} successfully.`, 'success');
      // Update row in-place
      const statusEl = document.getElementById(`status-${userId}`);
      if (statusEl) {
        statusEl.textContent = newStatus;
        statusEl.className = `status-pill ${newStatus === 'Active' ? 'pill-active' : 'pill-inactive'}`;
      }
      const actionsEl = document.getElementById(`actions-${userId}`);
      if (actionsEl && newStatus === 'Active') {
        actionsEl.innerHTML = `<button class="btn btn-action-ghost btn-small-action" onclick="editUser(${userId})">Edit</button>
                               <button class="btn btn-action-danger btn-small-action" onclick="setUserStatus(${userId},'Inactive',this)">Disable</button>`;
      } else if (actionsEl) {
        actionsEl.innerHTML = `<button class="btn btn-action-approve btn-small-action" onclick="setUserStatus(${userId},'Active',this)">Enable</button>`;
      }
    } else {
      showToast('Failed to update user.', 'error');
      btn.disabled = false;
      btn.textContent = newStatus === 'Active' ? 'Approve' : 'Disable';
    }
  }).catch(() => {
    showToast('Network error.', 'error');
    btn.disabled = false;
  });
}

function deleteUser(userId, btn) {
  if (!confirm('Are you sure you want to delete this user? This cannot be undone.')) return;
  fetch(`/api/admin/users/${userId}`, { method: 'DELETE' })
    .then(r => r.json()).then(d => {
      if (d.success) {
        document.getElementById(`user-row-${userId}`)?.remove();
        showToast('User deleted.', 'success');
      }
    });
}

function editUser(userId) {
  window.location.href = `/admin-dashboard/users#user-${userId}`;
}

function renderActivityChart(data) {
  const container = document.getElementById('activityChart');
  if (!data || data.error || data.length === 0) {
    container.innerHTML = `<span style="font-size:10px;color:#555">No data available</span>`;
    return;
  }
  const maxSessions = Math.max(...data.map(d => d.sessions), 20);
  const totalSessions = data.reduce((sum, d) => sum + d.sessions, 0);
  document.getElementById('statsThisWeek').textContent = totalSessions.toLocaleString();
  const todayStr = new Date().toISOString().split('T')[0];
  container.innerHTML = data.map(d => {
    const h = Math.max(5, (d.sessions / maxSessions) * 100);
    const dayStr = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][new Date(d.date).getDay()] || '--';
    const isToday = d.date === todayStr;
    return `<div class="chart-bar-group">
      <span class="chart-val">${d.sessions}</span>
      <div class="chart-bar ${isToday ? 'today' : ''}" style="height:${h}%"></div>
      <span class="chart-day">${dayStr}</span>
    </div>`;
  }).join('');
  const activeNow = data.length > 0 ? Math.floor(data[data.length - 1].sessions * 0.4) : 0;
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
    return `<div class="notice-card">
      <div class="notice-dot"></div>
      <div class="notice-content">
        <h4 class="notice-title">${n.title || n.body || 'Important Notice'}</h4>
        <p class="notice-meta">${dt} &middot; ${n.views || 0} views</p>
      </div>
    </div>`;
  }).join('');

  // Wire quick notice form
  const form = document.querySelector('.quick-notice-form');
  if (form && !form.dataset.wired) {
    form.dataset.wired = 'true';
    form.querySelector('button').addEventListener('click', () => {
      const input = form.querySelector('input');
      const title = input.value.trim();
      if (!title) return;
      fetch('/api/admin/notices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body: title, category: 'Academic' })
      }).then(r => r.json()).then(d => {
        if (d.success) {
          showToast('Notice posted!', 'success');
          input.value = '';
          fetch('/api/notices?limit=4').then(r => r.json()).then(renderNotices);
        } else {
          showToast('Failed to post notice.', 'error');
        }
      });
    });
  }
}

function renderApprovals(approvals, libRequests) {
  const container = document.getElementById('approvalsList');

  // Merge library requests into approvals list
  const libItems = (libRequests || []).map(r => ({
    id: r.id,
    type: `Library ${(r.request_type || 'Issue').charAt(0).toUpperCase() + (r.request_type || 'issue').slice(1)} Request`,
    requestor_name: r.user_name,
    details: `Book: ${r.book_title}`,
    created_at: r.request_date ? new Date(r.request_date).toLocaleDateString() : 'Today',
    is_library_request: true,
    request_type: r.request_type
  }));

  const allApprovals = [...(approvals.filter ? approvals.filter(a => !a.error) : []), ...libItems];

  if (allApprovals.length === 0) {
    container.innerHTML = `<div class="empty-state" style="padding:15px"><i data-lucide="check-circle" style="stroke:var(--green)"></i><span class="empty-message">All caught up! No pending approvals.</span></div>`;
    return;
  }

  // Link to review all
  const reviewAll = container.closest('.card')?.querySelector('.panel-action');
  if (reviewAll) reviewAll.href = '/admin/library';

  container.innerHTML = allApprovals.slice(0, 5).map(a => {
    const approveAction = a.is_library_request
      ? `onclick="approveLibraryRequest(${a.id}, this)"`
      : `onclick="approveApproval(${a.id}, this)"`;
    const denyAction = a.is_library_request
      ? `onclick="rejectLibraryRequest(${a.id}, this)"`
      : `onclick="denyApproval(${a.id}, this)"`;
    return `<div class="approval-card" id="approval-${a.id}">
      <h4 class="approval-title">${a.type} &mdash; ${a.requestor_name}</h4>
      <p class="approval-meta">${a.created_at} &middot; ${a.details}</p>
      <div class="approval-actions">
        <button class="btn btn-action-approve btn-small-action" ${approveAction}>Approve</button>
        <button class="btn btn-action-danger btn-small-action" ${denyAction}>Deny</button>
      </div>
    </div>`;
  }).join('');
}

function approveLibraryRequest(requestId, btn) {
  btn.disabled = true;
  fetch(`/admin/approve_request/${requestId}`, { method: 'POST' })
    .then(r => { 
      if (r.ok || r.redirected) {
        document.getElementById(`approval-${requestId}`)?.remove();
        showToast('Library request approved!', 'success');
      }
    }).catch(() => showToast('Failed to approve.', 'error'));
}

function rejectLibraryRequest(requestId, btn) {
  btn.disabled = true;
  const fd = new FormData();
  fd.append('feedback', 'Rejected by Admin');
  fetch(`/admin/reject_request/${requestId}`, { method: 'POST', body: fd })
    .then(r => {
      if (r.ok || r.redirected) {
        document.getElementById(`approval-${requestId}`)?.remove();
        showToast('Request rejected.', 'success');
      }
    }).catch(() => showToast('Failed to reject.', 'error'));
}

function approveApproval(id, btn) {
  btn.disabled = true;
  fetch(`/api/admin/approvals/${id}/approve`, { method: 'PATCH' })
    .then(r => r.json()).then(d => {
      if (d.success) { document.getElementById(`approval-${id}`)?.remove(); showToast('Approved!', 'success'); }
    });
}

function denyApproval(id, btn) {
  btn.disabled = true;
  fetch(`/api/admin/approvals/${id}/deny`, { method: 'PATCH' })
    .then(r => r.json()).then(d => {
      if (d.success) { document.getElementById(`approval-${id}`)?.remove(); showToast('Denied.', 'success'); }
    });
}

function renderSystemStatus(sysStatus) {
  const container = document.getElementById('systemStatusList');
  const warningBox = document.getElementById('sysWarning');
  if (!sysStatus || sysStatus.error || sysStatus.length === 0) {
    container.innerHTML = `<span style="font-size:10px;color:#555">Status unavailable</span>`;
    return;
  }
  let hasDegraded = false;
  container.innerHTML = sysStatus.map(s => {
    let dotClass = 'dot-online';
    if (s.status === 'Degraded') { dotClass = 'dot-degraded'; hasDegraded = true; }
    if (s.status === 'Offline') { dotClass = 'dot-offline'; hasDegraded = true; }
    return `<div class="status-row">
      <span class="status-name">${s.service}</span>
      <div class="status-dot ${dotClass}"></div>
      <span class="status-text">${s.status}</span>
    </div>`;
  }).join('');
  if (hasDegraded) warningBox.style.display = 'block';
}

function openNoticeModal() {
  // Simple prompt approach as modal isn't in the template
  const title = prompt('Enter notice title:');
  if (!title) return;
  const body = prompt('Enter notice body (optional):', title);
  fetch('/api/admin/notices', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, body: body || title, category: 'Academic' })
  }).then(r => r.json()).then(d => {
    if (d.success) {
      showToast('Notice posted successfully!', 'success');
      fetch('/api/notices?limit=4').then(r => r.json()).then(renderNotices);
    } else {
      showToast('Failed to post notice.', 'error');
    }
  });
}

function showToast(msg, type = 'success') {
  let toast = document.getElementById('adminToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'adminToast';
    toast.style.cssText = `
      position:fixed; bottom:24px; right:24px; z-index:9999;
      padding:12px 20px; border-radius:8px; font-size:14px; font-weight:500;
      box-shadow:0 4px 16px rgba(0,0,0,0.3); transition:all 0.3s ease;
      display:flex; align-items:center; gap:8px; min-width:220px;
    `;
    document.body.appendChild(toast);
  }
  toast.style.background = type === 'success' ? '#14532d' : '#7f1d1d';
  toast.style.color = type === 'success' ? '#86efac' : '#fca5a5';
  toast.style.border = `1px solid ${type === 'success' ? '#166534' : '#991b1b'}`;
  toast.innerHTML = `<span>${type === 'success' ? '✓' : '✗'}</span> ${msg}`;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
  }, 3500);
}
