/**
 * SKILL2HIRE — Main JavaScript
 * Save/Unsave jobs, notifications, UI enhancements
 */

document.addEventListener('DOMContentLoaded', function () {

  // --- Save/Unsave Job Buttons ---
  document.querySelectorAll('.save-btn').forEach(btn => {
    btn.addEventListener('click', async function (e) {
      e.preventDefault();
      e.stopPropagation();
      const jobId = this.dataset.jobId;
      const isSaved = this.dataset.saved === 'true';

      try {
        const resp = await fetch(`/api/jobs/${jobId}/save`, {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!resp.ok) {
          if (resp.status === 401) {
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
            return;
          }
          const data = await resp.json();
          showToast(data.error || 'Failed to save job.', 'danger');
          return;
        }
        const data = await resp.json();
        if (data.error) {
          showToast(data.error, 'warning');
          return;
        }

        const newSaved = data.saved;
        this.dataset.saved = newSaved ? 'true' : 'false';
        const icon = this.querySelector('i');
        if (icon) {
          icon.className = newSaved
            ? 'bi bi-bookmark-fill text-primary'
            : 'bi bi-bookmark';
        }
        // Update button text if it has text
        const textNode = [...this.childNodes].find(n => n.nodeType === 3);
        if (textNode) textNode.textContent = newSaved ? ' Saved' : ' Save';
        this.title = newSaved ? 'Remove from saved' : 'Save job';
        showToast(data.message, 'success');
      } catch (err) {
        console.error('Save job error:', err);
        showToast('Failed to save job. Please try again.', 'danger');
      }
    });
  });

  // --- Toast Notification ---
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    const id = 'toast-' + Date.now();
    const icons = { success: 'bi-check-circle-fill', danger: 'bi-exclamation-triangle-fill', warning: 'bi-exclamation-circle-fill', info: 'bi-info-circle-fill' };
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0 show mb-2`;
    toast.setAttribute('role', 'alert');
    toast.id = id;
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${icons[type] || 'bi-info-circle-fill'}"></i>
          <span>${message}</span>
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
      </div>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  function createToastContainer() {
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;';
    document.body.appendChild(div);
    return div;
  }

  // --- Navbar active link ---
  const currentPath = window.location.pathname;
  document.querySelectorAll('#mainNav .nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // --- Auto-dismiss alerts ---
  document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 6000);
  });

  // --- Animate stat numbers ---
  document.querySelectorAll('.stat-number').forEach(el => {
    const target = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
    if (target === 0) return;
    let current = 0;
    const step = Math.ceil(target / 40);
    const suffix = el.textContent.replace(/[0-9,]/g, '');
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString() + suffix;
      if (current >= target) clearInterval(timer);
    }, 30);
  });

  // --- Score bar animation ---
  document.querySelectorAll('.mini-bar-fill, .score-fill').forEach(bar => {
    const width = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => {
      bar.style.width = width;
      bar.style.transition = 'width 0.8s ease';
    }, 300);
  });

});
