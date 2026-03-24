document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    fetchSystemSettings();
    fetchHealthStatus();

    // Bind Save All listener
    document.getElementById('btn-save-all').addEventListener('click', saveGlobalStates);
});

/* =======================================
   TAB ROUTING LOGIC
======================================= */
function initTabs() {
    const navItems = document.querySelectorAll('.st-nav-item[data-target]');
    const panes = document.querySelectorAll('.tab-pane');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            const targetId = item.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });
}

/* =======================================
   ALERT SYSTEM
======================================= */
function showAlert(message, type = "success") {
    const container = document.getElementById('alert-container');
    const colors = {
        'success': { border: 'rgba(58,136,52,0.4)', bg: 'rgba(58,136,52,0.1)', text: 'var(--green)' },
        'error': { border: 'rgba(139,29,29,0.4)', bg: 'rgba(139,29,29,0.1)', text: 'var(--accent)' }
    };
    const c = colors[type] || colors['success'];

    const el = document.createElement('div');
    el.style.cssText = `background:${c.bg};border:1px solid ${c.border};color:${c.text};padding:12px 16px;border-radius:8px;font-size:11px;font-weight:500;display:flex;align-items:center;gap:8px;animation:slideIn 0.3s ease;font-family:'Inter',sans-serif;`;

    const icon = type === 'success'
        ? '<svg style="width:14px;height:14px;flex-shrink:0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
        : '<svg style="width:14px;height:14px;flex-shrink:0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';

    el.innerHTML = `${icon} ${message}`;
    container.appendChild(el);

    setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateX(20px)';
        el.style.transition = 'all 0.3s';
        setTimeout(() => el.remove(), 300);
    }, 4000);
}

