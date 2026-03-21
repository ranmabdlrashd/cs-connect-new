  lucide.createIcons();

  // Tab Switching
  function switchTab(tabId, el) {
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.left-nav-item').forEach(i => i.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    el.classList.add('active');
  }

  // Profile Data
  let currentUser = {};

  async function loadProfile() {
    try {
      const res = await fetch('/api/student/profile');
      if(res.ok) {
        currentUser = await res.json();
        renderProfile();
      } else {
        showErrorBanner();
      }
    } catch(e) {
      showErrorBanner();
    }
  }

  function renderProfile() {
    if(!currentUser.name) return;
    document.getElementById('prof-name').textContent = currentUser.name;
    document.getElementById('prof-batch').textContent = currentUser.batch || 'AISAT Student';
    
    // Initials
    const parts = currentUser.name.split(' ');
    const init = parts.length > 1 ? parts[0][0] + parts[parts.length-1][0] : currentUser.name.substring(0,2);
    document.getElementById('prof-initials').textContent = init.toUpperCase();

    document.getElementById('val-name').innerHTML = `<span>${currentUser.name}</span>`;
    document.getElementById('val-email').innerHTML = `<span>${currentUser.email}</span>`;
    document.getElementById('val-phone').innerHTML = `<span>${currentUser.phone || 'Not set'}</span>`;
    document.getElementById('val-roll').innerHTML = `<span>${currentUser.user_id}</span>`;
    document.getElementById('val-batch-row').innerHTML = `<span>${currentUser.batch || 'N/A'}</span>`;
  }

  function editField(field) {
    const valContainer = document.getElementById(`val-${field}`);
    const currentVal = currentUser[field] || '';
    valContainer.innerHTML = `
      <div style="display:flex; gap:8px;">
        <input type="text" id="input-${field}" class="inline-input" value="${currentVal}" />
        <button class="btn btn-primary" style="padding:4px 10px; font-size:12px;" onclick="saveField('${field}')">Save</button>
        <button class="btn btn-ghost" style="padding:4px 10px; font-size:12px;" onclick="renderProfile()">Cancel</button>
      </div>
    `;
    document.getElementById(`input-${field}`).focus();
  }

  async function saveField(field) {
    const newVal = document.getElementById(`input-${field}`).value;
    try {
      const res = await fetch('/api/student/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: newVal })
      });
      if(res.ok) {
        currentUser[field] = newVal;
        renderProfile();
      } else {
        alert("Failed to update " + field);
      }
    } catch (e) {
      alert("Error updating " + field);
    }
  }

  // Notifications Data
  const NOTIF_FIELDS = {
    'attendance_alerts': 'Attendance alerts (below 80%)',
    'assignment_alerts': 'Assignment due date reminders',
    'library_alerts': 'Library due date alerts',
    'placement_alerts': 'Placement drive notifications',
    'department_notices': 'Department notices',
    'exam_alerts': 'Exam schedule alerts'
  };

  async function loadNotifications() {
    try {
      const res = await fetch('/api/student/notification-preferences');
      if(res.ok) {
        const prefs = await res.json();
        renderNotifications(prefs);
      }
    } catch(e) {
      console.error("Failed to load notifications", e);
    }
  }

  function renderNotifications(prefs) {
    let html = '';
    for(const [key, label] of Object.entries(NOTIF_FIELDS)) {
      const isOn = prefs[key] === true;
      html += `
        <div class="toggle-row">
          <div class="toggle-label">${label}</div>
          <div class="toggle-switch ${isOn ? 'on' : ''}" onclick="toggleNotif('${key}', this)">
            <div class="toggle-thumb"></div>
          </div>
        </div>
      `;
    }
    document.getElementById('notif-card').innerHTML = html;
  }

  async function toggleNotif(key, el) {
    const isOn = el.classList.contains('on');
    const newState = !isOn;
    
    // Optimistic UI update
    if(newState) el.classList.add('on');
    else el.classList.remove('on');

    try {
      const res = await fetch('/api/student/notification-preferences', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: newState })
      });
      if(!res.ok) throw new Error();
    } catch(e) {
      // Revert if failed
      if(isOn) el.classList.add('on');
      else el.classList.remove('on');
    }
  }

  // Security functions
  function checkStrength() {
    const val = document.getElementById('new-pwd').value;
    const fill = document.getElementById('pwd-fill');
    let strength = 0;
    if(val.length > 5) strength += 33;
    if(val.length > 8 && /[A-Z]/.test(val)) strength += 33;
    if(val.length > 8 && /[0-9!@#]/.test(val)) strength += 34;
    
    fill.style.width = strength + '%';
    if(strength <= 33) fill.style.background = 'var(--red)';
    else if(strength <= 66) fill.style.background = 'var(--amber)';
    else fill.style.background = 'var(--green)';
  }

  async function changePassword() {
    const cur = document.getElementById('cur-pwd').value;
    const newPwd = document.getElementById('new-pwd').value;
    const conf = document.getElementById('conf-pwd').value;
    const msg = document.getElementById('pwd-msg');
    
    if(!cur || !newPwd || !conf) {
      msg.textContent = "Please fill all fields.";
      msg.style.color = 'var(--amber)'; msg.style.display = 'block'; return;
    }
    if(newPwd !== conf) {
      msg.textContent = "New passwords do not match.";
      msg.style.color = 'var(--red)'; msg.style.display = 'block'; return;
    }
    
    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: cur, new_password: newPwd })
      });
      const data = await res.json();
      if(res.ok) {
        msg.textContent = "Password updated successfully.";
        msg.style.color = 'var(--green)'; msg.style.display = 'block';
        document.getElementById('cur-pwd').value = '';
        document.getElementById('new-pwd').value = '';
        document.getElementById('conf-pwd').value = '';
        document.getElementById('pwd-fill').style.width = '0%';
      } else {
        msg.textContent = data.error || "Failed to update.";
        msg.style.color = 'var(--red)'; msg.style.display = 'block';
      }
    } catch(e) {
      msg.textContent = "Network error.";
      msg.style.color = 'var(--red)'; msg.style.display = 'block';
    }
  }

  async function logoutAll() {
    try {
      const res = await fetch('/api/auth/logout-all', { method: 'POST' });
      if(res.ok) {
        localStorage.removeItem('cs_connect_token');
        window.location.href = '/login';
      }
    } catch(e) {
      console.error("Error logging out from all devices", e);
    }
  }

  // Modal
  const logoutModal = document.getElementById('logoutModal');
  function openLogoutModal() { logoutModal.classList.add('active'); }
  function closeLogoutModal() { logoutModal.classList.remove('active'); }
  function confirmLogout() {
    localStorage.removeItem('cs_connect_token');
    window.location.href = '/login'; // Alternatively hit an API logout endpoint
  }
  if (logoutModal) {
    logoutModal.addEventListener('click', (e) => {
      if(e.target === logoutModal) closeLogoutModal();
    });
  }

  function showErrorBanner() {
    const pContainer = document.getElementById('profile-fields');
    if(pContainer) {
      pContainer.innerHTML = `
        <div style="background: rgba(139,29,29,0.1); padding: 16px; border-radius: 8px; color: var(--red); display:flex; justify-content:space-between; align-items:center;">
          API Error fetching data.
          <button class="btn btn-primary" onclick="loadProfile()">Retry</button>
        </div>`;
    }
  }

  // Load Initial Data
  document.addEventListener('DOMContentLoaded', () => {
    loadProfile();
    loadNotifications();
  });

  // Export functions to window for HTML inline event handlers
  window.switchTab = switchTab;
  window.editField = editField;
  window.saveField = saveField;
  window.toggleNotif = toggleNotif;
  window.checkStrength = checkStrength;
  window.changePassword = changePassword;
  window.logoutAll = logoutAll;
  window.openLogoutModal = openLogoutModal;
  window.closeLogoutModal = closeLogoutModal;
  window.confirmLogout = confirmLogout;
