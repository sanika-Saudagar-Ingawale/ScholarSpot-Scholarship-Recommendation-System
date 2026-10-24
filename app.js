document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("menuToggle");
  const nav = document.getElementById("navLinks");
  if (toggle && nav) toggle.addEventListener("click", () => nav.classList.toggle("open"));

  document.querySelectorAll(".flash-close").forEach(button => {
    button.addEventListener("click", () => button.closest(".flash").remove());
  });

  const filterToggle = document.getElementById("filterToggle");
  const filters = document.getElementById("filtersPanel");
  if (filterToggle && filters) filterToggle.addEventListener("click", () => filters.classList.toggle("show"));

  const filterForm = document.getElementById("filterForm");
  if (filterForm) {
    filterForm.querySelectorAll("select").forEach(select => {
      select.addEventListener("change", () => filterForm.requestSubmit());
    });
  }

  const password = document.getElementById("password");
  const confirmPassword = document.getElementById("confirm_password");
  if (password && confirmPassword) {
    confirmPassword.addEventListener("input", () => {
      confirmPassword.setCustomValidity(
        confirmPassword.value && password.value !== confirmPassword.value
          ? "Passwords do not match." : ""
      );
    });
    password.addEventListener("input", () => {
      confirmPassword.setCustomValidity(
        confirmPassword.value && password.value !== confirmPassword.value
          ? "Passwords do not match." : ""
      );
    });
  }
});
