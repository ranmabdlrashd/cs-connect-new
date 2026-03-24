document.addEventListener("DOMContentLoaded", () => {

    // Bindings
    const tbody = document.getElementById("app-tbody");
    const checkAll = document.getElementById("check-all");
    const bulkBtns = document.querySelectorAll(".bulk-btn");
    const bulkCountEl = document.getElementById("bulk-count");

    let appsData = [];
    let driveContext = null;

    loadApplicants();

    // 1. Check All listener
    checkAll.addEventListener("change", (e) => {
        const isChecked = e.target.checked;
        document.querySelectorAll(".row-check").forEach(cb => {
            cb.checked = isChecked;
        });
        updateBulkUI();
    });

    // 2. Delegate Row Checkboxes
    tbody.addEventListener("change", (e) => {
        if (e.target.classList.contains("row-check")) {
            updateBulkUI();

            // Uncheck checkAll if one row unchecked
            if (!e.target.checked) checkAll.checked = false;
        }
    });

    // 3. Bulk Action Triggers
    bulkBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const action = btn.getAttribute("data-action");
            const selectedIds = Array.from(document.querySelectorAll(".row-check:checked"))
                .map(cb => cb.value);

            if (selectedIds.length === 0) return;
            processBulk(action, selectedIds, btn);
        });
    });

    function updateBulkUI() {
        const cnt = document.querySelectorAll(".row-check:checked").length;
        bulkCountEl.innerText = cnt;
        bulkBtns.forEach(btn => btn.disabled = cnt === 0);
    }

    async function processBulk(action, ids, btnRef) {
        const originalText = btnRef.innerText;
        btnRef.innerText = "Processing...";
        btnRef.disabled = true;

        try {
            // We loop and run PATCH since the spec specifies individual PATCH routes, 
            // or we could assume a batch route. Since spec explicitly lists:
            // PATCH /api/admin/placements/applications/[id]/[action]
            // We sequentially promise all.

            const promises = ids.map(appId =>
                fetch(`/api/admin/placements/applications/${appId}/${action}`, { method: 'PATCH' })
            );
            await Promise.all(promises);
            await loadApplicants(); // Refresh UI
            checkAll.checked = false;
            updateBulkUI();
        } catch (e) {
            alert("Error running bulk action.");
        } finally {
            btnRef.innerText = originalText;
        }
    }

    // Individual action hook
    tbody.addEventListener("click", async (e) => {
        if (e.target.classList.contains("single-action")) {
            const id = e.target.getAttribute("data-id");
            const action = e.target.getAttribute("data-action");
            const originalText = e.target.innerText;
            e.target.innerText = "...";
            try {
                const res = await fetch(`/api/admin/placements/applications/${id}/${action}`, { method: 'PATCH' });
                const json = await res.json();
                if (json.success) {
                    await loadApplicants();
                } else alert("Failed action");
            } catch (err) {
                e.target.innerText = originalText;
                alert("Error.");
            }
        }
    });

    async function loadApplicants() {
        try {
            // Fetch drive metadata + list of applications
            const res = await fetch(`/api/admin/placements/drives/${DRIVE_ID}/applicants`);
            if (!res.ok) throw new Error();
            const payload = await res.json();

            driveContext = payload.drive;
            appsData = payload.applicants;

            updateHeaderContext();
            renderTable();

        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="6"><div class="state-box error"><div class="state-msg">Failed to load applicant list.</div></div></td></tr>`;
        }
    }

    function updateHeaderContext() {
        if (!driveContext) return;
        document.getElementById("bc-company").innerText = driveContext.company_name;
        document.getElementById("drive-title").innerText = `${driveContext.company_name} - ${driveContext.role}`;

        let pkgStr = `₹${driveContext.package_min}L`;
        if (driveContext.package_max) pkgStr += ` - ₹${driveContext.package_max}L`;
        document.getElementById("drive-sub").innerText = `Package: ${pkgStr} | Drive: ${formatDate(driveContext.drive_date)}`;

        // Stats Map
        let cApp = 0, cShort = 0, cSel = 0;
        appsData.forEach(r => {
            cApp++;
            if (r.status === 'Shortlisted') cShort++;
            if (r.status === 'Selected') cSel++;
        });

        document.getElementById("st-applied").innerText = cApp;
        document.getElementById("st-short").innerText = cShort;
        document.getElementById("st-sel").innerText = cSel;
    }

    function renderTable() {
        if (appsData.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6"><div class="state-box"><svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg><div class="state-msg">No students have applied yet.</div></div></td></tr>`;
            return;
        }

        let html = "";
        appsData.forEach(r => {
            const pillCls = `pill-${r.status.toLowerCase()}`;

            let actions = '';
            if (r.status === 'Applied') {
                actions = `
                    <button class="link-action single-action" data-action="shortlist" data-id="${r.id}" style="color:#6aacff">Shortlist</button>
                    <button class="link-action single-action" data-action="reject" data-id="${r.id}" style="color:var(--accent)">Reject</button>
                `;
            } else if (r.status === 'Shortlisted') {
                actions = `
                    <button class="link-action single-action" data-action="select" data-id="${r.id}" style="color:#5c5">Mark Selected</button>
                    <button class="link-action single-action" data-action="reject" data-id="${r.id}" style="color:var(--accent)">Reject</button>
                `;
            } else {
                actions = `
                    <div style="font-size:9px;color:var(--text-ghost)">Locked</div>
                `;
            }

            const resumeLink = r.resume_url
                ? `<a href="${r.resume_url}" target="_blank" class="link-action" style="font-size:9px;color:var(--text-dim)"><svg viewBox="0 0 24 24" width="10" height="10" style="vertical-align:middle;margin-right:2px;stroke:currentcolor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>Resume</a>`
                : `<span style="font-size:9px;color:var(--text-dead)">No Resume</span>`;

            html += `
                <tr>
                    <td style="padding-left:14px;"><input type="checkbox" class="row-check" value="${r.id}"></td>
                    <td>
                        <div style="font-weight:600;color:var(--cream)">${r.name}</div>
                        <div style="font-size:10px;color:var(--text-dim);margin-top:2px;">${r.roll_no} • ${r.batch}</div>
                    </td>
                    <td>
                        <div style="color:var(--text-primary);font-weight:500;">CGPA: ${r.cgpa || 'N/A'}</div>
                    </td>
                    <td>
                        <div>${formatDate(r.applied_date)}</div>
                        <div style="margin-top:4px;">${resumeLink}</div>
                    </td>
                    <td>
                        <div class="status-pill ${pillCls}">${r.status}</div>
                    </td>
                    <td style="text-align:right">
                        <div class="table-actions" style="justify-content: flex-end;">${actions}</div>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        checkAll.checked = false;
        updateBulkUI();
    }

    function formatDate(dStr) {
        if (!dStr) return '';
        const d = new Date(dStr);
        if (isNaN(d)) return dStr;
        return `${d.toLocaleString('default', { month: 'short' })} ${d.getDate()}, ${d.getFullYear()}`;
    }

});
