// ===================================
// FACULTY PAGE JAVASCRIPT
// ===================================

// Scroll Reveal Animation
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

// ===================================
// FACULTY FILTER FUNCTIONALITY
// ===================================
const filterButtons = document.querySelectorAll(".filter-btn");
const facultyCards = document.querySelectorAll(".faculty-card");
const searchInput = document.getElementById("facultySearch");
const noResults = document.getElementById("noResults");

// Filter by designation
filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    // Remove active class from all buttons
    filterButtons.forEach((btn) => btn.classList.remove("active"));
    // Add active class to clicked button
    button.classList.add("active");

    const filterValue = button.getAttribute("data-filter");

    let visibleCount = 0;

    facultyCards.forEach((card) => {
      const category = card.getAttribute("data-category");

      if (filterValue === "all" || category === filterValue) {
        card.style.display = "block";
        visibleCount++;
      } else {
        card.style.display = "none";
      }
    });

    // Show/hide no results message
    noResults.style.display = visibleCount === 0 ? "block" : "none";
  });
});

// Search functionality
searchInput.addEventListener("input", (e) => {
  const searchTerm = e.target.value.toLowerCase();
  let visibleCount = 0;

  facultyCards.forEach((card) => {
    const name = card.querySelector("h3").textContent.toLowerCase();
    const tags = Array.from(card.querySelectorAll(".tag"))
      .map((tag) => tag.textContent.toLowerCase())
      .join(" ");
    const subjects = card.querySelector(".faculty-details")
      ? card.querySelector(".faculty-details").textContent.toLowerCase()
      : "";

    const matchesSearch =
      name.includes(searchTerm) ||
      tags.includes(searchTerm) ||
      subjects.includes(searchTerm);

    // Check if card matches current filter
    const activeFilter = document
      .querySelector(".filter-btn.active")
      .getAttribute("data-filter");
    const category = card.getAttribute("data-category");
    const matchesFilter = activeFilter === "all" || category === activeFilter;

    if (matchesSearch && matchesFilter) {
      card.style.display = "block";
      visibleCount++;
    } else {
      card.style.display = "none";
    }
  });

  // Show/hide no results message
  noResults.style.display = visibleCount === 0 ? "block" : "none";
});

// ===================================
// PROFILE MODAL FUNCTIONALITY
// ===================================

// Faculty data (in real application, this would come from a database)
const facultyData = {
  faculty1: {
    name: "Dr. Arun Kumar",
    designation: "Professor",
    photo:
      "https://via.placeholder.com/400x450/8F7A6E/FFFFFF?text=Dr.+A.+Kumar",
    qualification:
      "Ph.D. in Computer Science (IIT Delhi), M.Tech CSE, B.Tech CSE",
    experience: "18 Years",
    subjects: [
      "Data Structures",
      "Algorithms",
      "Theory of Computation",
      "Compiler Design",
    ],
    research:
      "Machine Learning, Artificial Intelligence, Data Mining, Pattern Recognition, Neural Networks",
    publications: 38,
    achievements: [
      "Best Paper Award at ICML 2024",
      "IEEE Senior Member",
      "Guest Editor for International Journal of AI",
      "Principal Investigator for 5 funded research projects",
    ],
    email: "arun.kumar@aisat.ac.in",
    phone: "+91 98765 43211",
    officeHours: "Monday to Friday: 10:00 AM - 12:00 PM",
    scholarLink: "#",
    orcidLink: "#",
  },
  faculty2: {
    name: "Dr. Priya Sharma",
    designation: "Associate Professor",
    photo:
      "https://via.placeholder.com/400x450/8F7A6E/FFFFFF?text=Dr.+P.+Sharma",
    qualification:
      "Ph.D. in Computer Science (NIT Calicut), M.Tech CSE, B.E. CSE",
    experience: "12 Years",
    subjects: [
      "Database Management Systems",
      "Cloud Computing",
      "Big Data Analytics",
      "NoSQL Databases",
    ],
    research:
      "Cloud Computing, Big Data, Internet of Things, Distributed Systems, Edge Computing",
    publications: 28,
    achievements: [
      "DST Research Grant of ₹25 Lakhs",
      "Published in top-tier conferences (IEEE, ACM)",
      "Expert reviewer for international journals",
      "Industry collaboration with Amazon AWS",
    ],
    email: "priya.sharma@aisat.ac.in",
    phone: "+91 98765 43212",
    officeHours: "Tuesday to Thursday: 2:00 PM - 4:00 PM",
    scholarLink: "#",
    orcidLink: "#",
  },
  // Add more faculty data as needed
};

function openProfileModal(facultyId) {
  const modal = document.getElementById("profileModal");
  const modalBody = document.getElementById("modalBody");
  const faculty = facultyData[facultyId];

  if (!faculty) return;

  modalBody.innerHTML = `
        <div class="profile-detail">
            <div class="profile-header-modal">
                <img src="${faculty.photo}" alt="${faculty.name}">
                <div>
                    <h2>${faculty.name}</h2>
                    <p class="modal-designation">${faculty.designation}</p>
                </div>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-graduation-cap"></i> Qualification</h3>
                <p>${faculty.qualification}</p>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-briefcase"></i> Experience</h3>
                <p>${faculty.experience} in Academia and Research</p>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-book-open"></i> Subjects Handled</h3>
                <ul class="subjects-list">
                    ${faculty.subjects.map((subject) => `<li>${subject}</li>`).join("")}
                </ul>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-flask"></i> Research Interests</h3>
                <p>${faculty.research}</p>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-trophy"></i> Key Achievements</h3>
                <ul class="achievements-list">
                    ${faculty.achievements.map((achievement) => `<li>${achievement}</li>`).join("")}
                </ul>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-chart-line"></i> Publications</h3>
                <p><strong>${faculty.publications}+</strong> publications in reputed international journals and conferences</p>
                <div class="profile-links">
                    <a href="${faculty.scholarLink}" class="profile-link-btn">
                        <i class="fab fa-google"></i> Google Scholar
                    </a>
                    <a href="${faculty.orcidLink}" class="profile-link-btn">
                        <i class="fab fa-orcid"></i> ORCID Profile
                    </a>
                </div>
            </div>
            
            <div class="profile-section">
                <h3><i class="far fa-clock"></i> Office Hours</h3>
                <p>${faculty.officeHours}</p>
            </div>
            
            <div class="profile-section">
                <h3><i class="fas fa-envelope"></i> Contact Information</h3>
                <p><strong>Email:</strong> <a href="mailto:${faculty.email}">${faculty.email}</a></p>
                <p><strong>Phone:</strong> <a href="tel:${faculty.phone}">${faculty.phone}</a></p>
            </div>
        </div>
    `;

  modal.classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeProfileModal() {
  const modal = document.getElementById("profileModal");
  modal.classList.remove("active");
  document.body.style.overflow = "auto";
}

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeProfileModal();
  }
});
