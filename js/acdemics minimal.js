// Reveal Animation
window.addEventListener("scroll", revealMinimal);

function revealMinimal() {
  var reveals = document.querySelectorAll(".reveal-minimal");
  for (var i = 0; i < reveals.length; i++) {
    var windowheight = window.innerHeight;
    var revealtop = reveals[i].getBoundingClientRect().top;
    var revealpoint = 150;

    if (revealtop < windowheight - revealpoint) {
      reveals[i].classList.add("active");
    }
  }
}

revealMinimal();

// Tab Functionality
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    // Remove active class from all
    tabButtons.forEach((btn) => btn.classList.remove("active"));
    tabContents.forEach((content) => content.classList.remove("active"));

    // Add active to clicked
    button.classList.add("active");
    const year = button.getAttribute("data-year");
    document
      .querySelector(`.tab-content[data-year="${year}"]`)
      .classList.add("active");
  });
});

// Smooth Scroll for Pills
document.querySelectorAll(".pill").forEach((pill) => {
  pill.addEventListener("click", (e) => {
    e.preventDefault();
    const target = document.querySelector(pill.getAttribute("href"));
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });

      // Update active pill
      document
        .querySelectorAll(".pill")
        .forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
    }
  });
});
