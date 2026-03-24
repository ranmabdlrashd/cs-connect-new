document.addEventListener("DOMContentLoaded", () => {

    // UI Elements
    const composeForm = document.getElementById("compose-form");
    const composeBtn = document.getElementById("compose-btn");
    const subjTbody = document.getElementById("subj-tbody");
    const facList = document.getElementById("fac-list");
    const totalCreditsEl = document.getElementById("total-credits");
    const listTitle = document.getElementById("list-title");
    const composeSemSelect = document.getElementById("compose-sem");

    // Modals
    const editModal = document.getElementById("edit-modal");
    const editForm = document.getElementById("edit-form");
    const editCancel = document.getElementById("edit-cancel");

    const delModal = document.getElementById("del-modal");
    const delCancel = document.getElementById("del-cancel");
    const delConfirmBtn = document.getElementById("del-confirm-btn");
    const delTargetTitle = document.getElementById("del-target-title");
    const delTargetSem = document.getElementById("del-target-sem");

    let activeSem = 'S6';
    let subjectsData = [];
    let facultyOptionsHtml = '<option value="">-- Unassigned --</option>';
    let delIdTarget = null;

    // Init Sequence
    initSequence();

    async function initSequence() {
        await loadFacultyDict();
        // pre-populate global selects
        document.querySelectorAll('.global-fac-select').forEach(sel => sel.innerHTML = facultyOptionsHtml);

        loadSemesterData();
    }

    // Event Bindings for Tabs
    document.getElementById("sem-tabs").addEventListener("click", (e) => {
        if (e.target.classList.contains("sem-tab")) {
            document.querySelectorAll(".sem-tab").forEach(p => p.classList.remove("active"));
            e.target.classList.add("active");
            activeSem = e.target.getAttribute("data-sem");
            composeSemSelect.value = activeSem;
            loadSemesterData();
        }
    });

    composeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const original = composeBtn.innerHTML;
        composeBtn.innerHTML = "Adding...";
        composeBtn.disabled = true;

        const payload = {
            subject_name: document.getElementById("compose-name").value,
            subject_code: document.getElementById("compose-code").value,
            semester: document.getElementById("compose-sem").value,
            credits: document.getElementById("compose-credits").value,
            hours_per_week: document.getElementById("compose-hours").value,
            subject_type: document.getElementById("compose-type").value,
            faculty_id: document.getElementById("compose-faculty").value,
            exam_type: document.getElementById("compose-exam").value,
            description: document.getElementById("compose-desc").value
        };

        try {
            const res = await fetch("/api/admin/courses/subjects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                composeForm.reset();
                composeSemSelect.value = activeSem; // Restore active mapping
                await loadSemesterData(); // Overkill if sem didn't match, but reliable
                composeBtn.innerHTML = "Success!";
                setTimeout(() => composeBtn.innerHTML = original, 2000);
            } else {
                throw new Error(data.error);
            }
        } catch (err) {
            alert("Error adding subject.");
            composeBtn.innerHTML = original;
        } finally {
            composeBtn.disabled = false;
        }
    });

    // Fetches
    async function loadFacultyDict() {
        try {
            const res = await fetch("/api/admin/users/faculty-list");
            if (res.ok) {
                const arr = await res.json();
                arr.forEach(f => {
                    facultyOptionsHtml += `<option value="${f.id}">${f.name} (${f.department})</option>`;
                });
            }
        } catch (e) { console.error("Could not load faculty dict"); }
    }

    async function loadSemesterData() {
        listTitle.innerText = `Semester ${activeSem} Subjects`;
        subjTbody.innerHTML = `<tr><td colspan="5"><div class="skeleton" style="height:30px"></div></td></tr>`;
        facList.innerHTML = `<div class="skeleton" style="height:40px; margin: 10px;"></div>`;
        totalCreditsEl.innerText = "0";

        try {
            const res = await fetch(`/api/admin/courses/subjects?semester=${activeSem}`);
            if (!res.ok) throw new Error();
            subjectsData = await res.json();

            if (subjectsData.length === 0 && !subjectsData.error) {
                subjTbody.innerHTML = `<tr><td colspan="5"><div class="state-box"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg><div class="state-msg">No subjects mapped to ${activeSem}.</div></div></td></tr>`;
                facList.innerHTML = `<div class="state-msg" style="padding:15px; text-align:center;">No subjects to assign.</div>`;
                return;
            }
            if (subjectsData.error) throw new Error();
            renderData();
        } catch (e) {
            subjTbody.innerHTML = `<tr><td colspan="5"><div class="state-box error"><div class="state-msg">Failed to load payload.</div></div></td></tr>`;
            facList.innerHTML = "";
        }
    }

    function renderData() {
        let html = "";
        let facHtml = "";
        let totalCr = 0;

        subjectsData.forEach(d => {
            let typeCls = d.subject_type.toLowerCase();
            if (typeCls === 'lab/practical') typeCls = 'lab';
            const badgeCls = `type-${typeCls}`;

            totalCr += parseInt(d.credits || 0);

            html += `
                <tr>
                    <td>
                        <div>${d.subject_name}</div>
                        <div style="font-size:10px;color:var(--text-ghost);margin-top:2px;font-family:monospace">${d.subject_code}</div>
                    </td>
                    <td>
                        <div class="type-badge ${badgeCls}">${d.subject_type}</div>
                    </td>
                    <td>
                        <div style="color:${d.faculty_name ? 'var(--text-primary)' : 'var(--text-dead)'}">${d.faculty_name || 'Unassigned'}</div>
                    </td>
                    <td>
                        <div>${d.credits} Cr</div>
                        <div style="font-size:9px;color:var(--text-ghost);margin-top:2px;">${d.hours_per_week} hrs/wk</div>
                    </td>
                    <td style="text-align:right">
                        <div class="table-actions" style="justify-content: flex-end;">
                            <button class="link-action exec-edit" data-id="${d.id}">Edit</button>
                            <button class="link-action exec-del" data-id="${d.id}" data-title="${d.subject_name}" style="color:var(--accent)">Remove</button>
                        </div>
                    </td>
                </tr>
            `;

            // Build Reassignment Panel concurrently
            // Create a specific option set pre-selecting the current faculty
            // Note: facultyOptionsHtml contains the base string. We can hijack it via DOMParser or Regex, or just rebuild.
            // Using a hack for simplicity: selecting it via JS after render
            facHtml += `
                <div class="faculty-row">
                    <div class="f-subj">${d.subject_name} <span style="color:var(--text-ghost); font-size:10px;">(${d.subject_code})</span></div>
                    <select class="form-select f-select active-fac-bind" data-id="${d.id}" data-selected="${d.faculty_id || ''}">
                        ${facultyOptionsHtml}
                    </select>
                    <button class="btn btn-ghost btn-small exec-reassign" data-id="${d.id}">Reassign</button>
                </div>
            `;

        });
        subjTbody.innerHTML = html;
        facList.innerHTML = facHtml;
        totalCreditsEl.innerText = totalCr;

        // BIND ACTIONS: Modals
        document.querySelectorAll('.exec-edit').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-id');
                const dr = subjectsData.find(x => x.id == id);
                if (dr) {
                    document.getElementById("edit-id").value = dr.id;
                    document.getElementById("edit-name").value = dr.subject_name;
                    document.getElementById("edit-type").value = dr.subject_type;
                    document.getElementById("edit-credits").value = dr.credits;
                    editModal.classList.add("active");
                }
            });
        });

        document.querySelectorAll('.exec-del').forEach(btn => {
            btn.addEventListener('click', () => {
                delIdTarget = btn.getAttribute('data-id');
                delTargetTitle.innerText = btn.getAttribute('data-title');
                delTargetSem.innerText = `Semester ${activeSem}`;
                delModal.classList.add("active");
            });
        });

        // Pre-select the dropdowns
        document.querySelectorAll('.active-fac-bind').forEach(sel => {
            sel.value = sel.getAttribute('data-selected');
        });

        // BIND Faculty Reassign Action
        document.querySelectorAll('.exec-reassign').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                // find corresponding select
                const selectEl = document.querySelector(`.active-fac-bind[data-id="${id}"]`);
                const facId = selectEl.value;
                const originalText = btn.innerText;

                btn.innerText = "...";
                try {
                    const res = await fetch(`/api/admin/courses/subjects/${id}/faculty`, {
                        method: 'PATCH',
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ faculty_id: facId || null })
                    });
                    const json = await res.json();
                    if (json.success) {
                        btn.innerText = "Done";
                        btn.style.color = "#5c5";
                        setTimeout(() => { btn.innerText = "Reassign"; btn.style.color = ""; }, 2000);
                        // Refresh to sync right list
                        loadSemesterData();
                    } else throw new Error();
                } catch (e) {
                    alert('Reassignment failed');
                    btn.innerText = originalText;
                }
            });
        });
    }

    // Modal Edit Resolvers
    editCancel.addEventListener("click", () => editModal.classList.remove("active"));
    editForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("edit-id").value;
        const btn = document.getElementById("edit-save-btn");
        const original = btn.innerHTML;
        btn.innerHTML = "Saving...";
        btn.disabled = true;

        const payload = {
            subject_name: document.getElementById("edit-name").value,
            subject_type: document.getElementById("edit-type").value,
            credits: document.getElementById("edit-credits").value
        };

        try {
            const res = await fetch(`/api/admin/courses/subjects/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                editModal.classList.remove("active");
                loadSemesterData();
            } else throw new Error();
        } catch (err) { alert("Failed to update."); }
        finally { btn.innerHTML = original; btn.disabled = false; }
    });

    delCancel.addEventListener("click", () => delModal.classList.remove("active"));
    delConfirmBtn.addEventListener("click", async () => {
        if (!delIdTarget) return;
        const btn = delConfirmBtn;
        btn.innerHTML = "Removing...";
        try {
            const res = await fetch(`/api/admin/courses/subjects/${delIdTarget}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                delModal.classList.remove("active");
                loadSemesterData();
            }
        } catch (e) { alert("Error removing subject"); }
        finally { btn.innerHTML = "Confirm Remove"; }
    });

    document.getElementById("export-btn").addEventListener("click", () => {
        alert("JSON Export mapping sequence initiated (Placeholder logic bound).");
    });
});
