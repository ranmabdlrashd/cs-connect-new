document.addEventListener("DOMContentLoaded", () => {

    // UI Elements
    const composeForm = document.getElementById("compose-form");
    const composeBtn = document.getElementById("compose-btn");
    const drivesTbody = document.getElementById("drives-tbody");
    const driveFilters = document.getElementById("drive-filters");

    // Modals
    const editModal = document.getElementById("edit-modal");
    const editForm = document.getElementById("edit-form");
    const editCancel = document.getElementById("edit-cancel");

    const closeModal = document.getElementById("close-modal");
    const closeCancel = document.getElementById("close-cancel");
    const closeConfirmBtn = document.getElementById("close-confirm-btn");
    const closeTargetTitle = document.getElementById("close-target-title");

    let drivesData = [];
    let closeIdTarget = null;
    let currentFilter = 'All';

    // Init
    loadDrives();
    loadStats();

    // Event Bindings
    driveFilters.addEventListener("click", (e) => {
        if (e.target.classList.contains("filter-pill")) {
            document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
            e.target.classList.add("active");
            currentFilter = e.target.getAttribute("data-cat");
            renderDrivesList();
        }
    });

    composeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const original = composeBtn.innerHTML;
        composeBtn.innerHTML = "Adding...";
        composeBtn.disabled = true;

        // Gather branches
        const branchCheckboxes = document.querySelectorAll('#compose-branches input:checked');
        const branches = Array.from(branchCheckboxes).map(cb => cb.value).join(',');

        const payload = {
            company_name: document.getElementById("compose-company").value,
            role: document.getElementById("compose-role").value,
            package_min: document.getElementById("compose-pmin").value,
            package_max: document.getElementById("compose-pmax").value,
            min_cgpa: document.getElementById("compose-cgpa").value,
            branches: branches,
            batch_year: document.getElementById("compose-batch").value,
            drive_date: document.getElementById("compose-rdate").value,
            aptitude_date: document.getElementById("compose-adate").value,
            venue: document.getElementById("compose-venue").value,
            description: document.getElementById("compose-desc").value,
            status: document.getElementById("compose-status").value,
            deadline: document.getElementById("compose-deadline").value,
            website: document.getElementById("compose-link").value
        };

        try {
            const res = await fetch("/api/admin/placements/drives", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                composeForm.reset();
                await loadDrives();
                loadStats();
                composeBtn.innerHTML = "Success!";
                setTimeout(() => composeBtn.innerHTML = original, 2000);
            } else {
                throw new Error(data.error);
            }
        } catch (err) {
            alert("Error adding Drive.");
            composeBtn.innerHTML = original;
        } finally {
            composeBtn.disabled = false;
        }
    });

    editCancel.addEventListener("click", () => editModal.classList.remove("active"));

    editForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("edit-id").value;
        const btn = document.getElementById("edit-save-btn");
        const original = btn.innerHTML;
        btn.innerHTML = "Saving...";
        btn.disabled = true;

        const payload = {
            role: document.getElementById("edit-role").value,
            status: document.getElementById("edit-status").value,
        };

        try {
            const res = await fetch(`/api/admin/placements/drives/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                editModal.classList.remove("active");
                loadDrives();
                loadStats();
            } else throw new Error();
        } catch (err) {
            alert("Failed to update.");
        } finally {
            btn.innerHTML = original;
            btn.disabled = false;
        }
    });

    closeCancel.addEventListener("click", () => closeModal.classList.remove("active"));

    closeConfirmBtn.addEventListener("click", async () => {
        if (!closeIdTarget) return;
        const btn = closeConfirmBtn;
        btn.innerHTML = "Closing...";
        try {
            const res = await fetch(`/api/admin/placements/drives/${closeIdTarget}/close`, { method: "PATCH" });
            const data = await res.json();
            if (data.success) {
                closeModal.classList.remove("active");
                loadDrives();
                loadStats();
            }
        } catch (e) {
            alert("Error closing drive");
        } finally {
            btn.innerHTML = "Close Drive";
        }
    });

    // Fetches
    async function loadDrives() {
        try {
            const res = await fetch("/api/admin/placements/drives");
            if (!res.ok) throw new Error();
            drivesData = await res.json();

            if (drivesData.length === 0 && !drivesData.error) {
                drivesTbody.innerHTML = `<tr><td colspan="6"><div class="state-box"><svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg><div class="state-msg">No placement drives structured.</div></div></td></tr>`;
                return;
            }
            if (drivesData.error) throw new Error();
            renderDrivesList();
        } catch (e) {
            drivesTbody.innerHTML = `<tr><td colspan="6"><div class="state-box error"><div class="state-msg">Failed to load drives.</div></div></td></tr>`;
        }
    }

    function renderDrivesList() {
        let html = "";
        let filtered = drivesData.filter(d => currentFilter === 'All' || d.status === currentFilter);

        if (filtered.length === 0) {
            drivesTbody.innerHTML = `<tr><td colspan="6"><div class="state-msg" style="padding:15px;text-align:center;">No drives match filter.</div></td></tr>`;
            return;
        }

        filtered.forEach(d => {
            let statusPillClass = `pill-${d.status.toLowerCase()}`;
            if (!['open', 'upcoming', 'closed'].includes(d.status.toLowerCase())) statusPillClass = 'pill-closed';

            // Format package string
            let packStr = `₹${d.package_min}L`;
            if (d.package_max && d.package_max > d.package_min) packStr += ` - ₹${d.package_max}L`;

            let actionHtml = '';
            if (d.status !== 'Closed') {
                actionHtml = `
                    <button class="link-action exec-edit" data-id="${d.id}">Edit</button>
                    <button class="link-action exec-close" data-id="${d.id}" data-title="${d.company_name}">Close</button>
                    <a href="/admin-dashboard/placements/${d.id}/applicants" class="link-action" style="color:#6aacff">Applicants→</a>
                `;
            } else {
                actionHtml = `
                    <a href="/admin-dashboard/placements/${d.id}/applicants" class="link-action" style="color:var(--cream)">View Results→</a>
                    <button class="link-action" style="color:var(--accent)">Archive</button>
                `;
            }

            html += `
                <tr>
                    <td style="color:var(--cream);font-weight:600;">${d.company_name}</td>
                    <td>
                        <div style="font-weight:500;color:var(--text-primary)">${d.role}</div>
                        <div style="font-size:9px;color:var(--text-dim);margin-top:2px;">${packStr}</div>
                    </td>
                    <td>
                        <div>Min CGPA: ${d.min_cgpa}</div>
                        <div style="font-size:9px;color:var(--text-dim);margin-top:2px;">${d.branches || 'All'}</div>
                    </td>
                    <td>
                        <div>Drive: ${formatDate(d.drive_date)}</div>
                        <div style="font-size:9px;color:var(--text-dim);margin-top:2px;">Exp: ${formatDate(d.deadline)}</div>
                    </td>
                    <td>
                        <div class="status-pill ${statusPillClass}">${d.status}</div>
                        <div style="font-size:9px;color:var(--text-ghost);margin-top:4px;">${d.applicant_count} applied</div>
                    </td>
                    <td style="text-align:right">
                        <div class="table-actions" style="justify-content: flex-end;">${actionHtml}</div>
                    </td>
                </tr>
            `;
        });
        drivesTbody.innerHTML = html;

        // BIND ACTIONS
        document.querySelectorAll('.exec-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = btn.getAttribute('data-id');
                const dr = drivesData.find(x => x.id == id);
                if (dr) {
                    document.getElementById("edit-id").value = dr.id;
                    document.getElementById("edit-role").value = dr.role;
                    document.getElementById("edit-status").value = dr.status;
                    editModal.classList.add("active");
                }
            });
        });

        document.querySelectorAll('.exec-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                closeIdTarget = btn.getAttribute('data-id');
                closeTargetTitle.innerText = btn.getAttribute('data-title');
                closeModal.classList.add("active");
            });
        });
    }

    async function loadStats() {
        try {
            const res = await fetch("/api/admin/placements/stats");
            let data = await res.json();

            if (!data || data.error || Object.keys(data).length === 0) {
                // Fallback mock math if no data tables exist yet
                document.getElementById('stat-total').innerText = "0";
                document.getElementById('stat-high').innerText = "₹0L";
                document.getElementById('stat-avg').innerText = "₹0L";
                document.getElementById('stat-active').innerText = "0";
                document.getElementById('bar-chart').innerHTML = `<div class="state-msg" style="width:100%;text-align:center;">Not enough data for analytics.</div>`;
                return;
            }

            document.getElementById('stat-total').innerText = data.total_placed || "0";
            document.getElementById('stat-high').innerText = `₹${data.highest_package || 0}L`;
            document.getElementById('stat-avg').innerText = `₹${data.avg_package || 0}L`;
            document.getElementById('stat-active').innerText = data.active_drives || "0";

            // Draw Bar Chart purely via CSS math if stats exist
            if (data.chart_data && data.chart_data.length > 0) {
                const maxVal = Math.max(...data.chart_data.map(d => d.value));
                let chartHtml = "";
                data.chart_data.forEach(d => {
                    const pct = maxVal > 0 ? (d.value / maxVal) * 100 : 0;
                    chartHtml += `
                        <div class="chart-bar" style="height:${pct}%" title="${d.company}: ${d.value} offers">
                            <div class="chart-val">${d.value}</div>
                            <div class="chart-label">${d.company}</div>
                        </div>
                    `;
                });
                document.getElementById('bar-chart').innerHTML = chartHtml;
            } else {
                document.getElementById('bar-chart').innerHTML = `<div class="state-msg" style="width:100%;text-align:center;">Awaiting drive completions.</div>`;
            }
        } catch (e) {
            console.error("Stats fail");
        }
    }

    function formatDate(dStr) {
        if (!dStr) return '';
        const d = new Date(dStr);
        if (isNaN(d)) return dStr;
        const month = d.toLocaleString('default', { month: 'short' });
        const day = d.getDate();
        const yr = d.getFullYear();
        return `${month} ${day}, ${yr}`;
    }

});
