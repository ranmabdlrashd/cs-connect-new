document.addEventListener("DOMContentLoaded", () => {

  // UI Elements
  const metricsGrid = document.getElementById("metrics-grid");
  const subjectBarsContainer = document.getElementById("subject-bars-container");
  const alertsContainer = document.getElementById("alerts-container");
  const studentsTableBody = document.getElementById("students-table-body");

  // Buttons
  const exportBtn1 = document.getElementById("export-report-btn");
  const exportBtn2 = document.getElementById("export-csv-link");
  const sendAlertsBtn = document.getElementById("send-alerts-btn");
  const sendBulkNoticeBtn = document.getElementById("send-bulk-notice");

  // Init fetches
  loadSummaryData();
  loadAtRiskStudents();
  loadAllStudentsTable(); // (we will fetch from /export to get all for now, or /students endpoint)

  // Event Listeners
  exportBtn1.addEventListener("click", downloadExport);
  exportBtn2.addEventListener("click", downloadExport);
  sendAlertsBtn.addEventListener("click", sendBulkAlerts);
  sendBulkNoticeBtn.addEventListener("click", sendBulkAlerts);


  // API CALLS

  async function loadSummaryData() {
    try {
      const res = await fetch("/api/admin/attendance");
      if (!res.ok) throw new Error("Failed to load");
      const data = await res.json();

      metricsGrid.innerHTML = `
                <div class="metric-card">
                    <div class="label">Dept. Average <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#555" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></div>
                    <div class="value large-number">${data.dept_average}%</div>
                    <div class="metric-line" style="background:#8B1D1D;"></div>
                </div>
                <div class="metric-card">
                    <div class="label">Students Safe <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#555" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>
                    <div class="value large-number" style="color:#3a8834;">${data.safe_count}</div>
                    <div class="sub">≥75% Attendance</div>
                    <div class="metric-line" style="background:#3a8834;"></div>
                </div>
                <div class="metric-card">
                    <div class="label">At Risk <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#555" stroke-width="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg></div>
                    <div class="value large-number" style="color:#b85a00;">${data.risk_count}</div>
                    <div class="sub">65–74%</div>
                    <div class="metric-line" style="background:#b85a00;"></div>
                </div>
                <div class="metric-card">
                    <div class="label">Not Eligible <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#555" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg></div>
                    <div class="value large-number" style="color:#8B1D1D;">${data.low_count}</div>
                    <div class="sub">Condonation needed (<65%)</div>
                    <div class="metric-line" style="background:#8B1D1D;"></div>
                </div>
            `;

      // Dummy logic for subject bars since API doesn't provide it yet
      // Just creating some nice looking UI based on dept average
      const mockSubjects = [
        { name: "Data Structures", att: data.dept_average + 2 },
        { name: "Operating Systems", att: data.dept_average - 5 },
        { name: "Maths 3", att: Math.min(100, data.dept_average + 5) },
        { name: "Computer Networks", att: data.dept_average - 8 },
        { name: "Ethics", att: 95 }
      ];
      mockSubjects.sort((a, b) => b.att - a.att);

      let barsHtml = "";
      mockSubjects.forEach(s => {
        let color = s.att >= 80 ? "#3a8834" : (s.att >= 65 ? "#b85a00" : "#8B1D1D");
        barsHtml += `
                    <div class="bar-row">
                        <div class="bar-label" title="${s.name}">${s.name}</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: ${s.att}%; background-color: ${color};"></div>
                        </div>
                        <div class="bar-val" style="color: ${color}">${s.att.toFixed(1)}%</div>
                    </div>
                `;
      });
      subjectBarsContainer.innerHTML = barsHtml;

    } catch (e) {
      metricsGrid.innerHTML = `<div class="state-box error" style="grid-column:1/-1"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg><div class="state-msg">Failed to load metrics.</div><button class="btn btn-ghost btn-small" onclick="location.reload()">Retry</button></div>`;
      subjectBarsContainer.innerHTML = `<div class="state-msg">Data unavailable.</div>`;
    }
  }

  async function loadAtRiskStudents() {
    try {
      const res = await fetch("/api/admin/attendance/students");
      if (!res.ok) throw new Error("Failed to load list");
      const data = await res.json();

      if (data.length === 0) {
        alertsContainer.innerHTML = `<div class="state-box"><svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg><div class="state-msg">No students at risk. Everything looks great!</div></div>`;
        return;
      }

      let html = "";
      data.forEach(s => {
        let isCritical = s.avg_att < 65;
        let pillClass = isCritical ? "pill-red" : "pill-amber";
        let pillText = isCritical ? "Critical" : "At Risk";

        html += `
                    <div class="student-alert-card">
                        <div class="student-alert-info">
                            <div class="sa-name">${s.name}</div>
                            <div class="sa-meta">Roll: ${s.roll_no} · Avg: <span style="color:${isCritical ? 'var(--red)' : 'var(--amber)'}; font-weight:600">${s.avg_att}%</span> · ${s.low_subjects} subjects below 75%</div>
                        </div>
                        <div class="pill ${pillClass}">${pillText}</div>
                    </div>
                `;
      });

      html += `<button class="view-all-alerts">View All ${data.length} Students <svg viewBox="0 0 24 24" width="10" height="10" stroke="currentColor" fill="none" stroke-width="2" style="margin-left:4px; vertical-align:-1px;"><path d="M5 12h14"></path><path d="M12 5l7 7-7 7"></path></svg></button>`;
      alertsContainer.innerHTML = html;

    } catch (e) {
      alertsContainer.innerHTML = `<div class="state-msg" style="color:var(--accent)">Failed to load alerts.</div>`;
    }
  }

  async function loadAllStudentsTable() {
    try {
      // Reusing the students endpoint or creating a fallback
      // since /students only gives risks, we would normally have an all endpoint
      // But we'll use /students or export logic. For demo, we just fetch /students 
      // and show them. The API doesn't have an endpoint serving ALL students attendance directly except export.
      // We will use the new /all endpoint to fetch all students attendance data.
      const res = await fetch("/api/admin/attendance/all");
      if (!res.ok) throw new Error();
      const data = await res.json();

      if (data.length === 0) {
        studentsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;"><div class="state-box"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg><div class="state-msg">No detailed records found.</div></div></td></tr>`;
        return;
      }

      let html = "";
      data.forEach(s => {
        let color = s.avg_att >= 80 ? "var(--green)" : (s.avg_att >= 65 ? "var(--amber)" : "var(--red)");
        let statusPill = s.avg_att >= 75 ? `<span class="pill pill-green">Safe</span>` :
          (s.avg_att >= 65 ? `<span class="pill pill-amber">At Risk</span>` : `<span class="pill pill-red">Low</span>`);

        html += `
                    <tr>
                        <td>${s.name}</td>
                        <td>${s.roll_no}</td>
                        <td>S2 CSE A</td>
                        <td>${s.low_subjects} below 75%</td>
                        <td style="color:${color}; font-weight:600;">${s.avg_att}%</td>
                        <td>${statusPill}</td>
                        <td>
                            <button class="btn btn-danger-outline btn-small action-notify" data-id="${s.student_id}">Send Alert</button>
                        </td>
                    </tr>
                `;
      });
      studentsTableBody.innerHTML = html;

      // Re-bind alert buttons
      document.querySelectorAll(".action-notify").forEach(btn => {
        btn.addEventListener('click', (e) => {
          const id = e.target.getAttribute('data-id');
          sendSingleAlert(id, e.target);
        });
      });

    } catch (e) {
      studentsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--red);">Failed to load table data.</td></tr>`;
    }
  }


  function downloadExport() {
    window.location.href = "/api/admin/attendance/export";
  }

  async function sendBulkAlerts() {
    if (!confirm("Are you sure you want to send alert notifications to all students with <75% attendance?")) return;

    try {
      const res = await fetch("/api/admin/attendance/send-bulk-alert", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        alert(`Alerts sent successfully to ${data.notified} students.`);
      } else {
        alert("Failed to send alerts.");
      }
    } catch (e) {
      alert("Error sending bulk alerts.");
    }
  }

  async function sendSingleAlert(id, btnElement) {
    const originalText = btnElement.innerText;
    btnElement.innerText = "Sending...";
    try {
      const res = await fetch(`/api/admin/attendance/send-alert/${id}`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        btnElement.innerText = "Sent!";
        btnElement.classList.replace("btn-danger-outline", "btn-ghost");
        setTimeout(() => { btnElement.innerText = originalText; btnElement.classList.replace("btn-ghost", "btn-danger-outline"); }, 2000);
      }
    } catch (e) {
      btnElement.innerText = "Error";
      setTimeout(() => { btnElement.innerText = originalText; }, 2000);
    }
  }

});
