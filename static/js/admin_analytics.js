const fmtLPA = (val) => `₹${val} LPA`;

document.addEventListener("DOMContentLoaded", () => {
    initHydration();

    // Bind Forms
    document.getElementById("custom-rep-form").addEventListener("submit", handleCustomReportGen);
    document.getElementById("quick-rep-form").addEventListener("submit", handleQuickReportGen);
});

function showModal(id) { document.getElementById(id).classList.add("active"); }
function closeModal(id) { document.getElementById(id).classList.remove("active"); }

function openQuickReport(typeStr) {
    document.getElementById("qr-title").innerText = `${typeStr} Report`;
    document.getElementById("qr-type").value = typeStr;

    // Default dates (Last 30 Days)
    const today = new Date();
    const last30 = new Date();
    last30.setDate(today.getDate() - 30);

    document.getElementById("qr-start").value = last30.toISOString().split("T")[0];
    document.getElementById("qr-end").value = today.toISOString().split("T")[0];

    showModal("quick-rep-modal");
}

async function initHydration() {
    try {
        // Concurrently run structural fetches
        const [overviewRes, activityRes, cgpaRes] = await Promise.all([
            fetch("/api/admin/analytics/overview"),
            fetch("/api/admin/analytics/activity"),
            fetch("/api/admin/analytics/cgpa")
        ]);

        renderOverview(await overviewRes.json());
        renderActivityChart(await activityRes.json());
        renderCGPAChart(await cgpaRes.json());

    } catch (err) { console.error("Global analytics rendering interrupted.", err); }
}

// -----------------------------------------------------------------
// 1. KPI & DONUT LOGIC (Overview)
// -----------------------------------------------------------------
function renderOverview(data) {
    // Top Row KPIs
    document.getElementById("kpi-logins").innerText = data.logins_today || 0;
    document.getElementById("kpi-cgpa").innerText = data.avg_cgpa || '0.0';
    document.getElementById("kpi-papers").innerText = data.research_papers || 0;

    // Attendance section removed
}

// -----------------------------------------------------------------
// 2. VERTICAL BAR CHART (Activity)
// -----------------------------------------------------------------
function renderActivityChart(data) {
    if (!data || data.length === 0) return;

    // Find absolute maximum traversing mapping algorithm
    // Limit to exactly 6 records
    const subset = data.slice(0, 6);
    let masterMax = 2000; // Force 2000 alignment to grid visually correctly
    subset.forEach(d => { if (d.sessions > masterMax) masterMax = d.sessions + 200; });

    let html = '';
    subset.forEach((m, idx) => {
        const heightCalc = (m.sessions / masterMax) * 100;
        const currentClass = idx === subset.length - 1 ? 'current' : ''; // Highlight last column logically
        html += `
        <div class="vc-bar-wrap">
            <div class="vc-bar ${currentClass}" style="height:${heightCalc}%">
                <div class="vc-val">${m.sessions}</div>
            </div>
            <div class="vc-label">${m.month}</div>
        </div>
        `;
    });

    document.getElementById("chart-activity").innerHTML = html;
}

// -----------------------------------------------------------------
// 3. HORIZONTAL BAR CHART (CGPA)
// -----------------------------------------------------------------
function renderCGPAChart(data) {
    // Expected keys natively: dist(>=9), fplus(8-8.9), f(7-7.9), sec(6-6.9), th(<6)
    if (!data) return;

    let localMax = 1;
    Object.values(data).forEach(v => { if (v > localMax) localMax = v; });

    const layout = [
        { lbl: "9.0 - 10.0", val: data.distinction || 0 },
        { lbl: "8.0 - 8.9", val: data.first_plus || 0 },
        { lbl: "7.0 - 7.9", val: data.first || 0 },
        { lbl: "6.0 - 6.9", val: data.second || 0 },
        { lbl: "< 6.0", val: data.third || 0 }
    ];

    let html = '';
    layout.forEach(row => {
        // Evaluate dynamic max width cleanly bypassing 100% overflow restrictions natively
        let barWidth = localMax === 0 ? 0 : Math.max(2, (row.val / localMax) * 100);
        html += `
        <div class="hc-row">
            <div class="hc-label">${row.lbl}</div>
            <div class="hc-track">
                <div class="hc-fill" style="width:${barWidth}%"></div>
                <div class="hc-val">${row.val}</div>
            </div>
        </div>`;
    });

    document.getElementById("chart-cgpa").innerHTML = html;
}

// -----------------------------------------------------------------
// 4. PLACEMENT LIST
// -----------------------------------------------------------------
function renderPlacementList(data) {
    if (!data) return;

    let html = `
    <div class="ps-item">
        <div class="ps-lbl">Total Placed</div>
        <div class="ps-val playfair">${data.total_placed} <span class="ps-sub">Students</span></div>
    </div>
    <div class="ps-item">
        <div class="ps-lbl">Highest Package</div>
        <div class="ps-val playfair" style="color:#b85a00">${fmtLPA(data.highest)}</div>
    </div>
    <div class="ps-item">
        <div class="ps-lbl">Average Package</div>
        <div class="ps-val playfair" style="color:var(--green)">${fmtLPA(data.average)}</div>
    </div>
    <div class="ps-item">
        <div class="ps-lbl">Top Recruiter</div>
        <div class="ps-val" style="display:flex;align-items:center;">
             ${data.top_recruiter.name} <span class="ps-sub">(${data.top_recruiter.offers} offers)</span>
        </div>
    </div>
    <div class="ps-item">
        <div class="ps-lbl">Companies Visited</div>
        <div class="ps-val playfair">${data.companies}</div>
    </div>
    `;

    document.getElementById("chart-placement").innerHTML = html;
}

// -----------------------------------------------------------------
// POST APIs
// -----------------------------------------------------------------
async function handleQuickReportGen(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-submit-quick");
    btn.innerText = "Processing Thread...";

    const payload = {
        type: document.getElementById("qr-type").value,
        format: document.getElementById("qr-format").value,
        start_date: document.getElementById("qr-start").value,
        end_date: document.getElementById("qr-end").value
    };

    try {
        const res = await fetch("/api/admin/reports/generate", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const ans = await res.json();

        closeModal("quick-rep-modal");
        alert(ans.success ? "Generated Format Array Triggered Successfully." : "Formatting bypass failed inherently.");
    } catch (err) { }
    finally { btn.innerText = "Initiate Thread"; }
}

async function handleCustomReportGen(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-submit-custom");
    btn.innerText = "Synthesizing Elements...";

    const checked = Array.from(document.querySelectorAll("input[name='ctype']:checked")).map(el => el.value);

    try {
        const res = await fetch("/api/admin/reports/custom", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                elements: checked,
                format: document.getElementById("custom-format").value
            })
        });
        const ans = await res.json();

        closeModal("custom-rep-modal");
        alert(ans.success ? "Custom Multidimensional Export Assembled!" : "Failed resolving subsets natively.");
    } catch (err) { }
    finally { btn.innerText = "Generate Intersecting Report"; }
}
