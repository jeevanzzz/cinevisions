function switchTab(tab) {
  document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));

  if (tab === "login") {
    document.getElementById("loginForm").classList.add("active");
    document.querySelectorAll(".tab")[0].classList.add("active");
  } else {
    document.getElementById("registerForm").classList.add("active");
    document.querySelectorAll(".tab")[1].classList.add("active");
  }
}

function togglePassword(id) {
  const input = document.getElementById(id);
  input.type = input.type === "password" ? "text" : "password";
}
