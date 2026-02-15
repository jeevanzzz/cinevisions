document.addEventListener('DOMContentLoaded', function () {
    // Poll every 5 seconds
    setInterval(checkNotifications, 5000);

    // Initial check
    checkNotifications();

    function checkNotifications() {
        console.log("Checking for notifications...");
        fetch('/api/notifications/unread')
            .then(response => {
                if (response.status === 403) return []; // Not admin
                return response.json();
            })
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    data.forEach(notif => {
                        showToast(notif);
                    });
                }
            })
            .catch(err => console.error('Error fetching notifications:', err));
    }

    function showToast(notif) {
        // Create toast element unique ID
        const toastId = `toast-${notif.id}`;

        // Prevent duplicate toasts
        if (document.getElementById(toastId)) return;

        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="false" style="border: 1px solid var(--primary);">
                <div class="toast-header bg-warning text-dark">
                    <strong class="me-auto">🔔 New Notification</strong>
                    <small>Just now</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close" onclick="markRead(${notif.id})"></button>
                </div>
                <div class="toast-body bg-dark text-white">
                    ${notif.message}
                    <div class="mt-2 pt-2 border-top border-secondary">
                        <button type="button" class="btn btn-sm btn-primary w-100" onclick="markRead(${notif.id})">Mark as Read</button>
                    </div>
                </div>
            </div>
        `;

        const container = document.getElementById('toast-container');
        if (container) {
            container.insertAdjacentHTML('beforeend', toastHtml);
            const toastEl = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        }
    }

    // Global function to mark as read
    window.markRead = function (id) {
        fetch(`/api/notifications/mark-read/${id}`, { method: 'POST' })
            .then(() => {
                const toastEl = document.getElementById(`toast-${id}`);
                if (toastEl) {
                    const toastInstance = bootstrap.Toast.getInstance(toastEl);
                    if (toastInstance) toastInstance.hide();
                    // Remove from DOM after transition
                    setTimeout(() => {
                        if (toastEl && toastEl.parentNode) {
                            toastEl.remove();
                        }
                    }, 500);
                }
            })
            .catch(err => console.error(err));
    }
});
