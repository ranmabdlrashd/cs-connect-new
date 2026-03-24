// Formatters
const fmtCurrency = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
const fmtDate = (dStr) => {
    if (!dStr) return '-';
    return new Date(dStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

let currentTab = "S6";
let activeData = [];

document.addEventListener("DOMContentLoaded", () => {

    // Bind Tab Selectors
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentTab = e.target.getAttribute('data-batch');
            document.getElementById("tbl-batch-label").innerText = currentTab;
            fetchTableData();
        });
    });

    // Modals
    document.getElementById("btn-bulk-remind").addEventListener("click", () => showModal("bulk-modal"));

    // Form submits
    document.getElementById("edit-form").addEventListener("submit", handleEditSubmit);
    document.getElementById("waive-form").addEventListener("submit", handleWaiveSubmit);
    document.getElementById("btn-exec-bulk").addEventListener("click", handleBulkReminders);

    // Initial load
    initLoad();
});

function showModal(id) { document.getElementById(id).classList.add("active"); }
function closeModal(id) { document.getElementById(id).classList.remove("active"); }

async function initLoad() {
    // Concurrent fetch logic
    await Promise.all([
        fetchStats(),
        fetchTableData()
    ]);
}

// -------------------------------------------------------------
// STATS AND SIDEBAR (1/3 COL) API MAPPING
// -------------------------------------------------------------
async function fetchStats() {
    try {
        const res = await fetch("/api/admin/fees/stats");
        const data = await res.json();

        // Populate KPIs
        document.getElementById("kpi-total").innerText = fmtCurrency(data.kpi.total_expected);

        document.getElementById("kpi-collected").innerText = fmtCurrency(data.kpi.collected);
        let colPct = data.kpi.total_expected ? Math.round((data.kpi.collected / data.kpi.total_expected) * 100) : 0;
        document.getElementById("kpi-col-sub").innerText = `${colPct}% collected overall`;

        document.getElementById("kpi-pending").innerText = fmtCurrency(data.kpi.pending);
        document.getElementById("kpi-pen-sub").innerText = `${data.kpi.pending_count} students pending`;

        document.getElementById("kpi-overdue").innerText = fmtCurrency(data.kpi.overdue);

        // Sidebar Progress mapping
        let phtml = '';
        if (data.progress && data.progress.length > 0) {
            data.progress.forEach(p => {
                let color = p.pct >= 90 ? 'var(--green)' : p.pct >= 70 ? 'var(--amber)' : 'var(--red)';
                phtml += `
                <div class="prog-item">
                    <div class="prog-header"><span>${p.batch}</span><span>${p.pct}%</span></div>
                    <div class="prog-track"><div class="prog-fill" style="width:${p.pct}%; background:${color}"></div></div>
                </div>`;
            });
        } else {
            phtml = '<div style="font-size:10px; color:#555;">No records configured.</div>';
        }
        document.getElementById("prog-bars-container").innerHTML = phtml;

        // Recent Payments
        let rhtml = '';
        if (data.recent && data.recent.length > 0) {
            data.recent.forEach(r => {
                rhtml += `
                <div class="rec-item">
                    <div>
                        <div class="rec-student">${r.name}</div>
                        <div class="rec-date">${fmtDate(r.paid_date)}</div>
                    </div>
                    <div class="rec-amt">${fmtCurrency(r.paid_amount)}</div>
                </div>`;
            });
        } else {
            rhtml = '<div style="font-size:10px; color:#555;">No recent transactions.</div>';
        }
        document.getElementById("recent-payments-container").innerHTML = rhtml;

        // Update bulk text accurately
        document.getElementById("blk-count").innerText = data.kpi.pending_count + (data.kpi.overdue_count || 0);

    } catch (e) { console.error("Stats Fetch failed", e); }
}

