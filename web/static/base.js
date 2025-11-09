function studentUpdatePeriods() {
  const table = document.getElementById("periods-table");
  const tbody = document.getElementById("periods-body");
  const noPeriodsMessage = document.getElementById("no-periods-message");

  tbody.innerHTML = "";
  noPeriodsMessage.style.display = "none";

  fetch("/api/periods/today")
    .then((response) => response.json())
    .then((data) => {
      if (data.length > 0) {
        table.style.display = "table";
        data.forEach((period) => {
          let row = document.createElement("tr");
          row.classList.add("status-" + period.status.toLowerCase());
          row.innerHTML = `
              <td>${period.subject_name}</td>
              <td>${period.start_time}</td>
              <td>${period.end_time}</td>
              <td>${period.status.toUpperCase()}</td>
            `;
          tbody.appendChild(row);
        });
      } else {
        noPeriodsMessage.style.display = "block";
      }
    })
    .catch((error) => {
      noPeriodsMessage.textContent =
        "Error fetching periods. Please try again later.";
      noPeriodsMessage.style.display = "block";
    });
}

function showToast(message, category = "info", duration = 4000) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${category}`;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}
function toggleDarkMode() {
  if (document.documentElement.getAttribute("data-theme") === "dark") {
    document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem("theme", "light");
    return;
  } else if (document.documentElement.getAttribute("data-theme") === "light") {
    document.documentElement.setAttribute("data-theme", "dark");
    localStorage.setItem("theme", "dark");
    return;
  }
}

// --- Custom Dropdown Setup Function ---
function setupCustomDropdown(buttonId, listId, inputId, callback = null) {
  const button = document.getElementById(buttonId);
  const list = document.getElementById(listId);
  const hiddenInput = document.getElementById(inputId);
  const wrapper = button.closest(".custom-select-wrapper");

  if (!button || !list || !hiddenInput) return;

  // Toggle Dropdown Visibility
  button.addEventListener("click", (e) => {
    e.stopPropagation();

    // Close all other open dropdowns
    document.querySelectorAll(".options-list.show").forEach((openlist) => {
      if (openlist !== list) {
        openlist.classList.remove("show");
        openlist.previousElementSibling.classList.remove("active");
      }
    });

    // Toggle this dropdown
    list.classList.toggle("show");
    button.classList.toggle("active");
  });

  // Handle Option Selection
  list.querySelectorAll(".option-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      const value = e.target.getAttribute("data-value");
      const text = e.target.textContent;

      // 1. Update the visual button text
      button.textContent = text;
      // 2. Add the custom arrow back
      button.innerHTML += `<span class="select-arrow">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/></svg>
                        </span>`;

      // 3. Update the hidden input
      hiddenInput.value = value;

      // 4. Close the dropdown
      list.classList.remove("show");
      button.classList.remove("active");

      // 5. Execute custom callback function (e.g., toggle fields)
      if (callback) {
        callback(value);
      }
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (!wrapper.contains(e.target)) {
      list.classList.remove("show");
      button.classList.remove("active");
    }
  });
}

function loadSection(sectionName) {
  fetch(`/api/${sectionName}`)
    .then((response) => response.text())
    .then((html) => {
      document.getElementById("main").innerHTML = html;
    });
}

function loadSectionScript(sectionName) {
  const script = document.createElement("script");
  script.src = `/static/js/${sectionName}.js`;
  script.dataset.section = sectionName;
  document.body.appendChild(script);
}
