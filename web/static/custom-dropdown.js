const teacherConfig = {
  COL_INDICES: {
    name: 0,
    roll_no: 1,
    date: 2,
    subject: 3,
    day: 4,
    status: 5,
  },
};

function teacherApplyFilters(value, hiddenInput, selectId) {
  applyFilters(value, hiddenInput, selectId, teacherConfig);
}

const studentConfig = {
  COL_INDICES: {
    date: 0,
    subject: 1,
    day: 2,
    status: 3,
  },
};

function studentApplyFilters(value, hiddenInput, selectId) {
  applyFilters(value, hiddenInput, selectId, studentConfig);
}

/**
 * Executes the filtering based on a configuration object.
 * This function is defined only once and used everywhere.
 * @param {object} config - Configuration including table ID and column indices.
 */
function applyFilters(value, hiddenInput, selectId, config) {
  const attendanceTableBody = document.querySelector("#attendance-table tbody");

  if (!attendanceTableBody) return;

  const COL_INDICES = config.COL_INDICES;

  if (selectId === "subject_filter" || selectId === "st_subject_filter") {
    const subjectFilter = hiddenInput;
    const subjectValue = subjectFilter.value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const subjectText = row.cells[COL_INDICES.subject].innerText
        .trim()
        .toLowerCase();
      row.style.display =
        !subjectValue || subjectText === subjectValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  } else if (selectId === "date_filter" || selectId === "st_date_filter") {
    const dateValue = value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const dateText = row.cells[COL_INDICES.date].innerText.trim();
      row.style.display = !dateValue || dateText === dateValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  } else if (selectId === "status_filter" || selectId === "st_status_filter") {
    const statusFilter = hiddenInput;
    const statusValue = statusFilter.value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const statusText = row.cells[COL_INDICES.status].innerText
        .trim()
        .toLowerCase();
      row.style.display =
        !statusValue || statusText === statusValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  } else if (selectId === "day_filter" || selectId === "st_day_filter") {
    const dayFilter = hiddenInput;
    const dayValue = dayFilter.value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const dayText = row.cells[COL_INDICES.day].innerText.trim().toLowerCase();
      row.style.display = !dayValue || dayText === dayValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  }
}

function resetFilters(containerID) {
  const filterContainer = document.getElementById(containerID);

  if (!filterContainer) return;

  const tableId = filterContainer.getAttribute("data-table-id");
  const attendanceTableBody = document.querySelector(`#${tableId} tbody`);

  if (!attendanceTableBody) return;

  const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

  rows.forEach((row) => {
    row.style.display = "";
  });

  // 1. Reset standard input fields (like date)
  filterContainer.querySelectorAll('input[type="date"]').forEach((input) => {
    input.value = "";
  });

  filterContainer.querySelectorAll(".calendar-wrapper").forEach((wrapper) => {
    if (typeof resetCalendar === "function") {
      resetCalendar(wrapper);
    }
  });

  // 2. Reset custom dropdowns
  filterContainer
    .querySelectorAll(".custom-select-wrapper")
    .forEach((wrapper) => {
      const hiddenInput = wrapper.querySelector('input[type="hidden"]');
      const button = wrapper.querySelector(".custom-select");
      const firstOption = wrapper.querySelector(".option-item"); // The first li is the default

      if (hiddenInput && button && firstOption) {
        // Set the hidden input value to the default (empty)
        hiddenInput.value = firstOption.getAttribute("data-value") || "";

        // Set the button text to the default
        button.textContent = firstOption.textContent;

        // Re-add the arrow icon
        button.innerHTML += `<span class="select-arrow">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/></svg>
                           </span>`;
      }
    });
}

/**
 * Transforms a native <select> element into the custom HTML dropdown structure.
 * @param {HTMLSelectElement} selectElement The native <select> element to transform.
 * @param {function(string, HTMLInputElement): void} [callback] An optional function to run on option selection.
 */
