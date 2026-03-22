document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    fetchUsers();
    setupEventListeners();
});

// App State
const state = {
    users: [],
    metrics: {},
    page: 1,
    limit: 15,
    totalPages: 1,
    roleFilter: 'all',
    statusFilter: 'all',
    searchQuery: '',
    selectedIds: new Set()
};

function setupEventListeners() {
    // Auth Guard check (fallback to session)
    const token = localStorage.getItem('cs_connect_token');
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.role !== 'admin') console.warn('Local role is not admin. Assuming valid Flask session.');
        } catch(e) {}
    }

    // Role Filters
    document.querySelectorAll('.filter-pill[data-filter]').forEach(pill => {
        pill.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-pill[data-filter]').forEach(p => p.classList.remove('active'));
            e.target.classList.add('active');
            state.roleFilter = e.target.dataset.filter;
            state.page = 1;
            fetchUsers();
        });
    });

    // Status Filters
    document.querySelectorAll('.filter-pill[data-filter-status]').forEach(pill => {
        pill.addEventListener('click', (e) => {
            const isActive = e.target.classList.contains('active');
            document.querySelectorAll('.filter-pill[data-filter-status]').forEach(p => p.classList.remove('active'));
            
            if (isActive) {
                state.statusFilter = 'all';
            } else {
                e.target.classList.add('active');
                state.statusFilter = e.target.dataset.filterStatus;
            }
            state.page = 1;
            fetchUsers();
        });
    });

    // Search
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            state.searchQuery = e.target.value.trim();
            state.page = 1;
            fetchUsers();
        }, 300);
    });

    // Modals
    document.getElementById('openAddModalBtn').addEventListener('click', () => openModal('userModal', 'Add User'));
    
    // Add User Role Tabs
    document.querySelectorAll('.role-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            document.querySelectorAll('.role-tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            
            const selectedRole = e.target.dataset.role;
            document.getElementById('roleField').value = selectedRole;
            
            document.getElementById('studentFields').style.display = selectedRole === 'student' ? 'block' : 'none';
            document.getElementById('facultyFields').style.display = (selectedRole === 'faculty' || selectedRole === 'admin') ? 'block' : 'none';
            
            document.getElementById('rollLabelAsterisk').style.display = selectedRole === 'student' ? 'inline' : 'none';
            document.getElementById('rollNoField').required = selectedRole === 'student';
            
            // Password only for Add, not edit
            if (!document.getElementById('userIdField').value) {
                document.getElementById('passwordGroup').style.display = 'block';
            }
        });
    });

    // Save User Form
    document.getElementById('saveUserBtn').addEventListener('click', saveUser);

    // Export
    document.getElementById('exportBtn').addEventListener('click', () => {
        window.open('/api/admin/users/export', '_blank');
    });
    
    // Select All Checkbox
    document.getElementById('selectAllCheckbox').addEventListener('change', (e) => {
        const checked = e.target.checked;
        document.querySelectorAll('.row-checkbox').forEach(cb => {
            cb.checked = checked;
            if (checked) state.selectedIds.add(cb.value);
            else state.selectedIds.delete(cb.value);
        });
        updateBulkBar();
    });

    // Bulk Actions
    document.getElementById('bulkApproveBtn').addEventListener('click', () => submitBulkAction('approve'));
    document.getElementById('bulkDisableBtn').addEventListener('click', () => submitBulkAction('disable'));
}

async function fetchUsers() {
    renderSkeletons();
    try {
        const queryParams = new URLSearchParams({
            page: state.page,
            limit: state.limit,
            role: state.roleFilter,
            status: state.statusFilter,
            search: state.searchQuery
        });
        
        const res = await fetch(`/api/admin/users?${queryParams}`);
        if (!res.ok) throw new Error('Network response was not ok');
        const data = await res.json();
        
        state.users = data.users;
        state.totalPages = data.pages;
        state.metrics = data.metrics || {};
        
        renderMetrics();
        renderTable();
        renderPagination(data.total);
    } catch (err) {
        console.error(err);
        document.getElementById('errorContainer').innerHTML = `
            <div class="error-banner">
                <span class="error-text">Failed to fetch users.</span>
            </div>
        `;
    }
}

function renderSkeletons() {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = Array(5).fill('<tr><td colspan="9"><div class="skeleton" style="height:32px; width:100%"></div></td></tr>').join('');
}

function renderMetrics() {
    const mRow = document.getElementById('metricsRow');
    if (!state.metrics) return;
    
    mRow.innerHTML = `
        <div class="metric-card">
            <div class="metric-title">Total Users</div>
            <div class="metric-value playfair">${state.metrics.total || 0}</div>
            <div class="bottom-accent" style="background: var(--accent);"></div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Students</div>
            <div class="metric-value playfair">${state.metrics.students || 0}</div>
            <div class="bottom-accent" style="background: #6aacff;"></div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Faculty</div>
            <div class="metric-value playfair">${state.metrics.faculty || 0}</div>
            <div class="bottom-accent" style="background: #5c5;"></div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Pending Approval</div>
            <div class="metric-value playfair" style="color:var(--amber)">${state.metrics.pending || 0}</div>
            <div class="bottom-accent" style="background: var(--amber);"></div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Inactive</div>
            <div class="metric-value playfair" style="color:#555">${state.metrics.inactive || 0}</div>
            <div class="bottom-accent" style="background: #555;"></div>
        </div>
    `;
}

