/**
 * JS Handler for Notification Icon & Popup
 */
document.addEventListener('DOMContentLoaded', () => {
    initNotifications();
});

async function initNotifications() {
    const notifBtn = document.querySelector('.notif-btn') || document.querySelector('.notification-bell');
    if (!notifBtn) return;

    // Create popup if it doesn't exist
    let popup = document.querySelector('.notif-popup');
    if (!popup) {
        popup = document.createElement('div');
        popup.className = 'notif-popup';
        popup.innerHTML = `
            <div class="notif-header">
                <h4>Notifications</h4>
                <button class="mark-all-btn" onclick="markAllAsRead()">Mark all as read</button>
            </div>
            <div class="notif-body" id="notif-list-container">
                <div class="empty-notif">Loading...</div>
            </div>
            <div class="notif-footer">
                <a href="/admin/notifications" class="see-all-link">See all notification history</a>
            </div>
        `;
        notifBtn.parentElement.appendChild(popup);
        
        // Adjust "See all" link based on role
        const seeAll = popup.querySelector('.see-all-link');
        if (window.location.pathname.includes('admin')) {
            seeAll.href = '/admin/notifications';
        } else {
            seeAll.href = '/student-dashboard/library'; // Or a dedicated page if exists
        }
    }

    // Toggle logic
    notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        popup.classList.toggle('active');
        if (popup.classList.contains('active')) {
            fetchNotifications();
        }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!popup.contains(e.target) && !notifBtn.contains(e.target)) {
            popup.classList.remove('active');
        }
    });

    // Initial count fetch
    updateUnreadCount();
}

async function updateUnreadCount() {
    try {
        const res = await fetch('/api/notifications/unread-count');
        const data = await res.json();
        const dot = document.querySelector('.notif-dot') || document.querySelector('.bell-dot');
        if (dot) {
            if (data.count > 0) {
                dot.style.display = 'block';
                dot.classList.add('visible');
            } else {
                dot.style.display = 'none';
                dot.classList.remove('visible');
            }
        }
    } catch(e) { console.error('Error fetching unread count:', e); }
}

async function fetchNotifications() {
    const list = document.getElementById('notif-list-container');
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        
        if (!data || data.length === 0) {
            list.innerHTML = '<div class="empty-notif"><i class="fas fa-bell-slash"></i>No recent notifications</div>';
            return;
        }

        list.innerHTML = data.map(n => {
            const isUnread = !n.read_status;
            return `
                <div class="notif-item ${isUnread ? 'unread' : ''}" onclick="markAsRead(${n.id}, this)">
                    <div class="notif-icon">
                        <i class="fas ${n.category === 'Academic' ? 'fa-book' : 'fa-info-circle'}"></i>
                    </div>
                    <div class="notif-info">
                        <div class="notif-msg">${n.message}</div>
                        <div class="notif-time">${formatTime(n.created_at)}</div>
                    </div>
                </div>
            `;
        }).join('');

    } catch(e) { 
        list.innerHTML = '<div class="empty-notif">Error loading notifications</div>';
    }
}

async function markAsRead(id, el) {
    try {
        await fetch(`/api/notifications/mark-read/${id}`, { method: 'POST' });
        el.classList.remove('unread');
        updateUnreadCount();
    } catch(e) {}
}

async function markAllAsRead() {
    try {
        await fetch('/api/notifications/mark-all-read', { method: 'POST' });
        document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
        updateUnreadCount();
    } catch(e) {}
}

function formatTime(dateStr) {
    if (!dateStr) return 'Recently';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return Math.floor(diff/60000) + 'm ago';
    if (diff < 86400000) return Math.floor(diff/3600000) + 'h ago';
    return date.toLocaleDateString();
}
