// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });

      // Close mobile menu if open
      if (window.innerWidth <= 768) {
        navMenu.classList.remove("active");
        document.body.style.overflow = "";
      }
    }
  });
});

// Mobile menu toggle
const hamburger = document.getElementById("hamburger");
const navMenu = document.getElementById("nav-menu");

if (hamburger) {
  hamburger.addEventListener("click", () => {
    navMenu.classList.toggle("active");

    // Prevent body scroll when menu is open
    if (navMenu.classList.contains("active")) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    // Animate hamburger
    hamburger.classList.toggle("active");
  });
}

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
  const currentScroll = window.pageYOffset;

  if (currentScroll <= 0) {
    navbar.style.boxShadow = "0 4px 6px -1px rgba(0, 0, 0, 0.1)";
  } else {
    navbar.style.boxShadow = "0 10px 30px -10px rgba(0, 0, 0, 0.5)";
  }

  lastScroll = currentScroll;
});

// Intersection Observer for fade-in animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -100px 0px",
};

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = "1";
      entry.target.style.transform = "translateY(0)";
    }
  });
}, observerOptions);

// Observe all sections and cards
document
  .querySelectorAll("section, .project-card, .highlight-card, .timeline-item")
  .forEach(el => {
    el.style.opacity = "0";
    el.style.transform = "translateY(30px)";
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
    observer.observe(el);
  });

// Active nav link highlighting
const sections = document.querySelectorAll("section[id]");
const navLinks = document.querySelectorAll(".nav-link");

function highlightNavLink() {
  let current = "";

  sections.forEach(section => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.clientHeight;
    if (pageYOffset >= sectionTop - 100) {
      current = section.getAttribute("id");
    }
  });

  navLinks.forEach(link => {
    link.classList.remove("active");
    if (link.getAttribute("href") === `#${current}`) {
      link.classList.add("active");
    }
  });
}

window.addEventListener("scroll", highlightNavLink);

// Dynamic stats counter animation
function animateCounter(element, target, duration = 2000) {
  let start = 0;
  const increment = target / (duration / 16);

  const timer = setInterval(() => {
    start += increment;
    if (start >= target) {
      element.textContent = target.toLocaleString();
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(start).toLocaleString();
    }
  }, 16);
}

// Initialize counters when cinema section is in view
const cinemaSection = document.getElementById("cinema");
let countersAnimated = false;

const cinemaObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !countersAnimated) {
        const totalMovies = document.getElementById("total-movies");
        const avgRating = document.getElementById("avg-rating");
        const totalRuntime = document.getElementById("total-runtime");
        const countries = document.getElementById("countries");

        if (totalMovies) animateCounter(totalMovies, 2282);
        if (totalRuntime) animateCounter(totalRuntime, 4872);

        // Animate rating with decimal
        if (avgRating) {
          let start = 0;
          const target = 8.2;
          const increment = target / 100;

          const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
              avgRating.textContent = target.toFixed(1);
              clearInterval(timer);
            } else {
              avgRating.textContent = start.toFixed(1);
            }
          }, 20);
        }

        if (countries) {
          countries.textContent = "95+";
        }

        countersAnimated = true;
      }
    });
  },
  { threshold: 0.5 }
);

if (cinemaSection) {
  cinemaObserver.observe(cinemaSection);
}

// Parallax effect for hero section
const hero = document.querySelector(".hero");

if (hero) {
  window.addEventListener("scroll", () => {
    const scrolled = window.pageYOffset;
    hero.style.transform = `translateY(${scrolled * 0.5}px)`;
  });
}

// Loading animation
window.addEventListener("load", () => {
  document.body.classList.add("loaded");
});

// Add typing effect to hero title
const heroTitle = document.querySelector(".hero-title .highlight");
if (heroTitle) {
  const text = heroTitle.textContent;
  heroTitle.textContent = "";
  let i = 0;

  function typeWriter() {
    if (i < text.length) {
      heroTitle.textContent += text.charAt(i);
      i++;
      setTimeout(typeWriter, 100);
    }
  }

  setTimeout(typeWriter, 500);
}

// Easter egg: Konami code
let konamiCode = [
  "ArrowUp",
  "ArrowUp",
  "ArrowDown",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "ArrowLeft",
  "ArrowRight",
  "b",
  "a",
];
let konamiIndex = 0;

document.addEventListener("keydown", e => {
  if (e.key === konamiCode[konamiIndex]) {
    konamiIndex++;
    if (konamiIndex === konamiCode.length) {
      activateEasterEgg();
      konamiIndex = 0;
    }
  } else {
    konamiIndex = 0;
  }
});

function activateEasterEgg() {
  const originalBg = document.body.style.background;
  document.body.style.background =
    "linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3)";
  document.body.style.backgroundSize = "400% 400%";
  document.body.style.animation = "rainbow 3s ease infinite";

  const style = document.createElement("style");
  style.textContent = `
        @keyframes rainbow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
    `;
  document.head.appendChild(style);

  setTimeout(() => {
    document.body.style.background = originalBg;
    document.body.style.animation = "";
    style.remove();
  }, 5000);

  console.log(
    "ðŸŽ‰ You found the Easter egg! Louise appreciates your curiosity!"
  );
}

// Project link handlers
document.querySelectorAll(".project-link, .feature-link").forEach(link => {
  link.addEventListener("click", e => {
    if (link.getAttribute("href") === "#") {
      e.preventDefault();
      alert(
        "This project page is coming soon! Stay tuned for detailed documentation and live demos."
      );
    }
  });
});

// Add current year to footer
const yearElement = document.querySelector(".footer-content p");
if (yearElement) {
  const currentYear = new Date().getFullYear();
  yearElement.textContent = yearElement.textContent.replace(
    "2025",
    currentYear
  );
}

// Console message
console.log(
  "%cðŸ‘‹ Hello, curious developer!",
  "font-size: 20px; font-weight: bold; color: #8B5CF6;"
);
console.log(
  "%cThis website was built with love by Louise Ferreira",
  "font-size: 14px; color: #CBD5E1;"
);
console.log(
  "%cTech stack: HTML, CSS, JavaScript, Python",
  "font-size: 12px; color: #94A3B8;"
);
console.log(
  "%cInterested in collaboration? Reach out at louisesfer@gmail.com",
  "font-size: 12px; color: #10B981;"
);