// Inject animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes spin { 100% { transform: rotate(360deg); } }
`;
document.head.appendChild(style);

/* =======================================
   API DATA FETCHING
======================================= */
async function fetchSystemSettings() {
    // Hide error banner, show loading state
    document.getElementById('general-error').style.display = 'none';

    try {
        const response = await fetch('/api/admin/settings');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.success) {
            populateGeneral(data.general);
            populateSecurity(data.security);
            populateEmail(data.email);
            populateIntegrations(data.integrations);

            if (data.general.maintenance_mode) {
                document.getElementById('maint-banner-wrap').style.display = 'block';
            }
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (err) {
        console.error("Settings fetch failed:", err);
        document.getElementById('general-error').style.display = 'flex';
        showAlert("Failed to load system settings. Use the Retry button.", "error");
    }
}

function populateGeneral(gen) {
    document.getElementById('gen_pname').value = gen.portal_name || '';
    document.getElementById('gen_inst').value = gen.institution || '';
    document.getElementById('gen_dept').value = gen.department || 'CSE';
    document.getElementById('gen_acad').value = gen.academic_year || '';
    document.getElementById('gen_scheme').value = gen.scheme || '';
    document.getElementById('gen_version').value = gen.version || 'v1.4.2-stable';

    // Remove loading placeholders
    document.querySelectorAll('#form-general .form-control').forEach(el => {
        el.placeholder = '';
    });

    // Feature toggles
    document.getElementById('feat_reg').checked = gen.features?.registration ?? false;
    document.getElementById('feat_lib').checked = gen.features?.library ?? false;
    document.getElementById('feat_ai').checked = gen.features?.chatbot ?? false;
    document.getElementById('feat_lab').checked = gen.features?.labs ?? false;
    document.getElementById('feat_place').checked = gen.features?.placements ?? false;
    document.getElementById('feat_fee').checked = gen.features?.fees ?? false;
    document.getElementById('feat_maint').checked = gen.maintenance_mode ?? false;
}

function populateSecurity(sec) {
    document.getElementById('sec_plen').value = sec.min_password_len;
    document.getElementById('sec_pexp').value = sec.password_expiry_days;
    document.getElementById('sec_uc').checked = sec.require_uppercase;
    document.getElementById('sec_num').checked = sec.require_numbers;
    document.getElementById('sec_spc').checked = sec.require_special;

    document.getElementById('sec_jwt').value = sec.jwt_expiry;
    document.getElementById('sec_conc').value = sec.max_concurrent;
    document.getElementById('sec_fout').checked = sec.force_logout_on_pwd_change;
    document.getElementById('sec_ipres').checked = sec.restrict_ips;
    document.getElementById('sec_iplist').value = (sec.allowed_ips || []).join('\n');
}

function populateEmail(eml) {
    document.getElementById('eml_host').value = eml.host || '';
    document.getElementById('eml_port').value = eml.port || '';
    document.getElementById('eml_user').value = eml.username || '';

    // Remove loading placeholders
    document.querySelectorAll('#pane-email .form-control').forEach(el => {
        if (el.placeholder === 'Loading...') el.placeholder = '';
    });
}

function populateIntegrations(intg) {
    if (!intg) return;
    const gcid = document.getElementById('int_gcid');
    const gcsec = document.getElementById('int_gcsec');
    const rzp = document.getElementById('int_rzpkey');

    if (gcid) { gcid.value = intg.google_client_id || ''; gcid.placeholder = ''; }
    if (gcsec) { gcsec.value = intg.google_client_secret || ''; gcsec.placeholder = ''; }
    if (rzp) { rzp.value = intg.razorpay_key || ''; rzp.placeholder = ''; }
}

/* =======================================
   SYSTEM HEALTH FETCHING
======================================= */
async function fetchHealthStatus() {
    const grid = document.getElementById('health-grid-matrix');
    const diagBody = document.getElementById('diag-log-body');
    const auditBody = document.getElementById('audit-log-body');

    try {
        const [healthRes, logRes] = await Promise.all([
            fetch('/api/admin/system/health'),
            fetch('/api/admin/system/logs')
        ]);

        if (!healthRes.ok || !logRes.ok) throw new Error('API returned error');

        const health = await healthRes.json();
        const logs = await logRes.json();

        // 1. Health grid
        if (health.services && health.services.length > 0) {
            grid.innerHTML = health.services.map(srv => {
                let col = srv.status === 'operational' ? '' : (srv.status === 'degraded' ? 'amber' : 'red');
                return `<div class="health-node">
                    <div class="hn-top">
                        <span class="hn-name"><div class="hn-dot ${col}"></div> ${srv.name}</span>
                        <span style="font-size:9px; color:#555">UPTIME</span>
                    </div>
                    <div class="hn-val">${srv.uptime}%</div>
                </div>`;
            }).join('');
        } else {
            grid.innerHTML = `<div class="empty-state" style="grid-column:span 3">
                <svg viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                <div class="empty-title">No services registered</div>
                <div>System health data is currently unavailable.</div>
            </div>`;
        }

        // 2. Performance metrics
        if (health.metrics) {
            document.getElementById('pm_db').textContent = `${health.metrics.db_latency_ms} ms`;
            document.getElementById('pm_api').textContent = `${health.metrics.api_latency_ms} ms`;
            document.getElementById('pm_conn').textContent = health.metrics.active_connections;

            let perc = (health.metrics.storage_used_gb / health.metrics.storage_total_gb) * 100;
            document.getElementById('pm_vol').textContent = `${health.metrics.storage_used_gb} GB / ${health.metrics.storage_total_gb} GB`;
            document.getElementById('pm_vol_fill').style.width = `${perc}%`;
        }

        // 3. Diagnostic logs
        if (Array.isArray(logs) && logs.length > 0) {
            diagBody.innerHTML = logs.map(l => {
                let pc = l.level === 'ERROR' ? 'error' : (l.level === 'WARN' ? 'warning' : 'info');
                return `<tr>
                    <td>${l.timestamp}</td>
                    <td><span class="log-pill ${pc}">${l.level}</span></td>
                    <td>${l.message}</td>
                    <td>${l.service}</td>
                </tr>`;
            }).join('');
        } else {
            diagBody.innerHTML = `<tr><td colspan="4"><div class="empty-state">
                <svg viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <div class="empty-title">No diagnostic logs</div>
                <div>System is running without recorded events.</div>
            </div></td></tr>`;
        }

        // 4. Audit log
        if (Array.isArray(logs) && logs.length > 0) {
            auditBody.innerHTML = logs.slice(0, 5).map(l => {
                return `<tr>
                    <td style="color:#C0A88A">System Admin</td>
                    <td>Executed configuration change on '${l.service}'.</td>
                    <td>${l.timestamp}</td>
                    <td style="font-family:monospace; font-size:10px">192.168.1.104</td>
                </tr>`;
            }).join('');
        } else {
            auditBody.innerHTML = `<tr><td colspan="4"><div class="empty-state">
                <svg viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                <div class="empty-title">No audit records</div>
                <div>No admin actions have been recorded yet.</div>
            </div></td></tr>`;
        }

    } catch (err) {
        console.error("Health fetch failed:", err);
        grid.innerHTML = `<div class="error-banner" style="grid-column:span 3">
            <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:var(--accent);fill:none" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            <span>Failed to load system health data.</span>
            <button class="btn btn-ghost" style="font-size:9px;padding:3px 9px;margin-left:auto" onclick="fetchHealthStatus()">Retry</button>
        </div>`;
        diagBody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--accent);font-size:11px;padding:16px">
            Failed to load logs. <a href="javascript:fetchHealthStatus()" style="color:var(--amber);text-decoration:underline;margin-left:4px">Retry</a>
        </td></tr>`;
        auditBody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--accent);font-size:11px;padding:16px">
            Failed to load audit data. <a href="javascript:fetchHealthStatus()" style="color:var(--amber);text-decoration:underline;margin-left:4px">Retry</a>
        </td></tr>`;
    }
}

/* =======================================
   SAVE HANDLERS
======================================= */
async function saveGlobalStates() {
    const btn = document.getElementById('btn-save-all');
    btn.disabled = true;
    btn.innerHTML = `<svg style="animation:spin 1s linear infinite;width:14px;height:14px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> Saving...`;

    const payload = {
        general: {
            portal_name: document.getElementById('gen_pname').value,
            institution: document.getElementById('gen_inst').value,
            academic_year: document.getElementById('gen_acad').value,
            scheme: document.getElementById('gen_scheme').value,
            maintenance_mode: document.getElementById('feat_maint').checked,
            features: {
                registration: document.getElementById('feat_reg').checked,
                library: document.getElementById('feat_lib').checked,
                chatbot: document.getElementById('feat_ai').checked,
                labs: document.getElementById('feat_lab').checked,
                placements: document.getElementById('feat_place').checked,
                fees: document.getElementById('feat_fee').checked
            }
        }
    };

    try {
        const res = await fetch('/api/admin/settings/general', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const resp = await res.json();

        if (resp.success) {
            showAlert("System configurations saved successfully.");
            document.getElementById('maint-banner-wrap').style.display = payload.general.maintenance_mode ? 'block' : 'none';
        } else throw new Error(resp.error);
    } catch (err) {
        showAlert(err.message || "Failed to save settings.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg viewBox="0 0 24 24" style="width:14px;height:14px" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg> Save All Changes`;
    }
}

async function testEmail() {
    showAlert("Testing SMTP connection...");
    try {
        const res = await fetch('/api/admin/settings/test-email', { method: 'POST' });
        const obj = await res.json();
        if (obj.success) showAlert(`SMTP test passed: ${obj.message}`);
        else showAlert(`SMTP test failed: ${obj.error}`, "error");
    } catch (err) {
        showAlert("SMTP connection test failed.", "error");
    }
}

async function runBackup() {
    showAlert("Initiating database backup...");
    try {
        const res = await fetch('/api/admin/system/backup', { method: 'POST' });
        const d = await res.json();
        if (d.success) {
            showAlert(`Backup completed successfully. Size: ${d.size_mb} MB`);
            const dt = new Date().toISOString().replace('T', ' ').substring(0, 19);
            document.getElementById('bk-last').textContent = `${dt} · ${d.size_mb} MB`;
            document.getElementById('backup-log-body').insertAdjacentHTML('afterbegin',
                `<tr><td>${dt.split(' ')[0]}</td><td>${d.size_mb} MB</td><td><span class="log-pill info">Completed</span></td><td><a href="#" style="color:var(--amber)">Download ZIP</a></td></tr>`
            );
        } else showAlert("Backup failed.", "error");
    } catch (err) {
        showAlert("Backup request failed.", "error");
    }
}

/* =======================================
   MODAL CONTROLS
======================================= */
function showModal(id) {
    document.getElementById(id).style.display = 'flex';
}
function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

async function executeRestart() {
    const btn = document.getElementById('btn-exec-restart');
    btn.disabled = true;
    btn.innerHTML = 'Restarting...';
    try {
        const res = await fetch('/api/admin/system/restart', { method: 'POST' });
        const d = await res.json();
        if (d.success) {
            closeModal('restart-modal');
            showAlert("Services restarted successfully. Connections may drop briefly.");
        }
    } catch (err) {
        showAlert("Server restart failed.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = "Yes, Restart Completely";
    }
}