function transformSelectToCustomDropdown(selectElement, callback = null) {
  if (!selectElement || selectElement.tagName !== "SELECT") {
    console.error("Invalid element provided. Must be a <select> tag.");
    return;
  }

  const selectId =
    selectElement.id ||
    `custom-select-${Math.random().toString(36).substring(2, 9)}`;

  // Check for the initial selected option's value and text
  const initialValue = selectElement.value;
  const selectedIndex =
    selectElement.selectedIndex !== -1 ? selectElement.selectedIndex : 0;
  const initialText = selectElement.options[selectedIndex].textContent;

  // --- 1. BUILD THE NEW HTML STRUCTURE ---
  const wrapper = document.createElement("div");
  // Add the z-index fix to the wrapper for proper stacking

  wrapper.className = "custom-select-wrapper relative z-10";
  wrapper.id = `wrapper-${selectId}`;
  const arrowSvg = `
                 <span class="select-arrow">
                     <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                         <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
                     </svg>
                 </span>`;

  // The entire inner structure as a string
  let htmlContent = `
                 <input type="hidden" name="${
                   selectElement.name || selectId
                 }" id="value-${selectId}" value="${initialValue}" />
                 <div class="custom-select" id="button-${selectId}">
                     ${initialText}
                     ${arrowSvg}
                 </div>
                 <ul class="options-list" id="list-${selectId}">
             `;

  // Add list items from <option> elements
  Array.from(selectElement.options).forEach((option) => {
    htmlContent += `<li class="option-item" data-value="${option.value}">${option.textContent}</li>`;
  });

  htmlContent += `</ul>`;
  wrapper.innerHTML = htmlContent;

  // --- 2. REPLACE AND INITIALIZE ---
  selectElement.parentNode.replaceChild(wrapper, selectElement);

  // Get references to the new elements
  const button = document.getElementById(`button-${selectId}`);
  const list = document.getElementById(`list-${selectId}`);
  const hiddenInput = document.getElementById(`value-${selectId}`);

  if (selectElement.id === "roleSelect") {
    const customSelectButton = document.getElementById("button-roleSelect");
    customSelectButton.className += " input";
  }

  // Call your existing setup logic using the new references
  setupCustomDropdownLogic(button, list, hiddenInput, callback, selectId);
}

/**
 * Common logic for all custom dropdowns. Handles toggling, selection, and callbacks.
 */
function setupCustomDropdownLogic(
  button,
  list,
  hiddenInput,
  callback = null,
  selectId
) {
  const wrapper = button.closest(".custom-select-wrapper");

  // ----------------------------------------------------
  // --- PART 1: Toggle Dropdown Visibility ---
  // ----------------------------------------------------
  button.addEventListener("click", (e) => {
    e.stopPropagation();

    // Close all other open dropdowns
    document.querySelectorAll(".options-list.show").forEach((openlist) => {
      // Check if the current button is the one being clicked
      if (openlist !== list) {
        openlist.classList.remove("show");
        // The element preceding the list is the button div
        const siblingButton = openlist.previousElementSibling;
        if (siblingButton) siblingButton.classList.remove("active");
      }
    });

    // Toggle this dropdown
    list.classList.toggle("show");
    button.classList.toggle("active");
  });

  // ----------------------------------------------------
  // --- PART 2: Handle Option Selection ---
  // ----------------------------------------------------
  list.querySelectorAll(".option-item").forEach((item) => {
    item.addEventListener("click", (e) => {
      const value = e.target.getAttribute("data-value");
      const text = e.target.textContent;

      if (wrapper.id.startsWith("wrapper-classStudents")) {
        wrapper
          .closest(".student-card")
          .querySelector("#enroll-btn")
          .setAttribute("data-class-id", value);
      }

      // Only update and execute if the value actually changed
      if (hiddenInput.value !== value) {
        // 1. Update the hidden input
        hiddenInput.value = value;

        // 2. Execute custom callback (this is your onchange equivalent!)
        if (callback) {
          // Pass the new value AND the hidden input (for context)
          callback(value, hiddenInput, selectId);
        }
      }

      // 3. Update the visual button text and re-add arrow
      button.textContent = text;
      button.innerHTML += `<span class="select-arrow">
                                                 <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/></svg>
                                             </span>`;

      // 4. Close the dropdown
      list.classList.remove("show");
      button.classList.remove("active");
    });
  });

  // Close dropdowns if clicking outside (this handles the global document click)
  document.addEventListener("click", (e) => {
    if (!wrapper.contains(e.target)) {
      list.classList.remove("show");
      button.classList.remove("active");
    }
  });
}

/**
 * Finds all native select elements marked for custom styling and transforms them.
 */
function initializeAllCustomDropdowns() {
  document.querySelectorAll("select.js-custom-dropdown").forEach((select) => {
    if (select.closest("#add-class-modal")) {
      return;
    }
    let callback = null;

    if (
      select.id === "status_filter" ||
      select.id === "subject_filter" ||
      select.id === "date_filter" ||
      select.id === "day_filter"
    ) {
      callback = teacherApplyFilters;
    } else if (
      select.id === "st_status_filter" ||
      select.id === "st_subject_filter" ||
      select.id === "st_date_filter" ||
      select.id === "st_day_filter"
    ) {
      callback = studentApplyFilters;
    } else if (select.id === "roleSelect") {
      callback = toggleStudentFields;
    }
    transformSelectToCustomDropdown(select, callback);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initializeAllCustomDropdowns();
});
