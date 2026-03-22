// admin_attendance.js
// This script fetches data from the admin attendance API endpoints and populates the UI components.

document.addEventListener('DOMContentLoaded', () => {
  // Fetch and display summary metrics
  fetchSummary();
  // Populate subject-wise attendance bars
  fetchSubjectBars();
  // Load at‑risk students list
  fetchAtRiskStudents();
  // Load detailed student table with pagination
  loadStudentsTable(1);

  // Event listeners for export and alert buttons
  document.getElementById('exportReportBtn')?.addEventListener('click', exportReport);
  document.getElementById('sendAlertsBtn')?.addEventListener('click', sendBulkAlerts);
  document.getElementById('bulkAlertBtn')?.addEventListener('click', sendBulkAlerts);
  document.getElementById('exportCsvBtn')?.addEventListener('click', exportCsv);

  // Filter change listeners (subject, faculty, search)
  document.getElementById('subjectFilter')?.addEventListener('change', () => loadStudentsTable(1));
  document.getElementById('facultyFilter')?.addEventListener('change', () => loadStudentsTable(1));
  document.getElementById('studentSearch')?.addEventListener('input', () => loadStudentsTable(1));
});

function fetchSummary() {
  fetch('/api/admin/attendance')
    .then(res => res.json())
    .then(data => {
      document.getElementById('cardDeptAvg').innerHTML = `<h4>Dept Avg</h4><p>${data.dept_average}%</p>`;
      document.getElementById('cardSafe').innerHTML = `<h4>Safe</h4><p>${data.safe_count}</p>`;
      document.getElementById('cardRisk').innerHTML = `<h4>Risk</h4><p>${data.risk_count}</p>`;
      document.getElementById('cardLow').innerHTML = `<h4>Low</h4><p>${data.low_count}</p>`;
    })
    .catch(err => console.error('Error loading summary:', err));
}

function fetchSubjectBars() {
  // Assuming an endpoint exists for subject averages – reuse summary for demo
  // Replace with real endpoint when available
  fetch('/api/admin/attendance')
    .then(res => res.json())
    .then(data => {
      // Mock data for demonstration
      const subjects = [
        { name: 'Math', avg: 85 },
        { name: 'Physics', avg: 78 },
        { name: 'Chemistry', avg: 72 },
        { name: 'Biology', avg: 68 },
        { name: 'History', avg: 60 },
      ];
      const container = document.getElementById('subjectBars');
      container.innerHTML = subjects.map(s => `
        <div class="subject-bar">
          <div class="subject-name">${s.name}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${s.avg}%; background:${s.avg >= 75 ? 'var(--green)' : s.avg >= 65 ? 'var(--amber)' : 'var(--red)'}"></div></div>
          <div class="bar-perc">${s.avg}%</div>
        </div>`).join('');
    })
    .catch(err => console.error('Error loading subject bars:', err));
}

function fetchAtRiskStudents() {
  fetch('/api/admin/attendance/students')
    .then(res => res.json())
    .then(students => {
      const container = document.getElementById('atRiskStudents');
      if (students.length === 0) {
        container.innerHTML = '<p class="text-ghost">No at‑risk students.</p>';
        return;
      }
      container.innerHTML = students.map(s => `
        <div class="at-risk-card">
          <div class="info">${s.name} (Roll: ${s.roll_no})</div>
          <div class="details">Avg: ${s.avg_att}% – Low subjects: ${s.low_subjects}</div>
          <button class="btn btn-primary btn-small-action" onclick="sendAlert(${s.student_id})">Alert</button>
        </div>`).join('');
    })
    .catch(err => console.error('Error loading at‑risk students:', err));
}

function sendAlert(studentId) {
  fetch(`/api/admin/attendance/send-alert/${studentId}`, { method: 'POST' })
    .then(res => res.json())
    .then(() => alert('Alert sent'))
    .catch(err => console.error('Error sending alert:', err));
}

function sendBulkAlerts() {
  fetch('/api/admin/attendance/send-bulk-alert', { method: 'POST' })
    .then(res => res.json())
    .then(data => alert(`Bulk alerts sent to ${data.notified} students`))
    .catch(err => console.error('Error sending bulk alerts:', err));
}

function exportReport() {
  // Trigger CSV export endpoint
  window.location.href = '/api/admin/attendance/export';
}

function exportCsv() {
  // Alias for exportReport – kept for UI button consistency
  exportReport();
}

function loadStudentsTable(page) {
  const subject = document.getElementById('subjectFilter')?.value || '';
  const faculty = document.getElementById('facultyFilter')?.value || '';
  const search = document.getElementById('studentSearch')?.value || '';
  const params = new URLSearchParams({ page, subject, faculty, search });
  fetch(`/api/admin/attendance/students?${params}`)
    .then(res => res.json())
    .then(data => {
      const tbody = document.getElementById('studentsTbody');
      tbody.innerHTML = data.students.map(s => `
        <tr>
          <td>${s.name}</td>
          <td>${s.roll_no}</td>
          <td>${s.batch}</td>
          <td>${s.avg_att}%</td>
          <td><span class="status-pill ${s.avg_att >= 75 ? 'status-safe' : s.avg_att >= 65 ? 'status-warn' : 'status-danger'}">${s.avg_att >= 75 ? 'Safe' : s.avg_att >= 65 ? 'Risk' : 'Low'}</span></td>
          <td><button class="btn btn-ghost btn-small-action" onclick="sendAlert(${s.id})">Alert</button></td>
        </tr>`).join('');
      // Simple pagination UI (assumes total_pages returned)
      const pagination = document.getElementById('pagination');
      pagination.innerHTML = '';
      for (let i = 1; i <= data.total_pages; i++) {
        const btn = document.createElement('button');
        btn.className = 'pagination-btn' + (i === page ? ' active' : '');
        btn.textContent = i;
        btn.onclick = () => loadStudentsTable(i);
        pagination.appendChild(btn);
      }
    })
    .catch(err => console.error('Error loading student table:', err));
}
