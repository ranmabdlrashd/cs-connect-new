document.addEventListener("DOMContentLoaded", () => {

    // UI Elements
    const composeForm = document.getElementById("compose-form");
    const composeBtn = document.getElementById("compose-btn");

    const upcomingGrid = document.getElementById("upcoming-grid");
    const upcomingCount = document.getElementById("upcoming-count");

    const pastToggle = document.getElementById("past-toggle");
    const pastContent = document.getElementById("past-content");
    const pastList = document.getElementById("past-list");
    const pastCount = document.getElementById("past-count");

    const highlightsList = document.getElementById("highlights-list");
    const hlCountLabel = document.getElementById("hl-count-label");

    // Modals
    const editModal = document.getElementById("edit-modal");
    const editForm = document.getElementById("edit-form");
    const editCancel = document.getElementById("edit-cancel");

    const deleteModal = document.getElementById("delete-modal");
    const deleteCancel = document.getElementById("delete-cancel");
    const deleteConfirmBtn = document.getElementById("delete-confirm-btn");
    const deleteTitleTarget = document.getElementById("delete-title-target");

    let eventsData = [];
    let deleteIdTarget = null;
    let dragSrcEl = null;

    // Init
    loadEvents();

    // Event Bindings
    pastToggle.addEventListener("click", () => {
        pastToggle.classList.toggle("open");
        pastContent.classList.toggle("open");
    });

    composeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const original = composeBtn.innerHTML;
        composeBtn.innerHTML = "Adding...";
        composeBtn.disabled = true;

        const payload = {
            title: document.getElementById("compose-title").value,
            category: document.getElementById("compose-category").value,
            event_date: document.getElementById("compose-date").value,
            venue: document.getElementById("compose-venue").value,
            description: document.getElementById("compose-desc").value,
            icon_name: document.getElementById("compose-icon").value,
            registration_link: document.getElementById("compose-link").value,
            show_on_homepage: document.getElementById("compose-show").checked
        };

        try {
            const res = await fetch("/api/admin/events", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                composeForm.reset();
                await loadEvents();
                composeBtn.innerHTML = "Added!";
                setTimeout(() => composeBtn.innerHTML = original, 2000);
            } else {
                throw new Error();
            }
        } catch (err) {
            alert("Error adding event.");
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
            event_date: document.getElementById("edit-date").value,
            venue: document.getElementById("edit-venue").value,
            description: document.getElementById("edit-desc").value,
            show_on_homepage: document.getElementById("edit-show").checked
        };

        try {
            const res = await fetch(`/api/admin/events/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                editModal.classList.remove("active");
                loadEvents();
            } else throw new Error();
        } catch (err) {
            alert("Failed to update event.");
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
            const res = await fetch(`/api/admin/events/${deleteIdTarget}`, { method: "DELETE" });
            const data = await res.json();
            if (data.success) {
                deleteModal.classList.remove("active");
                loadEvents();
            }
        } catch (e) {
            alert("Error deleting event");
        } finally {
            btn.innerHTML = "Delete";
        }
    });

    // Fetches
    async function loadEvents() {
        try {
            const res = await fetch("/api/admin/events");
            if (!res.ok) throw new Error();
            eventsData = await res.json();

            if (eventsData.length === 0 && !eventsData.error) {
                renderEmpty();
                return;
            }
            if (eventsData.error) throw new Error();

            renderLists();
        } catch (e) {
            upcomingGrid.innerHTML = `<div class="state-box error"><div class="state-msg">Failed to load events.</div></div>`;
            pastList.innerHTML = `<div class="state-msg" style="color:var(--accent)">Failed to load.</div>`;
        }
    }

    function renderEmpty() {
        upcomingCount.innerText = "0 items";
        pastCount.innerText = "0";
        hlCountLabel.innerText = "Currently showing 0 highlight slots";
        upcomingGrid.innerHTML = `<div class="state-box"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg><div class="state-msg">No events found.</div></div>`;
        pastList.innerHTML = `<div class="state-msg" style="padding:10px;">No past events.</div>`;
        highlightsList.innerHTML = `<div class="state-msg">No showcase events designated.</div>`;
    }

    function renderLists() {
        const now = new Date();
        const upcoming = [];
        const past = [];
        const highlights = [];

        eventsData.forEach(e => {
            if (new Date(e.event_date) >= now) upcoming.push(e);
            else past.push(e);

            if (e.show_on_homepage) highlights.push(e);
        });

        upcomingCount.innerText = `${upcoming.length} items`;
        if (upcoming.length === 0) upcomingGrid.innerHTML = `<div class="state-box"><div class="state-msg">No upcoming events.</div></div>`;
        else {
            let html = "";
            upcoming.forEach(e => {
                html += `
                    <div class="event-card">
                        <div class="ec-top">
                            <div class="ec-title">${e.title}</div>
                            <span class="ec-badge badge-upcoming">Upcoming</span>
                        </div>
                        <div class="ec-row"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> ${formatDate(e.event_date)}</div>
                        <div class="ec-row"><svg viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> ${e.venue || 'TBA'}</div>
                        <div class="ec-desc">${escapeHtml(e.description)}</div>
                        <div class="ec-actions">
                            <button class="ec-action-btn exec-edit" data-id="${e.id}">Edit</button>
                            <button class="ec-action-btn delete exec-delete" data-id="${e.id}" data-title="${e.title}">Delete</button>
                        </div>
                    </div>
                `;
            });
            upcomingGrid.innerHTML = html;
        }

        pastCount.innerText = past.length;
        if (past.length === 0) pastList.innerHTML = `<div class="state-msg" style="padding:10px;">No past events.</div>`;
        else {
            let html = "";
            past.slice(0, 10).forEach(e => {
                html += `
                    <div class="past-item">
                        <div class="past-item-info">
                            <div class="past-item-title">${e.title}</div>
                            <div class="past-item-meta"><span>${formatDate(e.event_date)}</span><span>&bull;</span><span>${e.category}</span></div>
                        </div>
                        <div style="display:flex; gap:10px;">
                            <button class="ec-action-btn exec-edit" data-id="${e.id}">Edit</button>
                            <button class="ec-action-btn delete exec-delete" data-id="${e.id}" data-title="${e.title}">Delete</button>
                        </div>
                    </div>
                `;
            });
            pastList.innerHTML = html;
        }

        hlCountLabel.innerText = `Currently showing ${highlights.length} highlight slot${highlights.length !== 1 ? 's' : ''}`;
        if (highlights.length === 0) highlightsList.innerHTML = `<div class="state-msg">No showcase events designated.</div>`;
        else {
            let html = "";
            highlights.forEach(e => {
                html += `
                    <div class="hl-item" draggable="true" data-id="${e.id}">
                        <div class="hl-drag-handle"><svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg></div>
                        <div class="hl-item-info">
                            <div class="hl-item-title">${e.title}</div>
                            <div class="hl-item-cat">${e.category}</div>
                        </div>
                        <label class="switch">
                            <input type="checkbox" checked class="hl-toggle" data-id="${e.id}">
                            <span class="slider"></span>
                        </label>
                    </div>
                `;
            });
            highlightsList.innerHTML = html;
            bindDragDrop();
        }

        bindActionButtons();
    }

    function bindActionButtons() {
        document.querySelectorAll('.exec-edit').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-id');
                const e = eventsData.find(x => x.id == id);
                if (e) {
                    document.getElementById("edit-id").value = e.id;
                    document.getElementById("edit-title").value = e.title;
                    document.getElementById("edit-category").value = e.category;
                    const d = e.event_date.split(" ")[0];
                    document.getElementById("edit-date").value = d;
                    document.getElementById("edit-venue").value = e.venue || '';
                    document.getElementById("edit-desc").value = e.description;
                    document.getElementById("edit-show").checked = e.show_on_homepage === 1 || e.show_on_homepage === true;
                    editModal.classList.add("active");
                }
            });
        });

        document.querySelectorAll('.exec-delete').forEach(btn => {
            btn.addEventListener('click', () => {
                deleteIdTarget = btn.getAttribute('data-id');
                deleteTitleTarget.innerText = btn.getAttribute('data-title');
                deleteModal.classList.add("active");
            });
        });

        document.querySelectorAll(".hl-toggle").forEach(toggle => {
            toggle.addEventListener('change', async (e) => {
                const id = e.target.getAttribute('data-id');
                try {
                    await fetch(`/api/admin/events/${id}/toggle-homepage`, { method: "PATCH" });
                    loadEvents();
                } catch (err) { e.target.checked = !e.target.checked; }
            });
        });
    }

    function bindDragDrop() {
        let items = document.querySelectorAll('.hl-item');
        items.forEach(function (item) {
            item.addEventListener('dragstart', handleDragStart, false);
            item.addEventListener('dragenter', handleDragEnter, false);
            item.addEventListener('dragover', handleDragOver, false);
            item.addEventListener('dragleave', handleDragLeave, false);
            item.addEventListener('drop', handleDrop, false);
            item.addEventListener('dragend', handleDragEnd, false);
        });
    }

    function handleDragStart(e) {
        dragSrcEl = this;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.innerHTML);
        this.classList.add('dragging');
    }

    function handleDragOver(e) {
        if (e.preventDefault) e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        return false;
    }

    function handleDragEnter(e) { this.style.opacity = '0.5'; }
    function handleDragLeave(e) { this.style.opacity = '1'; }

    async function handleDrop(e) {
        if (e.stopPropagation) e.stopPropagation();
        if (dragSrcEl !== this) {
            const parent = dragSrcEl.parentNode;
            const draggingIndex = Array.from(parent.children).indexOf(dragSrcEl);
            const dropIndex = Array.from(parent.children).indexOf(this);

            if (draggingIndex < dropIndex) {
                parent.insertBefore(dragSrcEl, this.nextSibling);
            } else {
                parent.insertBefore(dragSrcEl, this);
            }

            let newOrder = Array.from(parent.children).map(child => child.getAttribute('data-id'));

            try {
                await fetch("/api/admin/events/homepage-order", {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ order: newOrder })
                });
            } catch (e) { console.error(e); }
        }
        return false;
    }

    function handleDragEnd(e) {
        document.querySelectorAll('.hl-item').forEach(item => {
            item.classList.remove('dragging');
            item.style.opacity = '1';
        });
        bindActionButtons();
    }

    function formatDate(dStr) {
        const d = new Date(dStr);
        if (isNaN(d)) return dStr;
        const month = d.toLocaleString('default', { month: 'short' });
        const day = d.getDate();
        const yr = d.getFullYear();
        return `${month} ${day}, ${yr}`;
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return "";
        return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

});