function renderTable() {
    const tbody = document.getElementById('usersTableBody');
    if (!state.users || state.users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9">
            <div class="empty-state">
                <i data-lucide="users"></i><span class="empty-message">No users found matching filters.</span>
            </div></td></tr>`;
        lucide.createIcons();
        return;
    }

    state.selectedIds.clear();
    document.getElementById('selectAllCheckbox').checked = false;
    updateBulkBar();

    tbody.innerHTML = state.users.map(u => {
        const initial = u.name ? u.name.charAt(0).toUpperCase() : '?';
        const roleClass = u.role === 'admin' ? 'role-admin' : (u.role === 'faculty' ? 'role-faculty' : 'role-student');
        let statusClass = 'pill-inactive';
        if (u.status === 'Active') statusClass = 'pill-active';
        if (u.status === 'Pending') statusClass = 'pill-pending';
        if (u.status === 'Suspended') statusClass = 'pill-closed';

        let buttons = '';
        if (u.status === 'Active') {
            buttons = `
                <button class="btn btn-action-ghost btn-small-action" onclick="openEditModal(${u.id})">Edit</button>
                <button class="btn btn-action-danger btn-small-action" onclick="promptStatus(${u.id}, 'Inactive', 'disable')">Disable</button>
            `;
        } else if (u.status === 'Pending') {
            buttons = `
                <button class="btn btn-action-approve btn-small-action" onclick="promptStatus(${u.id}, 'Active', 'approve')">Approve</button>
                <button class="btn btn-action-danger btn-small-action" onclick="promptStatus(${u.id}, 'Inactive', 'deny')">Deny</button>
            `;
        } else {
            buttons = `
                <button class="btn btn-action-approve btn-small-action" onclick="promptStatus(${u.id}, 'Active', 'enable')">Enable</button>
                <button class="btn btn-action-danger btn-small-action" onclick="deleteUser(${u.id})">Delete</button>
            `;
        }

        const deptOrBatch = u.role === 'student' ? (u.batch || 'N/A') : (u.department || 'N/A');

        return `
        <tr>
            <td class="td-checkbox">
                <input type="checkbox" class="custom-checkbox row-checkbox" value="${u.id}" onchange="handleRowCheck(this)">
            </td>
            <td>
                <div class="user-cell">
                    <div class="avatar-sm">${initial}</div>
                    <span>${u.name}</span>
                </div>
            </td>
            <td><span class="role-badge ${roleClass}" style="text-transform:capitalize">${u.role}</span></td>
            <td>${u.roll_no}</td>
            <td>${deptOrBatch}</td>
            <td>${u.email}</td>
            <td>${u.created_at}</td>
            <td><span class="status-pill ${statusClass}">${u.status}</span></td>
            <td><div style="display:flex; gap:4px;">${buttons}</div></td>
        </tr>`;
    }).join('');
    
    lucide.createIcons();
}

function renderPagination(totalCount) {
    const ctl = document.getElementById('paginationControls');
    document.getElementById('paginationInfo').textContent = `Showing ${state.users.length > 0 ? ((state.page - 1) * state.limit) + 1 : 0} to ${Math.min(state.page * state.limit, totalCount)} of ${totalCount} users`;
    
    if (state.totalPages <= 1) {
        ctl.innerHTML = '';
        return;
    }
    
    let btns = '';
    // simple bounds
    for(let i = 1; i <= state.totalPages; i++) {
        if (i === 1 || i === state.totalPages || (i >= state.page - 1 && i <= state.page + 1)) {
            btns += `<div class="page-btn ${i === state.page ? 'active' : ''}" onclick="goToPage(${i})">${i}</div>`;
        } else if (i === 2 && state.page > 3) {
            btns += `<span style="color:#555; align-self:center">...</span>`;
        } else if (i === state.totalPages - 1 && state.page < state.totalPages - 2) {
            btns += `<span style="color:#555; align-self:center">...</span>`;
        }
    }
    ctl.innerHTML = btns;
}

function goToPage(p) {
    state.page = p;
    fetchUsers();
}

/* Modals */
function openModal(id, title = '') {
    if (title) document.getElementById('userModalTitle').innerText = title;
    // reset form
    if (title === 'Add User') {
        document.getElementById('userForm').reset();
        document.getElementById('userIdField').value = '';
        document.querySelector('.role-tab[data-role="student"]').click(); // triggers view change
        document.getElementById('passwordGroup').style.display = 'block';
    }
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

window.openEditModal = function(id) {
    const u = state.users.find(x => x.id === id);
    if (!u) return;
    openModal('userModal', 'Edit User');
    
    document.getElementById('userIdField').value = u.id;
    document.getElementById('nameField').value = u.name;
    document.getElementById('emailField').value = u.email;
    document.getElementById('rollNoField').value = u.roll_no;
    
    document.querySelector(`.role-tab[data-role="${u.role}"]`).click(); // updates form fields
    
    if (u.role === 'student') document.getElementById('batchField').value = u.batch || '';
    if (u.role !== 'student') document.getElementById('departmentField').value = u.department || '';
    
    document.getElementById('passwordGroup').style.display = 'none'; // dont edit pw here
};

async function saveUser(e) {
    e.preventDefault();
    const id = document.getElementById('userIdField').value;
    const isEdit = !!id;
    
    const role = document.getElementById('roleField').value;
    const batch = document.getElementById('batchField').value;
    const dept = document.getElementById('departmentField').value;
    const name = document.getElementById('nameField').value;
    const email = document.getElementById('emailField').value;
    const roll_no = document.getElementById('rollNoField').value;
    
    // Basic validation
    if (!name || !email) return alert("Name and Email are required.");
    if (email.indexOf('@aisat.ac.in') === -1 && email.indexOf('@csconnect.in') === -1) {
       // Just a prompt rule validation mock 
       // return alert("Institutional email required");
    }

    const payload = { role, name, email, roll_no };
    if (role === 'student') payload.batch = batch;
    else payload.department = dept;
    
    const method = isEdit ? 'PATCH' : 'POST';
    const endpoint = isEdit ? `/api/admin/users/${id}` : '/api/admin/users';
    
    try {
        document.getElementById('saveUserBtn').textContent = 'Saving...';
        const res = await fetch(endpoint, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            closeModal('userModal');
            fetchUsers();
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        alert("Server error");
    } finally {
        document.getElementById('saveUserBtn').textContent = 'Save User';
    }
}

let pendingStatusAction = { id: null, status: null };
window.promptStatus = function(id, targetStatus, actionName) {
    const u = state.users.find(x => x.id === id);
    if (!u) return;
    pendingStatusAction = { id, status: targetStatus };
    
    const actionMap = {
        'disable': ['disable', 'lose access immediately', 'var(--red)'],
        'deny': ['deny', 'not be granted access', 'var(--red)'],
        'approve': ['approve', 'gain access to CS Connect', 'var(--green)'],
        'enable': ['enable', 'regain access to CS Connect', 'var(--green)'],
    };
    
    const [verb, effect, color] = actionMap[actionName];
    
    const title = document.querySelector('#confirmModal .modal-title');
    title.innerText = verb.charAt(0).toUpperCase() + verb.slice(1) + ' User';
    title.style.color = color;
    
    document.getElementById('confirmMessage').innerText = `Are you sure you want to ${verb} ${u.name}? They will ${effect}.`;
    
    const btn = document.getElementById('confirmActionBtn');
    btn.style.background = color;
    btn.onclick = async () => {
        btn.textContent = 'Processing...';
        await fetch(`/api/admin/users/${pendingStatusAction.id}/status`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: pendingStatusAction.status})
        });
        closeModal('confirmModal');
        btn.textContent = 'Confirm';
        fetchUsers();
    };
    openModal('confirmModal');
};

window.deleteUser = async function(id) {
    if(!confirm("DELETE FOREVER? This cannot be undone.")) return;
    // ... delete API logic ...
};

/* Bulk Actions Support */
window.handleRowCheck = function(checkbox) {
    if (checkbox.checked) state.selectedIds.add(checkbox.value);
    else state.selectedIds.delete(checkbox.value);
    
    // update "select all" checkbox intermediate state
    const allCbs = document.querySelectorAll('.row-checkbox');
    const checkedCbs = document.querySelectorAll('.row-checkbox:checked');
    const master = document.getElementById('selectAllCheckbox');
    
    if (checkedCbs.length === 0) master.checked = false;
    else if (checkedCbs.length === allCbs.length) master.checked = true;
    else master.indeterminate = true;
    
    updateBulkBar();
};

function updateBulkBar() {
    const bar = document.getElementById('bulkActionBar');
    const text = document.getElementById('bulkActionCount');
    if (state.selectedIds.size >= 2) {
        text.innerText = `${state.selectedIds.size} users selected`;
        bar.style.display = 'flex';
    } else {
        bar.style.display = 'none';
    }
}

async function submitBulkAction(action) {
    if (state.selectedIds.size === 0) return;
    try {
        await fetch('/api/admin/users/bulk', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ action, user_ids: Array.from(state.selectedIds) })
        });
        state.selectedIds.clear();
        fetchUsers();
    } catch(e) {
        alert("Bulk action failed");
    }
}
