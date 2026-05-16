/* Minimal JS for navigation, smooth scroll, and footer year */
document.addEventListener('DOMContentLoaded', function () {
  // Mobile nav toggle
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');

  navToggle && navToggle.addEventListener('click', function () {
    navMenu.classList.toggle('show');
  });

  // Close nav when a link is clicked (mobile)
  document.querySelectorAll('#nav-menu a').forEach(a => {
    a.addEventListener('click', () => navMenu.classList.remove('show'));
  });

  // Smooth scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href.length > 1) {
        e.preventDefault();
        const el = document.querySelector(href);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Insert current year in footer
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Small accessibility: close nav on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') navMenu.classList.remove('show');
  });
});

