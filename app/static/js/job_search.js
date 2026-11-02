/**
 * Job search live-search and filter JavaScript
 */
document.addEventListener('DOMContentLoaded', function () {
  // Debounced keyword search
  const searchInput = document.querySelector('input[name="q"]');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        // Submit form for server-side search
      }, 600);
    });
  }
});
