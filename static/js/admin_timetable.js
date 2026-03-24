// Global Accessors
const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const periods = [
    { id: 1, label: "9-10 AM" },
    { id: 2, label: "10-11 AM" },
    { id: 3, label: "11-12 PM" },
    { id: "LUNCH", label: "LUNCH" },
    { id: 4, label: "1-2 PM" },
    { id: 5, label: "2-3 PM" },
    { id: 6, label: "3-4 PM" },
    { id: 7, label: "4-5 PM" }
];

let currentBatch = "S6 CSE A";
let currentSem = "S6";
let timetableData = [];
let subjectsDict = [];
let facultyDict = [];
let stagingPayload = null; // Holds form data if interrupted by conflict

document.addEventListener("DOMContentLoaded", () => {

    // Bind Batch Selector logic
    const selBatch = document.getElementById("sel-batch");
    const inpSem = document.getElementById("inp-sem");

    selBatch.addEventListener("change", (e) => {
        currentBatch = e.target.value;
        currentSem = currentBatch.split(' ')[0]; // Extract "S6" from "S6 CSE A"
        inpSem.value = currentSem;
        document.getElementById("pub-batch-name").innerText = currentBatch;
        initHydration();
    });

    // Modal Links
    document.getElementById("btn-auto-trigger").addEventListener("click", () => showModal("auto-modal"));
    document.getElementById("btn-publish-trigger").addEventListener("click", () => showModal("publish-modal"));

    // Slot assignment listeners
    document.getElementById("slot-subject").addEventListener("change", (e) => {
        // Auto-select faculty based on subject's default binding
        const subId = e.target.value;
        const subj = subjectsDict.find(s => s.id == subId);
        if (subj && subj.faculty_id) {
            document.getElementById("slot-faculty").value = subj.faculty_id;
        }
    });

    document.getElementById("slot-save-btn").addEventListener("click", handleSlotSaveRequest);
    document.getElementById("conflict-override-btn").addEventListener("click", handleConflictOverride);
    document.getElementById("slot-clear-btn").addEventListener("click", handleSlotClear);
    document.getElementById("auto-submit-btn").addEventListener("click", handleAutoGenerate);
    document.getElementById("publish-submit-btn").addEventListener("click", handlePublish);

    // Initial Hydration
    initHydration();
});

function showModal(id) { document.getElementById(id).classList.add("active"); }
function closeModal(id) { document.getElementById(id).classList.remove("active"); }

// -------------------------------------------------------------
// HYDRATION (API Calls)
// -------------------------------------------------------------
async function initHydration() {
    document.getElementById("tt-grid").innerHTML = `<div class="skeleton" style="height:400px; grid-column:span 6; width:100%;"></div>`;
    try {
        // Load Dictionary dependencies concurrently
        const [facRes, subjRes, ttRes] = await Promise.all([
            fetch("/api/admin/users/faculty-list"),
            fetch(`/api/admin/courses/subjects?semester=${currentSem}`), // From Courses config
            fetch(`/api/admin/timetable?batch=${encodeURIComponent(currentBatch)}`)
        ]);

        facultyDict = await facRes.json();
        subjectsDict = await subjRes.json();
        const ttResp = await ttRes.json();

        timetableData = ttResp.slots || [];
        updateStatusBadge(ttResp.status || 'draft');

        populateFormSelects();
        renderGrid();
    } catch (e) { console.error("Hydration failed"); }
}

function updateStatusBadge(status) {
    const badge = document.getElementById("global-status");
    if (status === 'published') {
        badge.className = "status-badge live";
        badge.innerText = "Published · Live";
    } else {
        badge.className = "status-badge draft";
        badge.innerText = "Draft · Not Published";
    }
}

function populateFormSelects() {
    let facOpts = `<option value="">-- Manual Selection --</option>`;
    facultyDict.forEach(f => facOpts += `<option value="${f.id}">${f.name}</option>`);
    document.getElementById("slot-faculty").innerHTML = facOpts;

    let subOpts = `<option value="">-- Assigned Subject --</option>`;
    subjectsDict.forEach(s => subOpts += `<option value="${s.id}">${s.subject_name} (${s.subject_type})</option>`);
    document.getElementById("slot-subject").innerHTML = subOpts;
}

// -------------------------------------------------------------
// GRID RENDERING
// -------------------------------------------------------------
function renderGrid() {
    const grid = document.getElementById("tt-grid");
    let html = `<div class="tt-corner"></div>`;

    // Header Row
    days.forEach(d => html += `<div class="tt-col-head">${d.substring(0, 3)}</div>`);

    // Period Rows
    periods.forEach(p => {
        if (p.id === "LUNCH") {
            html += `<div class="tt-time-label lunch">12:00<br>1:00</div>`;
            html += `<div class="tt-cell lunch">Lunch Break</div>`;
        } else {
            html += `<div class="tt-time-label">${p.label.replace(' ', '<br>')}</div>`;
            days.forEach((day, dIdx) => {
                const dayKey = day;
                const periodKey = parseInt(p.id);

                // Find if slot exists
                const slot = timetableData.find(s => s.day_of_week === dayKey && s.period === periodKey);

                if (slot) {
                    html += `
                        <div class="tt-cell filled" onclick="openAssignModal('${dayKey}', ${periodKey}, ${slot.id})">
                            <div class="tt-subj">${slot.subject_name}</div>
                            <div class="tt-fac">${slot.faculty_name}</div>
                            <div class="tt-room">${slot.room}</div>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="tt-cell empty" onclick="openAssignModal('${dayKey}', ${periodKey}, null)">
                            <span>Assign Class</span>
                        </div>
                    `;
                }
            });
        }
    });

    grid.innerHTML = html;
}

