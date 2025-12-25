// Initialize window.config based on window.SESSION when available.
// Use safe checks for window.SESSION to avoid ReferenceError when SESSION isn't defined yet.
(function () {
  const role =
    typeof window !== "undefined" && window.SESSION && window.SESSION.role
      ? window.SESSION.role
      : "admin";

  const adminIndices = {
    class: 0,
    name: 1,
    roll_no: 2,
    date: 3,
    subject: 4,
    day: 5,
    status: 6,
  };
  const teacherIndices = {
    name: 0,
    roll_no: 1,
    date: 2,
    subject: 3,
    day: 4,
    status: 5,
  };
  const studentIndices = { date: 0, subject: 1, day: 2, status: 3 };

  if (typeof window !== "undefined") {
    if (role === "admin") window.config = { COL_INDICES: adminIndices };
    else if (role === "teacher")
      window.config = { COL_INDICES: teacherIndices };
    else if (role === "student")
      window.config = { COL_INDICES: studentIndices };
    else window.config = { COL_INDICES: adminIndices };
  }
})();

/**
 * Executes the filtering based on a configuration object.
 * This function is defined only once and used everywhere.
 * @param {object} config - Configuration including table ID and column indices.
 */
function applyFilters(value, hiddenInput, selectId) {
  // If Tabulator is active (student dashboard), apply filters to it
  if (window.studentAttendanceTable) {
    const subjectHidden = document.getElementById("value-subject_filter");
    const dayHidden = document.getElementById("value-day_filter");
    const statusHidden = document.getElementById("value-status_filter");
    const dateValue =
      selectId === "date_filter"
        ? value
        : document.getElementById("filterDateInput")
        ? document.getElementById("filterDateInput").value
        : "";

    const subjectVal = subjectHidden
      ? subjectHidden.value.trim().toLowerCase()
      : "";
    const dayVal = dayHidden ? dayHidden.value.trim().toLowerCase() : "";
    const statusVal = statusHidden
      ? statusHidden.value.trim().toLowerCase()
      : "";
    const dateVal = dateValue ? String(dateValue).trim() : "";

    // Combined filter function for Tabulator
    window.studentAttendanceTable.setFilter((data) => {
      if (subjectVal) {
        if (
          !data.subject ||
          !String(data.subject).toLowerCase().includes(subjectVal)
        )
          return false;
      }
      if (dayVal) {
        if (!data.day || String(data.day).toLowerCase() !== dayVal)
          return false;
      }
      if (statusVal) {
        if (!data.status || String(data.status).toLowerCase() !== statusVal)
          return false;
      }
      if (dateVal) {
        if (!data.date || String(data.date).trim() !== String(dateVal).trim())
          return false;
      }
      return true;
    });

    return; // Tabulator handled filtering
  }

  // --- Fallback: native table filtering (teacher/admin dashboards) ---
  const attendanceTableBody = document.querySelector("#attendance-table tbody");

  if (!attendanceTableBody) return;

  const defaultAdmin = {
    class: 0,
    name: 1,
    roll_no: 2,
    date: 3,
    subject: 4,
    day: 5,
    status: 6,
  };
  const defaultTeacher = {
    name: 0,
    roll_no: 1,
    date: 2,
    subject: 3,
    day: 4,
    status: 5,
  };
  const defaultStudent = { date: 0, subject: 1, day: 2, status: 3 };

  const role =
    typeof window !== "undefined" && window.SESSION && window.SESSION.role
      ? window.SESSION.role
      : "admin";
  const COL_INDICES =
    window.config && window.config.COL_INDICES
      ? window.config.COL_INDICES
      : role === "teacher"
      ? defaultTeacher
      : role === "student"
      ? defaultStudent
      : defaultAdmin;

  if (selectId === "subject_filter") {
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
    return;
  } else if (selectId === "class_filter") {
    const classValue = value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const classText = row.cells[COL_INDICES.class].innerText
        .trim()
        .toLowerCase();
      row.style.display = !classValue || classText === classValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  } else if (selectId === "student_filter") {
    const nameValue = value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const nameText = row.cells[COL_INDICES.name].innerText
        .trim()
        .toLowerCase();
      row.style.display = !nameValue || nameText === nameValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  } else if (selectId === "date_filter") {
    const dateValue = value;

    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));

    rows.forEach((row) => {
      if (row.cells.length < COL_INDICES.status + 1) return;
      const dateText = row.cells[COL_INDICES.date].innerText.trim();
      row.style.display = !dateValue || dateText === dateValue ? "" : "none";
    });
    return; // Early return since we handled filtering here
  } else if (selectId === "status_filter") {
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
  } else if (selectId === "day_filter") {
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

  if (attendanceTableBody) {
    const rows = Array.from(attendanceTableBody.getElementsByTagName("tr"));
    rows.forEach((row) => {
      row.style.display = "";
    });
  }

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
      resetDropdown(wrapper);
    });

  // If Tabulator is active, clear its filters too
  if (
    window.studentAttendanceTable &&
    typeof window.studentAttendanceTable.clearFilter === "function"
  ) {
    window.studentAttendanceTable.clearFilter(true);
  }
}

function resetDropdown(wrapper) {
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
  if (selectElement.id === "genderSelect") {
    const customSelectButton = document.getElementById("button-genderSelect");
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
        const enrollBtn = wrapper
          .closest(".student-card")
          .querySelector(".enroll-btn");
        if (enrollBtn) enrollBtn.setAttribute("data-class-id", value);
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
    if (
      select.closest("#add-class-modal") ||
      select.closest("#teacher-panel")
    ) {
      return;
    }
    let callback = null;

    if (
      select.id === "class_filter" ||
      select.id === "student_filter" ||
      select.id === "status_filter" ||
      select.id === "subject_filter" ||
      select.id === "date_filter" ||
      select.id === "day_filter"
    ) {
      callback = applyFilters;
    } else if (select.id === "roleSelect") {
      callback = toggleStudentFields;
    } else if (select.classList.contains("teacher-class-select")) {
      callback = (value, hiddenInput, selectId) => {
        const teacherId = hiddenInput
          .closest(".teacher-assignment-card")
          .getAttribute("data-teacher-id");
        updateTeacherSubjectDropdown(teacherId, value);
      };
    }
    transformSelectToCustomDropdown(select, callback);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initializeAllCustomDropdowns();
});
