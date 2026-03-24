document.addEventListener("DOMContentLoaded", () => {

    // UI Elements
    const composeForm = document.getElementById("compose-form");
    const composeVisible = document.getElementById("compose-visible");
    const composeBatchGroup = document.getElementById("compose-batch-group");
    const composeBtn = document.getElementById("compose-btn");

    const noticesList = document.getElementById("notices-list");
    const totalNotices = document.getElementById("total-notices");
    const searchInput = document.getElementById("search-notices");
    const categoryFilters = document.getElementById("category-filters");

    const analyticsTbody = document.getElementById("analytics-tbody");

    // Modals
    const editModal = document.getElementById("edit-modal");
    const editForm = document.getElementById("edit-form");
    const editCancel = document.getElementById("edit-cancel");

    const deleteModal = document.getElementById("delete-modal");
    const deleteCancel = document.getElementById("delete-cancel");
    const deleteConfirmBtn = document.getElementById("delete-confirm-btn");
    const deleteTitleTarget = document.getElementById("delete-title-target");
    const deleteViewsTarget = document.getElementById("delete-views-target");

    let currentFilter = 'all';
    let searchQuery = '';
    let noticesData = [];
    let deleteIdTarget = null;

    // Init
    loadNotices();
    loadAnalytics();

    // Event Bindings
    composeVisible.addEventListener("change", (e) => {
        if (e.target.value === "Specific Batch") {
            composeBatchGroup.style.display = "flex";
        } else {
            composeBatchGroup.style.display = "none";
        }
    });

    categoryFilters.addEventListener("click", (e) => {
        if (e.target.classList.contains("filter-pill")) {
            document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
            e.target.classList.add("active");
            currentFilter = e.target.getAttribute("data-cat");
            renderNoticesList();
        }
    });

    searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.toLowerCase();
        renderNoticesList();
    });

    composeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const original = composeBtn.innerHTML;
        composeBtn.innerHTML = "Posting...";
        composeBtn.disabled = true;

        const payload = {
            title: document.getElementById("compose-title").value,
            category: document.getElementById("compose-category").value,
            content: document.getElementById("compose-content").value,
            audience: document.getElementById("compose-visible").value === "Specific Batch" ? document.getElementById("compose-batch").value : document.getElementById("compose-visible").value,
            priority: document.getElementById("compose-priority").value,
            is_pinned: document.getElementById("compose-pin").checked
        };

        try {
            const res = await fetch("/api/admin/notices", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                composeForm.reset();
                composeBatchGroup.style.display = "none";
                await loadNotices();
                composeBtn.innerHTML = "Success!";
                setTimeout(() => composeBtn.innerHTML = original, 2000);
            } else {
                throw new Error(data.error);
            }
        } catch (err) {
            alert("Error posting notice.");
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
            title: document.getElementById("edit-title").value,
            category: document.getElementById("edit-category").value,
            content: document.getElementById("edit-content").value,
            is_pinned: document.getElementById("edit-pin").checked
        };

        try {
            const res = await fetch(`/api/admin/notices/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                editModal.classList.remove("active");
                loadNotices();
            } else {
                throw new Error();
            }
        } catch (err) {
            alert("Failed to update notice.");
        } finally {
            btn.innerHTML = original;
            btn.disabled = false;
        }
    });

    deleteCancel.addEventListener("click", () => deleteModal.classList.remove("active"));

    deleteConfirmBtn.addEventListener("click", async () => {
        if (!deleteIdTarget) return;
        const btn = deleteConfirmBtn;
        btn.innerHTML = "Deleting...";
        try {
            const res = await fetch(`/api/admin/notices/${deleteIdTarget}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                deleteModal.classList.remove("active");
                loadNotices();
                loadAnalytics();
            }
        } catch (e) {
            alert("Error deleting notice");
        } finally {
            btn.innerHTML = "Delete";
        }
    });

    // API Fetches
    async function loadNotices() {
        try {
            const res = await fetch("/api/admin/notices");
            if (!res.ok) throw new Error();
            noticesData = await res.json();

            if (noticesData.length === 0 && !noticesData.error) {
                // If totally empty database, show empty state immediately
                noticesList.innerHTML = `<div class="state-box"><svg viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg><div class="state-msg">No notices found. Post one to get started!</div></div>`;
                totalNotices.innerText = "0";
                return;
            }
            if (noticesData.error) throw new Error();
            renderNoticesList();
        } catch (e) {
            noticesList.innerHTML = `<div class="state-box error"><div class="state-msg">Failed to load notices list.</div></div>`;
        }
    }

    function renderNoticesList() {
        let html = "";
        let filtered = noticesData.filter(n => {
            const matchesCategory = currentFilter === 'all' || n.category === currentFilter;
            const matchesSearch = n.title.toLowerCase().includes(searchQuery);
            return matchesCategory && matchesSearch;
        });

        totalNotices.innerText = filtered.length;

        if (filtered.length === 0) {
            noticesList.innerHTML = `<div class="state-box"><div class="state-msg" style="color:var(--text-ghost)">No notices found matching filters.</div></div>`;
            return;
        }

        filtered.forEach(n => {
            let catClass = `cat-${n.category.toLowerCase()}`;
            // safe fallback for unknown cats
            if (!['exam', 'event', 'academic', 'library', 'placement', 'urgent'].includes(n.category.toLowerCase())) catClass = 'cat-general';

            let pinHtml = n.is_pinned ? `<svg class="notice-pin" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="17" x2="12" y2="22"></line><path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.68V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v4.68a2 2 0 0 1-1.11 1.87l-1.78.9A2 2 0 0 0 5 15.24Z"></path></svg>` : '';

            html += `
                <div class="notice-item">
                    <div class="notice-top">
                        <span class="cat-badge ${catClass}">${n.category}</span>
                        <div class="notice-title playfair">${n.title}</div>
                        ${pinHtml}
                    </div>
                    <div class="notice-meta">
                        <span><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> ${n.created_at || 'Just now'}</span>
                        <span><svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg> ${n.views_count || 0} views</span>
                        <span><svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg> ${n.audience || 'All'}</span>
                    </div>
                    <div class="notice-actions">
                        <button class="link-action edit-btn" data-id="${n.id}" data-title="${n.title}" data-category="${n.category}" data-content="${escapeHtml(n.content)}" data-pinned="${n.is_pinned}">Edit</button>
                        <button class="link-action delete-btn" data-id="${n.id}" data-title="${n.title}" data-views="${n.views_count}" style="color:var(--accent);">Delete</button>
                    </div>
                </div>
            `;
        });
        noticesList.innerHTML = html;

        // BIND ACTIONS
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.getElementById("edit-id").value = btn.getAttribute('data-id');
                document.getElementById("edit-title").value = btn.getAttribute('data-title');
                document.getElementById("edit-category").value = btn.getAttribute('data-category');
                document.getElementById("edit-content").value = btn.getAttribute('data-content');
                document.getElementById("edit-pin").checked = btn.getAttribute('data-pinned') === 'true' || btn.getAttribute('data-pinned') === '1';
                editModal.classList.add("active");
            });
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                deleteIdTarget = btn.getAttribute('data-id');
                deleteTitleTarget.innerText = btn.getAttribute('data-title');
                deleteViewsTarget.innerText = btn.getAttribute('data-views') || '0';
                deleteModal.classList.add("active");
            });
        });
    }

    async function loadAnalytics() {
        try {
            const res = await fetch("/api/admin/notices/stats");
            let data = await res.json();

            if (!data || data.length === 0) {
                // Mock fallback if table empty
                data = [
                    { title: "Mid-Semester Examinations Schedule published", views_count: 142, category: "Exam", created_at: "Mar 12, 2026" },
                    { title: "TechFest '26 Call for Registrations", views_count: 85, category: "Event", created_at: "Mar 08, 2026" },
                    { title: "Library Closure for Maintenance", views_count: 67, category: "Library", created_at: "Mar 01, 2026" }
                ];
            }

            let html = "";
            data.forEach(d => {
                html += `
                    <tr>
                        <td><span class="mini-title" title="${d.title}">${d.title}</span></td>
                        <td style="color:var(--cream);font-weight:600;">${d.views_count}</td>
                        <td>${d.category}</td>
                        <td>${d.created_at}</td>
                    </tr>
                `;
            });
            analyticsTbody.innerHTML = html;
        } catch (e) {
            analyticsTbody.innerHTML = `<tr><td colspan="4" style="color:var(--accent)">Failed to load metrics</td></tr>`;
        }
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return "";
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

});
