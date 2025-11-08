window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const msg = params.get("msg");
  const type = params.get("type"); // expected: "success", "danger", "info", etc.

  if (msg && type) {
    // Create alert div
    const alert = document.createElement("div");
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = "alert";

    // Add message text
    alert.textContent = msg;

    // Add close button
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "btn-close";
    closeBtn.setAttribute("data-bs-dismiss", "alert");
    closeBtn.setAttribute("aria-label", "Close");

    alert.appendChild(closeBtn);

    // Insert alert at top of main content
    const container = document.querySelector(".content") || document.body;
    container.prepend(alert);

    // Auto-close after 3 seconds using Bootstrap API
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close(); // triggers proper fade-out animation
    }, 3000);
  }
});

