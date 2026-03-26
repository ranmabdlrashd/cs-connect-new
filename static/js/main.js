// ===================================
// CS CONNECT - SHARED UTILITIES
// Used on all pages via base.html
// ===================================

// 1. SCROLL REVEAL ANIMATION
function reveal() {
  const reveals = document.querySelectorAll(".reveal");
  reveals.forEach((el) => {
    const top = el.getBoundingClientRect().top;
    if (top < window.innerHeight - 150) {
      el.classList.add("active");
    }
  });
}

window.addEventListener("scroll", reveal);
reveal(); // Trigger once on page load

// 2. STATS COUNTER (home page)
document.addEventListener("DOMContentLoaded", () => {
  const statsSection = document.querySelector(".stats-strip");
  if (!statsSection) return;

  const animateCounters = () => {
    document.querySelectorAll(".stat-number[data-target]").forEach((counter) => {
      const updateCount = () => {
        const target = +counter.getAttribute("data-target");
        const count = +counter.innerText;
        const inc = target / 200;
        if (count < target) {
          counter.innerText = Math.ceil(count + inc);
          setTimeout(updateCount, 20);
        } else {
          counter.innerText = target;
        }
      };
      updateCount();
    });
  };

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      animateCounters();
      observer.disconnect();
    }
  }, { threshold: 0.5 });

  observer.observe(statsSection);
});

// 3. MOBILE HAMBURGER NAVIGATION TOGGLE
function toggleNav() {
  const navLinks = document.getElementById("navLinks");
  const hamburger = document.getElementById("hamburger");
  if (!navLinks) return;
  navLinks.classList.toggle("nav-open");
  hamburger && hamburger.classList.toggle("is-open");
}

// Close nav when a link is clicked on mobile
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".nav-center a").forEach(link => {
    link.addEventListener("click", () => {
      const navLinks = document.getElementById("navLinks");
      const hamburger = document.getElementById("hamburger");
      if (navLinks) navLinks.classList.remove("nav-open");
      if (hamburger) hamburger.classList.remove("is-open");
    });
  });
});

/**
 * DASHBOARD SIDEBAR TOGGLE (Mobile)
 */
function toggleSidebar() {
  const wrapper = document.querySelector('.dash-wrapper');
  if (wrapper) wrapper.classList.toggle('sidebar-open');
}

