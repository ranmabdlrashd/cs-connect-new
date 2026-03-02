// Search Functionality
const searchInput = document.getElementById("searchInput");
searchInput.addEventListener("input", (e) => {
  const search = e.target.value.toLowerCase();
  document.querySelectorAll(".faculty-card").forEach((card) => {
    const name = card.querySelector("h3").textContent.toLowerCase();
    card.style.display = name.includes(search) ? "block" : "none";
  });
});

// Filter Functionality
document.querySelectorAll(".filter-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".filter-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const filter = btn.getAttribute("data-filter");
    document.querySelectorAll(".faculty-card").forEach((card) => {
      if (filter === "all") {
        card.classList.remove("hidden");
      } else {
        card.getAttribute("data-designation") === filter
          ? card.classList.remove("hidden")
          : card.classList.add("hidden");
      }
    });
  });
});

// Scroll Reveal
function reveal() {
  document.querySelectorAll(".reveal").forEach((el) => {
    const top = el.getBoundingClientRect().top;
    const windowHeight = window.innerHeight;
    if (top < windowHeight - 100) el.classList.add("active");
  });
}
window.addEventListener("scroll", reveal);
reveal();

// View Profile Button
document.querySelectorAll(".view-profile-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    alert("Detailed profile page will open here!");
  });
});
