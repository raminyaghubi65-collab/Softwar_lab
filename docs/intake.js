(() => {
  const form = document.querySelector("#intake-form");
  if (!form) return;
  const status = document.querySelector("#intake-status");
  const submit = form.querySelector('button[type="submit"]');
  const apiBase = (window.SOFTWARE_QA_INTAKE_API || "").trim().replace(/\/$/, "");
  const fileInput = form.querySelector('input[type="file"]');
  const maxBytes = 20 * 1024 * 1024;

  if (!apiBase || !/^https:\/\//i.test(apiBase)) {
    submit.disabled = true;
    status.textContent = "Secure file upload is not active yet. Please contact us first; do not email sensitive files.";
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "";
    const file = fileInput.files[0];
    if (!file) {
      status.textContent = "Please choose one project file.";
      return;
    }
    if (file.size > maxBytes) {
      status.textContent = "The maximum file size is 20 MiB.";
      return;
    }
    submit.disabled = true;
    submit.textContent = "Uploading securely…";
    try {
      const response = await fetch(apiBase + "/api/intake", {
        method: "POST",
        body: new FormData(form),
        mode: "cors",
        credentials: "omit",
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.detail || "Upload failed. Please try again later.");
      status.textContent = "File received. Reference: " + result.id + ". We will contact you by email.";
      form.reset();
    } catch (error) {
      status.textContent = error.message || "Upload failed. Please contact us.";
    } finally {
      submit.disabled = false;
      submit.textContent = "Submit project securely";
    }
  });
})();
