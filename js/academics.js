// Accordion Toggle Function
function toggleAccordion(header) {
  const content = header.nextElementSibling;
  const icon = header.querySelector(".accordion-icon");

  // Close all other accordions
  document.querySelectorAll(".accordion-content").forEach((item) => {
    if (item !== content) {
      item.classList.remove("active");
      item.previousElementSibling.classList.remove("active");
    }
  });

  // Toggle current accordion
  content.classList.toggle("active");
  header.classList.toggle("active");
}

// Scroll Reveal Animation (if not already in main.js)
window.addEventListener("scroll", reveal);

function reveal() {
  var reveals = document.querySelectorAll(".reveal");
  for (var i = 0; i < reveals.length; i++) {
    var windowheight = window.innerHeight;
    var revealtop = reveals[i].getBoundingClientRect().top;
    var revealpoint = 150;

    if (revealtop < windowheight - revealpoint) {
      reveals[i].classList.add("active");
    }
  }
}

// Trigger on page load
reveal();

// Smooth scroll to syllabus section
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});
