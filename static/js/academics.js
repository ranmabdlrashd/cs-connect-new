// Accordion Toggle Function
function toggleAccordion(header) {
  const accordion = header.parentElement;
  accordion.classList.toggle("active");
}

// Scroll Reveal Animation
window.addEventListener("scroll", reveal);

function reveal() {
  var reveals = document.querySelectorAll(".reveal");
  for (var i = 0; i < reveals.length; i++) {
    var windowHeight = window.innerHeight;
    var elementTop = reveals[i].getBoundingClientRect().top;
    var visible = 100;
    if (elementTop < windowHeight - visible) {
      reveals[i].classList.add("active");
    }
  }
}

// Initial reveal on page load
reveal();