// -------------------------------------------------------------
// MODAL & ASSIGNMENT LOGIC
// -------------------------------------------------------------
function openAssignModal(day, period, slotId) {
    document.getElementById("slot-day").value = day;
    document.getElementById("slot-period").value = period;

    const pLabel = periods.find(x => x.id === period).label;
    document.getElementById("slot-title").innerText = `Assign Class — ${day.substring(0, 3)} ${pLabel}`;
    document.getElementById("slot-sub").innerText = currentBatch;

    const clearBtn = document.getElementById("slot-clear-btn");

    if (slotId) {
        // Edit mode
        const slot = timetableData.find(s => s.id == slotId);
        document.getElementById("slot-id").value = slot.id;
        document.getElementById("slot-subject").value = slot.subject_id;
        document.getElementById("slot-faculty").value = slot.faculty_id;
        document.getElementById("slot-room").value = slot.room;
        clearBtn.style.display = "block";
    } else {
        // New mode
        document.getElementById("slot-form").reset();
        document.getElementById("slot-id").value = "";
        clearBtn.style.display = "none";
    }
    showModal("slot-modal");
}

async function handleSlotSaveRequest() {
    const payload = {
        batch: currentBatch,
        semester: currentSem,
        day_of_week: document.getElementById("slot-day").value,
        period: parseInt(document.getElementById("slot-period").value),
        subject_id: document.getElementById("slot-subject").value,
        faculty_id: document.getElementById("slot-faculty").value,
        room: document.getElementById("slot-room").value,
        existing_id: document.getElementById("slot-id").value || null
    };

    if (!payload.subject_id || !payload.faculty_id || !payload.room) return alert("Fill all fields.");

    // Conflict Check Phase
    try {
        document.getElementById("slot-save-btn").innerText = "...";
        const conflictRes = await fetch("/api/admin/timetable/check-conflict", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const conflictData = await conflictRes.json();

        if (conflictData.conflict) {
            // Trigger Conflict Modal
            stagingPayload = payload;
            document.getElementById("conflict-msg").innerHTML = `<strong>Conflict Detected:</strong><br>${conflictData.reason}`;
            closeModal("slot-modal");
            document.getElementById("slot-save-btn").innerText = "Save Slot";
            showModal("conflict-modal");
        } else {
            // No Conflict, Proceed
            await commitSlot(payload);
        }
    } catch (e) { alert("Error connecting to server."); }
}

async function handleConflictOverride() {
    if (!stagingPayload) return;
    document.getElementById("conflict-override-btn").innerText = "...";
    await commitSlot(stagingPayload);
    closeModal("conflict-modal");
    document.getElementById("conflict-override-btn").innerText = "Override Anyway";
}

async function commitSlot(payload) {
    try {
        const res = await fetch("/api/admin/timetable/slots", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            closeModal("slot-modal");
            initHydration(); // Re-fetch to guarantee absolute synchronization
        } else throw new Error();
    } catch (e) { alert("Failed to commit slot."); document.getElementById("slot-save-btn").innerText = "Save Slot"; }
}

async function handleSlotClear() {
    const id = document.getElementById("slot-id").value;
    if (!id) return;
    try {
        await fetch(`/api/admin/timetable/slots/${id}`, { method: "DELETE" });
        closeModal("slot-modal");
        initHydration();
    } catch (e) { alert("Failed to clear."); }
}

async function handleAutoGenerate() {
    const btn = document.getElementById("auto-submit-btn");
    btn.innerText = "Running...";
    try {
        const res = await fetch("/api/admin/timetable/auto-generate", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ batch: currentBatch, semester: currentSem })
        });
        const data = await res.json();
        if (data.success) {
            closeModal("auto-modal");
            initHydration();
        } else { alert("Generative logic failed natively."); }
    } catch (e) { alert("Connection Error"); }
    finally { btn.innerText = "Run Generator"; }
}

async function handlePublish() {
    const btn = document.getElementById("publish-submit-btn");
    btn.innerText = "Publishing...";
    try {
        const res = await fetch("/api/admin/timetable/publish", {
            method: "PUT", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ batch: currentBatch, semester: currentSem })
        });
        if ((await res.json()).success) {
            closeModal("publish-modal");
            initHydration();
        } else alert("Publish failed");
    } catch (e) { }
    finally { btn.innerText = "Publish Now"; }
}