// -------------------------------------------------------------
// TABLE HYDRATION (2/3 COL)
// -------------------------------------------------------------
async function fetchTableData() {
    const tbody = document.getElementById("fee-tbody");
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;">Loading...</td></tr>`;

    try {
        const res = await fetch(`/api/admin/fees?batch=${currentTab}`);
        activeData = await res.json();

        if (!activeData || activeData.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#555;">No explicit records isolated for ${currentTab}.</td></tr>`;
            return;
        }

        let html = '';
        activeData.forEach(row => {

            // Format Amount Cell
            let amtHTML = ``;
            if (row.status === 'partial') {
                amtHTML = `<span style="color:#b85">${fmtCurrency(row.paid_amount)}</span> / <span style="font-size:9px; color:#555">${fmtCurrency(row.amount)}</span>`;
            } else if (row.status === 'paid') {
                amtHTML = `<span style="color:#5c5">${fmtCurrency(row.paid_amount || row.amount)}</span>`;
            } else {
                amtHTML = fmtCurrency(row.amount);
            }

            // Action mappings
            let actBtn = ``;
            if (row.status === 'paid') {
                actBtn = `<a href="#" class="btn-action btn-receipt"><svg viewBox="0 0 24 24" style="width:10px;height:10px"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>Receipt</a>`;
            } else if (row.status === 'partial') {
                actBtn = `<button class="btn-action btn-remind" onclick="singleRemind(${row.id})">Remind</button>`;
            } else {
                actBtn = `<button class="btn-action btn-notice" onclick="singleRemind(${row.id})">Send Notice</button>`;
            }

            html += `
            <tr>
                <td>${row.name}<br><span style="font-size:9px; color:#555">${row.roll_no}</span></td>
                <td>${amtHTML}</td>
                <td>${row.status === 'paid' ? '-' : fmtDate(row.due_date)}</td>
                <td>${row.status === 'paid' || row.status === 'partial' ? fmtDate(row.paid_date) : '-'}</td>
                <td><span class="status-pill ${row.status}">${row.status}</span></td>
                <td>
                    <div class="action-box" style="justify-content:flex-end">
                        ${actBtn}
                        <button class="btn-edit-icon" onclick="openEdit(${row.id})" title="Edit Record"><svg viewBox="0 0 24 24"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg></button>
                    </div>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#8B1D1D;">Error fetching datastreams.</td></tr>`;
    }
}

// -------------------------------------------------------------
// MODAL LOGICS
// -------------------------------------------------------------
function openEdit(id) {
    const rec = activeData.find(x => x.id === id);
    if (!rec) return;

    document.getElementById("edit-id").value = rec.id;
    document.getElementById("edit-name").value = rec.name;
    document.getElementById("edit-sem").value = rec.semester;
    document.getElementById("edit-total").value = rec.amount;

    // Safely structure date bounds
    if (rec.due_date) document.getElementById("edit-due").value = rec.due_date.split('T')[0];
    if (rec.paid_date) document.getElementById("edit-pdate").value = rec.paid_date.split('T')[0];

    // Status mapping locks Overdue cleanly via the auto-calculation
    const selStatus = document.getElementById("edit-status");
    let cStat = rec.status;
    if (cStat === 'overdue') { cStat = 'pending'; } // Manual overrides strictly limit to pending logic unless updated
    selStatus.value = cStat;

    document.getElementById("edit-paid").value = rec.paid_amount || '';
    document.getElementById("edit-receipt").value = rec.receipt_ref || '';

    togglePartialFields();
    showModal("edit-modal");
}

function togglePartialFields() {
    const s = document.getElementById("edit-status").value;
    document.getElementById("grp-paid").style.display = (s === 'partial' || s === 'paid') ? "flex" : "none";
    document.getElementById("grp-date").style.display = (s === 'partial' || s === 'paid') ? "flex" : "none";
    document.getElementById("grp-receipt").style.display = s === 'paid' ? "flex" : "none";

    // Show waiver btn only if genuinely pending/partial
    document.getElementById("btn-pre-waive").style.display = (s === 'paid') ? "none" : "block";
}

async function handleEditSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-save-record");
    btn.innerText = "...";

    const id = document.getElementById("edit-id").value;
    const payload = {
        amount: document.getElementById("edit-total").value,
        due_date: document.getElementById("edit-due").value,
        status: document.getElementById("edit-status").value,
        paid_amount: document.getElementById("edit-paid").value || 0,
        paid_date: document.getElementById("edit-pdate").value || null,
        receipt_ref: document.getElementById("edit-receipt").value || null
    };

    try {
        await fetch(`/api/admin/fees/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        closeModal("edit-modal");
        initLoad(); // Refresh everything
    } catch (err) { alert("Save failed"); }
    btn.innerText = "Save Record";
}

function triggerWaiver() {
    const id = document.getElementById("edit-id").value;
    closeModal("edit-modal");
    document.getElementById("waive-id").value = id;
    document.getElementById("waive-reason").value = "";
    showModal("waive-modal");
}

async function handleWaiveSubmit(e) {
    e.preventDefault();
    const id = document.getElementById("waive-id").value;
    const reason = document.getElementById("waive-reason").value;

    try {
        await fetch(`/api/admin/fees/${id}/waive`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reason })
        });
        closeModal("waive-modal");
        initLoad();
    } catch (err) { alert("Waiver execution failed"); }
}

async function singleRemind(id) {
    try {
        const res = await fetch("/api/admin/fees/send-reminders", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fee_ids: [id] })
        });
        if (res.ok) alert("Notice sent securely.");
    } catch (e) { }
}

async function handleBulkReminders() {
    const btn = document.getElementById("btn-exec-bulk");
    btn.innerText = "Sending...";
    try {
        const res = await fetch("/api/admin/fees/send-reminders", { method: "POST" });
        if (res.ok) {
            closeModal("bulk-modal");
            alert("Reminders broadcasted securely to formal notice table.");
        }
    } catch (e) { alert("Bulk request failed"); }
    btn.innerText = "Send To All";
}
