document.addEventListener("DOMContentLoaded", () => {

    // UI Arrays
    let pendingData = [];
    let labsData = [];
    let bookingsData = [];
    let currentFilter = 'All';

    // DOM Elements
    const pendingGrid = document.getElementById("pending-grid");
    const pendingTitle = document.getElementById("pending-title");
    const labsGrid = document.getElementById("labs-grid");
    const bookingsTbody = document.getElementById("bookings-tbody");
    const bookingFilters = document.getElementById("booking-filters");

    const addModal = document.getElementById("add-modal");
    const denyModal = document.getElementById("deny-modal");
    const denyForm = document.getElementById("deny-form");
    const scheduleModal = document.getElementById("schedule-modal");

    // Initialization Calls
    fetchAll();

    async function fetchAll() {
        await Promise.all([loadLabs(), loadBookings()]);
    }

    // ──────────────────────────────────────────────
    // 1. DATA LOADERS
    // ──────────────────────────────────────────────

    async function loadLabs() {
        try {
            const res = await fetch("/api/admin/labs");
            labsData = await res.json();
            renderLabsGrid();
        } catch (e) {
            labsGrid.innerHTML = `<div class="state-msg">Error loading facilities.</div>`;
        }
    }

    async function loadBookings() {
        try {
            const res = await fetch("/api/admin/labs/bookings");
            bookingsData = await res.json();

            // Derive Pending
            pendingData = bookingsData.filter(b => b.status === 'pending');
            renderPending();
            renderBookingsTable();

        } catch (e) {
            pendingGrid.innerHTML = `<div class="state-msg">Error loading requests.</div>`;
            bookingsTbody.innerHTML = `<tr><td colspan="6" class="state-msg">Error loading history.</td></tr>`;
        }
    }

    // ──────────────────────────────────────────────
    // 2. RENDERERS
    // ──────────────────────────────────────────────

    function renderPending() {
        pendingTitle.innerText = `Pending Booking Requests — ${pendingData.length} Awaiting`;

        if (pendingData.length === 0) {
            pendingGrid.innerHTML = `<div class="state-msg" style="grid-column: 1/-1; padding:10px 0;">No active requests awaiting approval.</div>`;
            return;
        }

        let html = "";
        pendingData.forEach(p => {
            html += `
                <div class="pending-card">
                    <div class="card-left">
                        <div class="card-name">${p.student_name}</div>
                        <div class="card-meta">${p.lab_name} · ${formatDate(p.slot_start)} · ${formatTime(p.slot_start)}–${formatTime(p.slot_end)}</div>
                        <div class="card-meta" style="margin-top:3px; color:#777">Purpose: ${p.purpose}</div>
                    </div>
                    <div class="card-actions">
                        <button class="btn-approve exec-appr" data-id="${p.id}">Approve</button>
                        <button class="btn-deny exec-deny" data-id="${p.id}">Deny</button>
                    </div>
                </div>
            `;
        });
        pendingGrid.innerHTML = html;

        // Bind logic
        document.querySelectorAll('.exec-appr').forEach(btn => {
            btn.addEventListener('click', () => processBookingStatus(btn.getAttribute('data-id'), 'approve'));
        });
        document.querySelectorAll('.exec-deny').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('deny-id').value = btn.getAttribute('data-id');
                document.getElementById('deny-reason').value = '';
                denyModal.classList.add('active');
            });
        });
    }

    function renderLabsGrid() {
        if (labsData.length === 0) {
            labsGrid.innerHTML = `<div class="state-msg" style="grid-column:1/-1; text-align:center;">No lab configurations exist. Add a lab above.</div>`;
            return;
        }

        let html = "";
        labsData.forEach(l => {
            const isAvail = l.current_status === 'available';
            const cls = isAvail ? 'available' : (l.current_status === 'blocked' ? 'blocked' : 'occupied');
            const dotCls = isAvail ? 'green' : (l.current_status === 'blocked' ? 'grey' : 'red');
            const txt = isAvail ? 'Available' : (l.current_status === 'blocked' ? 'Maintenance Block' : `Occupied until ${formatTime(l.available_from)}`);

            html += `
                <div class="lab-card ${cls}">
                    <div class="lab-header">
                        <div>
                            <div class="lab-title">${l.lab_name}</div>
                            <div class="lab-cap">${l.capacity} seats · ${l.category || 'General'}</div>
                        </div>
                        <div class="status-row">
                            <div class="dot ${dotCls}"></div>
                            <span>${txt}</span>
                        </div>
                    </div>
                    
                    <div class="slots-wrap">
                        <div style="font-size:8px; color:#555; text-transform:uppercase;">Today's Slots</div>
                        <div class="slot-row" style="background:transparent; border:1px dashed rgba(255,255,255,0.05); text-align:center; justify-content:center;">
                            No active class bound currently
                        </div>
                    </div>

                    <div class="lab-actions">
                        <button class="btn btn-ghost btn-small exec-sched" style="flex:1" data-id="${l.id}">Schedule</button>
                        <button class="btn btn-ghost btn-small exec-block" style="flex:1; color:${isAvail ? 'var(--text-ghost)' : 'var(--accent)'}" data-id="${l.id}">
                            ${l.current_status === 'blocked' ? 'Unblock' : 'Block'}
                        </button>
                    </div>
                </div>
            `;
        });
        labsGrid.innerHTML = html;

        // Populate modal select
        let selHtml = '<option value="all">-- Select Lab --</option>';
        labsData.forEach(l => selHtml += `<option value="${l.id}">${l.lab_name}</option>`);
        document.getElementById('sched-lab-sel').innerHTML = selHtml;

        // Bind Block actions
        document.querySelectorAll('.exec-block').forEach(b => {
            b.addEventListener('click', async () => {
                const id = b.getAttribute('data-id');
                const orig = b.innerText;
                b.innerText = "...";
                try {
                    await fetch(`/api/admin/labs/${id}/block`, { method: 'PATCH' });
                    loadLabs();
                } catch (e) { b.innerText = orig; }
            });
        });
        // Sched
        document.querySelectorAll('.exec-sched').forEach(b => {
            b.addEventListener('click', async () => {
                const id = b.getAttribute('data-id');
                document.getElementById('sched-lab-sel').value = id;
                generateScheduleMatrix();
                scheduleModal.classList.add('active');
            });
        });
    }

    function renderBookingsTable() {
        let filtered = bookingsData.filter(b => currentFilter === 'All' || b.status === currentFilter.toLowerCase());

        if (filtered.length === 0) {
            bookingsTbody.innerHTML = `<tr><td colspan="6"><div class="state-msg" style="text-align:center; padding:20px;">No bookings match applied filter.</div></td></tr>`;
            return;
        }

        let html = "";
        filtered.forEach(d => {
            const pillCls = `pill-${d.status.toLowerCase()}`;
            html += `
                <tr>
                    <td><div style="font-weight:600; color:var(--cream)">${d.lab_name}</div></td>
                    <td>
                        <div style="color:var(--text-primary)">${d.student_name}</div>
                        <div style="font-size:9px; color:var(--text-ghost)">ID: ${d.student_id}</div>
                    </td>
                    <td>${formatDate(d.slot_start)}</td>
                    <td>
                        <div style="font-size:10px">${formatTime(d.slot_start)} – ${formatTime(d.slot_end)}</div>
                    </td>
                    <td>
                        <div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px;" title="${d.purpose}">${d.purpose}</div>
                    </td>
                    <td><div class="status-pill ${pillCls}">${d.status}</div></td>
                    <td style="text-align:right">
                        ${d.status === 'pending' ? '<button class="link-action" style="color:#555">Awaiting...</button>' : ''}
                        ${d.status === 'approved' ? `<button class="link-action exec-cancel" data-id="${d.id}" style="color:var(--accent)">Cancel</button>` : ''}
                    </td>
                </tr>
            `;
        });
        bookingsTbody.innerHTML = html;

        // Pseudo-cancel logic binds easily back to denial with no reason required in this simplified mockup
    }

    // ──────────────────────────────────────────────
    // 3. ACTION HANDLERS
    // ──────────────────────────────────────────────

    bookingFilters.addEventListener("click", (e) => {
        if (e.target.classList.contains("filter-pill")) {
            document.querySelectorAll("#booking-filters .filter-pill").forEach(p => p.classList.remove("active"));
            e.target.classList.add("active");
            currentFilter = e.target.getAttribute("data-cat");
            renderBookingsTable();
        }
    });

    document.getElementById('add-lab-btn').addEventListener('click', () => {
        document.getElementById('add-form').reset();
        addModal.classList.add('active');
    });

    document.getElementById('view-schedule-btn').addEventListener('click', () => {
        document.getElementById('sched-lab-sel').value = 'all';
        generateScheduleMatrix();
        scheduleModal.classList.add('active');
    });

    async function processBookingStatus(id, action, reason = null) {
        try {
            const body = reason ? JSON.stringify({ reason }) : null;
            const headers = reason ? { "Content-Type": "application/json" } : {};

            const res = await fetch(`/api/admin/labs/bookings/${id}/${action}`, {
                method: 'PATCH', headers, body
            });
            const data = await res.json();
            if (data.success) {
                loadBookings();
                if (action === 'approve') loadLabs(); // State might change
            } else alert("Action failed.");
        } catch (e) { alert("Network error"); }
    }

    denyForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const id = document.getElementById('deny-id').value;
        const res = document.getElementById('deny-reason').value;
        const btn = document.getElementById('deny-submit-btn');
        btn.innerText = "...";
        processBookingStatus(id, 'deny', res).finally(() => {
            btn.innerText = "Confirm Deny";
            denyModal.classList.remove('active');
        });
    });

    document.getElementById('add-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('add-submit-btn');
        btn.innerText = "...";
        btn.disabled = true;

        const payload = {
            lab_name: document.getElementById('add-name').value,
            room_number: document.getElementById('add-room').value,
            capacity: document.getElementById('add-cap').value,
            category: document.getElementById('add-cat').value,
            equipment: document.getElementById('add-equip').value
        };

        try {
            const res = await fetch("/api/admin/labs", {
                method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                addModal.classList.remove('active');
                loadLabs();
            } else throw new Error();
        } catch (err) {
            alert("Error adding lab.");
        } finally {
            btn.innerText = "Register Lab";
            btn.disabled = false;
        }
    });

    // ──────────────────────────────────────────────
    // 4. MATRIX GENERATOR (SCHEDULE MOCKUP)
    // ──────────────────────────────────────────────
    function generateScheduleMatrix() {
        const grid = document.getElementById('sched-grid');
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const times = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'];

        let html = `<div class="sg-header" style="background:transparentborder:none;"></div>`;
        days.forEach(d => html += `<div class="sg-header">${d}</div>`);

        times.forEach(t => {
            html += `<div class="sg-time">${t}</div>`;
            days.forEach(d => {
                // Pseudo-randomize visual grid for mockup fidelity since schedule endpoints aren't strictly hydrated
                let cls = 'sg-cell';
                let content = '';
                if (Math.random() > 0.8) {
                    cls += ' occupied';
                    content = 'Project<br>Review';
                } else if (Math.random() > 0.8) {
                    cls += ' class-session';
                    content = 'Batch A<br>Session';
                } else {
                    content = 'Available';
                }

                html += `<div class="${cls}">${content}</div>`;
            });
        });
        grid.innerHTML = html;
    }

    // ──────────────────────────────────────────────
    // 5. UTILS
    // ──────────────────────────────────────────────
    function formatDate(dStr) {
        if (!dStr) return '';
        const d = new Date(dStr);
        if (isNaN(d)) return dStr;
        return `${d.toLocaleString('default', { month: 'short' })} ${d.getDate()}`;
    }

    function formatTime(dStr) {
        if (!dStr) return '';
        const d = new Date(dStr);
        if (isNaN(d)) return dStr;
        const hr = d.getHours().toString().padStart(2, '0');
        const min = d.getMinutes().toString().padStart(2, '0');
        return `${hr}:${min}`;
    }
});
