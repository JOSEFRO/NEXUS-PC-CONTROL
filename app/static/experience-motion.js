(() => {
  "use strict";
  const sections = document.querySelectorAll("main>section");
  if (!("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add("nx-reveal","is-in-view");
      observer.unobserve(entry.target);
    }
  }), {threshold:.08});
  sections.forEach(section => { section.classList.add("nx-reveal"); observer.observe(section); });
})();