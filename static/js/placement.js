// Animated Counter
function animateCounter() {
  const counters = document.querySelectorAll(".stat-number");

  counters.forEach((counter) => {
    const target = parseFloat(counter.getAttribute("data-target"));
    const increment = target / 100;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        counter.textContent = target;
        clearInterval(timer);
      } else {
        counter.textContent = Math.floor(current * 10) / 10;
      }
    }, 20);
  });
}

// Scroll Reveal
function reveal() {
  const reveals = document.querySelectorAll(".reveal");

  reveals.forEach((element) => {
    const windowHeight = window.innerHeight;
    const elementTop = element.getBoundingClientRect().top;
    const revealPoint = 100;

    if (elementTop < windowHeight - revealPoint) {
      element.classList.add("active");
    }
  });
}

window.addEventListener("scroll", reveal);
window.addEventListener("load", () => {
  reveal();
  animateCounter();
});

// Company Category Filter
document.querySelectorAll(".cat-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".cat-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    const category = btn.getAttribute("data-cat");
    document.querySelectorAll(".company-logo").forEach((logo) => {
      if (
        category === "all" ||
        logo.getAttribute("data-category") === category
      ) {
        logo.style.display = "flex";
      } else {
        logo.style.display = "none";
      }
    });
  });
});

// Year Tabs
document.querySelectorAll(".year-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document
      .querySelectorAll(".year-tab")
      .forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const year = tab.getAttribute("data-year");
    document.querySelectorAll(".year-content").forEach((content) => {
      content.classList.remove("active");
    });
    document.getElementById("year-" + year).classList.add("active");
  });
});

// Alumni Slider
let alumniPosition = 0;

function slideAlumni(direction) {
  const track = document.querySelector(".alumni-track");
  const cards = document.querySelectorAll(".alumni-card");
  const cardWidth = cards[0].offsetWidth + 32; // card width + gap

  alumniPosition += direction;

  if (alumniPosition < 0) {
    alumniPosition = 0;
  }
  if (alumniPosition > cards.length - 3) {
    alumniPosition = cards.length - 3;
  }

  track.style.transform = `translateX(-${alumniPosition * cardWidth}px)`;
}

// Chart.js
const ctx = document.getElementById("chart2024");
if (ctx) {
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["0-5 LPA", "5-10 LPA", "10-15 LPA", "15-20 LPA", "20+ LPA"],
      datasets: [
        {
          label: "Number of Students",
          data: [15, 40, 35, 20, 8],
          backgroundColor: [
            "#a41f13",
            "#c92a1e",
            "#e74c3c",
            "#3498db",
            "#2ecc71",
          ],
          borderWidth: 0,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: "Salary Distribution - 2024 Batch",
          font: {
            size: 16,
            weight: "bold",
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Number of Students",
          },
        },
        x: {
          title: {
            display: true,
            text: "Salary Range",
          },
        },
      },
    },
  });
}

// Button Actions
document.querySelectorAll(".apply-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    alert("Application form will open here! Connect with placement cell.");
  });
});

const downloadBtn = document.querySelector(".download-btn");
if (downloadBtn) {
  downloadBtn.addEventListener("click", () => {
    alert("Resume templates are being downloaded...");
  });
}

const chatbotBtn = document.querySelector(".chatbot-btn");
if (chatbotBtn) {
  chatbotBtn.addEventListener("click", () => {
    alert("Mock interview chatbot will open here!");
  });
}

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
  reveal();
  animateCounter();
});
