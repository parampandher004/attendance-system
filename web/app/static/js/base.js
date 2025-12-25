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

function toggleStudentFields(value, hiddenInput, selectId) {
  const roleInput = hiddenInput;
  if (!roleInput) {
    console.error("Role hidden input not found.");
    return;
  }

  const role = roleInput.value;
  const fields = document.getElementById("studentFields");

  // Set the display property
  fields.style.display = role === "student" ? "flex" : "none";
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

function updatePeriodStatus(periodId, newStatus) {
  const wrapper = document.getElementById(`status-wrapper-${periodId}`);

  if (!wrapper) {
    console.error("Wrapper not found for period ID:", periodId);
    return;
  }

  const row = wrapper.closest("tr");
  if (!row) {
    console.error("Row not found for period ID:", periodId);
    return;
  }

  // Make the API call to update the status
  fetch(`/api/periods/${periodId}/status`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status: newStatus }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      // Update row class based on new status
      row.className = ""; // Clear existing classes
      row.classList.add("status-" + newStatus.toLowerCase());
      updatePeriods();
    })
    .catch((error) => {
      console.error("Error updating status:", error);
      alert("Failed to update status. Please try again.");
    });
}
function viewPeriodStudents(periodId) {
  fetch(`/api/periods/${periodId}/students`)
    .then((res) => res.json())
    .then((data) => {
      const tbody = document.getElementById("studentAttendanceList");
      tbody.innerHTML = "";
      data.forEach((s) => {
        if (s.status === "present") {
          tbody.innerHTML += `
            <tr>
              <td>${s.roll_no}</td>
              <td>${s.name}</td>
              <td style="color: green">Present</td>
              <td><button class="remove-attendance" onClick="removeAttendance(${s.id}, ${periodId})">
               <svg
                  viewBox="0 0 24 24"
                  fill=none
                  version="1.1"
                  xmlns="http://www.w3.org/2000/svg"
                  xmlns:svg="http://www.w3.org/2000/svg">
                  <path
                    id="rect1"
                    style="stroke-width:0.0194658"
                    transform="rotate(90)"
                    d="m 12,-24 c 1.662,0 3,1.29174 3,2.896277 V -2.8962774 C 15,-1.2917397 13.662,0 12,0 10.338,0 9,-1.2917397 9,-2.8962774 V -21.103723 C 9,-22.70826 10.338,-24 12,-24 Z" />
                </svg> 
              </button></td>
            </tr>
            `;
        } else {
          tbody.innerHTML += `
            <tr>
              <td>${s.roll_no}</td>
              <td>${s.name}</td>
              <td><button class="add-attendance" onClick="addAttendance(${s.id}, ${periodId})">
                <svg
                  viewBox="0 0 24 24"
                  fill=none
                  version="1.1"
                  xmlns="http://www.w3.org/2000/svg"
                  xmlns:svg="http://www.w3.org/2000/svg">
                  <path
                    id="rect1"
                    style="stroke-width:0.0194658"
                    d="M 12 0 C 10.338 -5.6843419e-16 9 1.2917514 9 2.8962891 L 9 9 L 2.8962891 9 C 1.2917514 9 0 10.338 0 12 C -5.6843419e-16 13.662 1.2917514 15 2.8962891 15 L 9 15 L 9 21.103711 C 9 22.708249 10.338 24 12 24 C 13.662 24 15 22.708249 15 21.103711 L 15 15 L 21.103711 15 C 22.708249 15 24 13.662 24 12 C 24 10.338 22.708249 9 21.103711 9 L 15 9 L 15 2.8962891 C 15 1.2917514 13.662 0 12 0 z " />
                  </svg>
                  </button></td>
              <td style="color: red">Absent</td>
            </tr>
            `;
        }
      });
      document.getElementById("periodModal").style.display = "flex";
    });
}
function addAttendance(studentId, periodId) {
  fetch(`/api/periods/${periodId}/students/${studentId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => res.json())
    .then((data) => {
      showToast(data.message, "success");
      viewPeriodStudents(periodId);
    });
}
function removeAttendance(studentId, periodId) {
  fetch(`/api/periods/${periodId}/students/${studentId}`, {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then((data) => {
      showToast(data.message, "success");
      viewPeriodStudents(periodId);
    });
}
function initializeStatusDropdowns() {
  document
    .querySelectorAll('.custom-select-wrapper[id^="status-wrapper-"]')
    .forEach((wrapper) => {
      const periodId = wrapper.id.replace("status-wrapper-", "");

      const buttonId = `statusSelectButton-${periodId}`;
      const listId = `statusOptionsList-${periodId}`;
      const inputId = `statusValue-${periodId}`;

      const statusCallback = (newValue) => {
        if (typeof updatePeriodStatus === "function") {
          updatePeriodStatus(periodId, newValue);
        }
      };

      // This is your original custom dropdown setup function
      setupCustomDropdown(buttonId, listId, inputId, statusCallback);
    });
}
// Function to handle the form submission
function handleAddClassSubmit(event) {
  event.preventDefault(); // Stop the default form submission (page reload)

  const form = event.target;
  const formData = new FormData(form);
  const periodData = Object.fromEntries(formData.entries());

  const modal = document.getElementById("add-class-modal");

  showToast("Saving...", "info", 4000);

  // Debug: Log what's being sent
  console.log("Form data before send:", periodData);

  // Ensure ts_id is present and not empty/undefined
  if (
    !periodData.ts_id ||
    periodData.ts_id === "" ||
    periodData.ts_id === "undefined"
  ) {
    showToast("Please select a subject", "error");
    return;
  }

  // Rename ts_id to teacher_subject_id for backend compatibility
  if (periodData.ts_id) {
    periodData.teacher_subject_id = periodData.ts_id;
    delete periodData.ts_id;
  }

  // 1. Send data to Flask backend
  fetch("/admin/api/periods", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(periodData),
  })
    .then((response) => {
      if (!response.ok) {
        // Check for non-200 status codes
        return response.json().then((err) => {
          throw new Error(err.error || "Failed to add class.");
        });
      }
      return response.json();
    })
    .then((data) => {
      showToast(data.message, "success", 4000);
      updatePeriods();

      // 2. Close the modal after a brief delay
      setTimeout(() => {
        modal.style.display = "none";
      }, 1500);
    })
    .catch((error) => {
      console.error("Error adding class:", error);
      showToast(error.message, "error", 4000);
    });
}

function closePeriodModal() {
  document.getElementById("periodModal").style.display = "none";
}
// The form submission function will be defined in the next step
function updatePeriods() {
  // Guard access to SESSION (may be defined on window later)
  const session =
    typeof window !== "undefined" && window.SESSION ? window.SESSION : {};

  // Skip for admin role - admins don't manage periods
  if (session.role === "admin") {
    return;
  }

  // Determine API URL based on user role
  const apiUrl =
    session.role === "teacher"
      ? "/teacher/api/periods/today"
      : "/student/api/periods/today";

  // If a Tabulator periods table exists, populate it and exit early
  if (
    window.periodsTable &&
    typeof window.periodsTable.setData === "function"
  ) {
    fetch(apiUrl)
      .then((response) => response.json())
      .then((data) => {
        try {
          window.periodsTable.setData(data);
        } catch (err) {
          console.error("Error setting periods Tabulator data:", err);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch periods for Tabulator:", err);
        try {
          window.periodsTable.clearData();
        } catch (err) {
          console.error("Error clearing periods Tabulator data:", err);
        }
      });
    return;
  }

  // --- Fallback: original DOM-table update (teacher/student without Tabulator) ---
  const table = document.getElementById("periods-table");
  const tbody = document.getElementById("periods-body");
  const noPeriodsMessage = document.getElementById("no-periods-message");

  if (!tbody || !noPeriodsMessage || !table) {
    return;
  }

  tbody.innerHTML = "";
  noPeriodsMessage.style.display = "none";

  fetch(apiUrl)
    .then((response) => response.json())
    .then((data) => {
      if (data.length > 0) {
        table.style.display = "table";
        if (SESSION.role === "teacher") {
          data.forEach((period) => {
            let row = document.createElement("tr");
            row.classList.add("status-" + (period.status || "").toLowerCase());

            row.innerHTML = `
            <td>${period.class_name || ""}</td>
            <td>${period.subject_name || ""}</td>
            <td>${period.start_time || ""}</td>
            <td>${period.end_time || ""}</td>
            <td style="overflow: visible;">
              <div class="custom-select-wrapper" id="status-wrapper-${
                period.id
              }">
                <input type="hidden" name="status-${
                  period.id
                }" id="statusValue-${period.id}" value="${
              period.status || ""
            }" />

                <div class="custom-select" id="statusSelectButton-${period.id}">
                  ${period.status || ""}
                  <span class="select-arrow">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
                    </svg>
                  </span>
                </div>

                <ul class="options-list" id="statusOptionsList-${period.id}">
                  <li class="option-item" data-value="scheduled">Scheduled</li>
                  <li class="option-item" data-value="running">Running</li>
                  <li class="option-item" data-value="completed">Completed</li>
                  <li class="option-item" data-value="cancelled">Cancelled</li>
                </ul>
              </div>
            </td>
          `;
            if (
              period.status &&
              (period.status.toLowerCase() === "running" ||
                period.status.toLowerCase() === "completed")
            ) {
              row.innerHTML += `
              <td>
                <svg
                  width="24"
                  height="24"
                  class="view-students"
                  viewBox="0 0 6.3499999 6.3499999"
                  fill="none"
                  onClick="viewPeriodStudents(${period.id})"
                >
                  <path
                    id="rect2"
                    style="fill-opacity: 1; stroke-width: 0.278307"
                    d="M 1.9905633,4.5649819e-4 C 1.8262455,-0.00615141 1.6524289,0.05902133 1.5182407,0.19320962 1.2796837,0.43176659 1.2595679,0.79546623 1.4727654,1.0086637 l 2.164209,2.164209 -2.164209,2.1642089 C 1.2595679,5.5502791 1.2796836,5.9139787 1.5182407,6.1525358 1.7567976,6.3910927 2.1204973,6.4117253 2.3336948,6.1985278 L 4.9738437,3.5583789 C 5.1401298,3.3920927 5.1640316,3.1341312 5.0534253,2.915524 5.0290986,2.859759 4.994519,2.8085586 4.9495557,2.7635953 L 2.3336947,0.1477344 C 2.2404209,0.05446051 2.1183659,0.00559597 1.9905633,4.5649819e-4 Z"
                    />
                </svg>
              </td>
            `;
            } else {
              row.innerHTML += "<td></td>";
            }
            tbody.appendChild(row);
          });
          initializeStatusDropdowns();
          setTableDataLabels("periods-table");
        } else if (SESSION.role === "student") {
          data.forEach((period) => {
            let row = document.createElement("tr");
            row.classList.add("status-" + (period.status || "").toLowerCase());
            row.innerHTML = `
              <td>${period.subject_name || ""}</td>
              <td>${period.start_time || ""}</td>
              <td>${period.end_time || ""}</td>
              <td>${(period.status || "").toUpperCase()}</td>
            `;
            tbody.appendChild(row);
          });
          setTableDataLabels("periods-table");
        } else if (SESSION.role === "admin") {
          data.forEach((period) => {
            let row = document.createElement("tr");
            row.classList.add("status-" + (period.status || "").toLowerCase());
            row.innerHTML = `
            <td>${period.class_name || ""}</td>
            <td>${period.subject_name || ""}</td>
            <td>${period.teacher_name || ""}</td>
            <td>${period.start_time || ""}</td>
            <td>${period.end_time || ""}</td>
            <td style="overflow: visible;">
              <div class="custom-select-wrapper" id="status-wrapper-${
                period.id
              }">
                <input type="hidden" name="status-${
                  period.id
                }" id="statusValue-${period.id}" value="${
              period.status || ""
            }" />

                <div class="custom-select" id="statusSelectButton-${period.id}">
                  ${period.status || ""}
                  <span class="select-arrow">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
                    </svg>
                  </span>
                </div>

                <ul class="options-list" id="statusOptionsList-${period.id}">
                  <li class="option-item" data-value="scheduled">Scheduled</li>
                  <li class="option-item" data-value="running">Running</li>
                  <li class="option-item" data-value="completed">Completed</li>
                  <li class="option-item" data-value="cancelled">Cancelled</li>
                </ul>
              </div>
            </td>
          `;
            if (
              period.status &&
              (period.status.toLowerCase() === "running" ||
                period.status.toLowerCase() === "completed")
            ) {
              row.innerHTML += `
              <td>
                <svg
                  width="24"
                  height="24"
                  class="view-students"
                  viewBox="0 0 6.3499999 6.3499999"
                  fill="none"
                  onClick="viewPeriodStudents(${period.id})"
                >
                  <path
                    id="rect2"
                    style="fill-opacity: 1; stroke-width: 0.278307"
                    d="M 1.9905633,4.5649819e-4 C 1.8262455,-0.00615141 1.6524289,0.05902133 1.5182407,0.19320962 1.2796837,0.43176659 1.2595679,0.79546623 1.4727654,1.0086637 l 2.164209,2.164209 -2.164209,2.1642089 C 1.2595679,5.5502791 1.2796836,5.9139787 1.5182407,6.1525358 1.7567976,6.3910927 2.1204973,6.4117253 2.3336948,6.1985278 L 4.9738437,3.5583789 C 5.1401298,3.3920927 5.1640316,3.1341312 5.0534253,2.915524 5.0290986,2.859759 4.994519,2.8085586 4.9495557,2.7635953 L 2.3336947,0.1477344 C 2.2404209,0.05446051 2.1183659,0.00559597 1.9905633,4.5649819e-4 Z"
                    />
                </svg>
              </td>
            `;
            } else {
              row.innerHTML += "<td></td>";
            }
            tbody.appendChild(row);
          });
          initializeStatusDropdowns();
          setTableDataLabels("periods-table");
        }
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
function closeModal() {
  document.getElementById("studentModal").style.display = "none";
}
function setTableDataLabels(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;
  const ths = table.querySelectorAll("thead th");
  const headers = Array.from(ths).map((th) => th.textContent.trim());
  table.querySelectorAll("tbody tr").forEach((row) => {
    Array.from(row.children).forEach((td, i) => {
      if (headers[i] !== "") td.setAttribute("data-label", headers[i] || "");
    });
  });
}

function updateStudent(value, hiddenInput, selectId) {
  if (selectId === "classStudents") {
    const class_id = value;
    console.log("Selected class ID:", class_id);

    const student_id = console.log("Student ID:", student_id);
    fetch(`/api/students/${student_id}/class`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ class_id: class_id }),
    })
      .then((res) => res.json())
      .then((data) => {
        hiddenInput.value = data;
      });
  }
}
function handleStudentEnroll(e) {
  const btn = e.target.closest(".enroll-btn");
  if (!btn) return;
  const studentId = btn.getAttribute("data-id") || btn.dataset.id;
  const classId = btn.getAttribute("data-class-id") || btn.dataset.classId;

  // Ensure we have a student id
  if (!studentId) return console.error("No student id found for enroll");

  fetch("/admin/api/student/enroll", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId, class_id: classId }),
  })
    .then((res) => {
      if (!res.ok) throw new Error("Enroll failed");
      return res.json();
    })
    .then((data) => {
      showToast(data.message || "Enrolled", "success");
      // remove the student card from pending list if present
      const card = btn.closest(".student-card");
      if (card) card.remove();
    })
    .catch((err) => {
      console.error(err);
      showToast("Enroll failed", "error");
    });
}
function handleStudentReject(e) {
  const btn = e.target.closest(".reject-btn");
  if (!btn) return;
  const studentId = btn.getAttribute("data-id") || btn.dataset.id;
  if (!studentId) return console.error("No student id found for reject");

  fetch("/admin/api/student/reject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId }),
  })
    .then((res) => {
      if (!res.ok) throw new Error("Reject failed");
      return res.json();
    })
    .then((data) => {
      showToast(data.message || "Rejected", "success");
      const card = btn.closest(".student-card");
      if (card) card.remove();
    })
    .catch((err) => {
      console.error(err);
      showToast("Reject failed", "error");
    });
}

function viewStudentImages(studentId, studentName) {
  // Store current student ID for later use
  window.currentStudentId = studentId;
  window.currentStudentName = studentName;

  // Open the images modal
  const imagesModal = document.getElementById("imagesModal");
  imagesModal.style.display = "flex";
  document.getElementById(
    "imagesModalTitle"
  ).textContent = `${studentName}'s Images`;

  // Load student images data
  loadStudentImages(studentId);
}

function loadStudentImages(studentId) {
  const loadingIndicator = document.getElementById("imagesLoadingIndicator");
  const imagesList = document.getElementById("imagesList");

  loadingIndicator.style.display = "block";
  imagesList.innerHTML = "";

  fetch(`/admin/api/students/${studentId}/images`)
    .then((res) => res.json())
    .then((data) => {
      loadingIndicator.style.display = "none";

      // Update stats
      document.getElementById("totalImagesCount").textContent =
        data.total_images;
      document.getElementById("encodedImagesCount").textContent =
        data.encoded_images;

      // Populate images list
      if (data.images.length === 0) {
        imagesList.innerHTML =
          '<tr><td colspan="3" style="text-align: center; padding: 1rem; color: var(--text-muted)">No images yet</td></tr>';
        return;
      }

      imagesList.innerHTML = data.images
        .map(
          (img) => `
        <tr>
          <td>${img.file_name}</td>
          <td>
            <span style="padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem; ${
              img.has_encoding
                ? "background: var(--success); color: white"
                : "background: var(--warning); color: white"
            }">
              ${img.has_encoding ? "✓ Yes" : "✗ No"}
            </span>
          </td>
          <td>
            <button onclick="deleteStudentImage(${studentId}, ${
            img.id
          })" style="background: var(--danger); color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer">Delete</button>
          </td>
        </tr>
      `
        )
        .join("");
    })
    .catch((err) => {
      loadingIndicator.style.display = "none";
      imagesList.innerHTML =
        '<tr><td colspan="3" style="text-align: center; color: var(--danger)">Failed to load images</td></tr>';
      console.error("Error loading student images:", err);
    });
}

function closeImagesModal() {
  const imagesModal = document.getElementById("imagesModal");
  imagesModal.style.display = "none";
}

function closeImageViewerModal() {
  const imageViewerModal = document.getElementById("imageViewerModal");
  imageViewerModal.style.display = "none";
}

function handleAddImages() {
  // Open upload modal for adding images
  if (window.currentStudentId) {
    const uploadModal = document.getElementById("uploadModal");
    uploadModal.style.display = "flex";
    document.getElementById("studentIdInput").value = window.currentStudentId;
    document.getElementById("uploadModalTitle").textContent =
      window.currentStudentName;

    const uploadModalClose = document.getElementById("closeUploadModal");
    uploadModalClose.onclick = () => {
      uploadModal.style.display = "none";
      // Refresh images list after upload
      loadStudentImages(window.currentStudentId);
    };
  }
}

function handleGenerateEncodings() {
  if (!window.currentStudentId) {
    showToast("No student selected", "error");
    return;
  }

  const loadingIndicator = document.getElementById("imagesLoadingIndicator");
  loadingIndicator.style.display = "block";

  fetch(`/admin/api/students/${window.currentStudentId}/generate-encodings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => {
      if (!res.ok) {
        return res.json().then((err) => {
          throw new Error(err.error || "Failed to generate encodings");
        });
      }
      return res.json();
    })
    .then((data) => {
      loadingIndicator.style.display = "none";

      if (data.error) {
        showToast(`Error: ${data.error}`, "error");
        console.error("Encoding error details:", data);
      } else {
        showToast(data.message, "success");
        // Reload images to update encoding status
        loadStudentImages(window.currentStudentId);
      }

      if (data.errors && data.errors.length > 0) {
        console.warn("Encoding warnings:", data.errors);
      }
    })
    .catch((err) => {
      loadingIndicator.style.display = "none";
      showToast(`Error: ${err.message}`, "error");
      console.error("Error generating encodings:", err);
    });
}

function handleShowImages() {
  if (!window.currentStudentId) {
    showToast("No student selected", "error");
    return;
  }

  fetch(`/admin/api/students/${window.currentStudentId}/images`)
    .then((res) => res.json())
    .then((data) => {
      if (data.images.length === 0) {
        showToast("No images to display", "info");
        return;
      }

      // Create a simple gallery viewer
      const imageViewerModal = document.getElementById("imageViewerModal");
      const imageViewerImg = document.getElementById("imageViewerImg");
      const imageViewerName = document.getElementById("imageViewerName");

      // Store all images for gallery navigation
      window.currentImageGallery = data.images;
      window.currentImageIndex = 0;

      // Display first image
      displayImageInGallery(0);
      imageViewerModal.style.display = "flex";
    })
    .catch((err) => {
      showToast("Failed to load images", "error");
      console.error("Error loading images:", err);
    });
}

function displayImageInGallery(index) {
  if (!window.currentImageGallery || window.currentImageGallery.length === 0)
    return;

  const image = window.currentImageGallery[index];
  // Use the server endpoint to get the image with proper authentication
  const imageUrl = `/admin/api/students/${window.currentStudentId}/images/${image.id}/view`;

  const imgElement = document.getElementById("imageViewerImg");

  // Clear previous image
  imgElement.src = "";
  imgElement.alt = "Loading...";

  // Set up error handler
  imgElement.onerror = () => {
    imgElement.alt = "Failed to load image";
    imgElement.style.backgroundColor = "#f0f0f0";
    showToast(`Failed to load image: ${image.file_name}`, "warning");
  };

  imgElement.onload = () => {
    imgElement.style.backgroundColor = "transparent";
  };

  // Set source
  imgElement.src = imageUrl;

  document.getElementById("imageViewerName").textContent = `${
    image.file_name
  } (${index + 1}/${window.currentImageGallery.length})`;

  // Show navigation buttons if multiple images
  const prevBtn = document.getElementById("imageNavPrev");
  const nextBtn = document.getElementById("imageNavNext");

  if (prevBtn && nextBtn) {
    prevBtn.style.display =
      window.currentImageGallery.length > 1 ? "block" : "none";
    nextBtn.style.display =
      window.currentImageGallery.length > 1 ? "block" : "none";
  }
}

function prevImage() {
  if (!window.currentImageGallery) return;
  window.currentImageIndex =
    (window.currentImageIndex - 1 + window.currentImageGallery.length) %
    window.currentImageGallery.length;
  displayImageInGallery(window.currentImageIndex);
}

function nextImage() {
  if (!window.currentImageGallery) return;
  window.currentImageIndex =
    (window.currentImageIndex + 1) % window.currentImageGallery.length;
  displayImageInGallery(window.currentImageIndex);
}

function deleteStudentImage(studentId, imageId) {
  if (!confirm("Are you sure you want to delete this image?")) {
    return;
  }

  fetch(`/admin/api/students/${studentId}/images/${imageId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        showToast(`Error: ${data.error}`, "error");
      } else {
        showToast(data.message, "success");
        loadStudentImages(studentId);
      }
    })
    .catch((err) => {
      showToast("Failed to delete image", "error");
      console.error("Error deleting image:", err);
    });
}

function toggleTeacherPanel(button) {
  const panel = document.getElementById("teacher-panel");
  const expandBtn = button;

  if (panel.style.display === "none") {
    panel.style.display = "block";
    setTimeout(() => {
      panel.classList.add("active");
    }, 10);
    expandBtn.classList.add("active");
  } else {
    panel.classList.remove("active");
    expandBtn.classList.remove("active");
    setTimeout(() => {
      panel.style.display = "none";
    }, 300);
  }
}

function assignTeacherToSubject() {
  const teacherId = document.getElementById("value-teacherSelect").value;
  if (!teacherId) {
    showToast("Please select a teacher", "error");
    return;
  }

  const classId = document.getElementById("value-teacherClass").value;
  const subjectId = document.getElementById("value-teacherSubject").value;

  if (!classId || !subjectId) {
    showToast("Please select both class and subject", "error");
    return;
  }

  fetch(`/api/teachers/${teacherId}/assign`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      class_id: classId,
      subject_id: subjectId,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      showToast(data.message, "success");
      // Optionally refresh the page or remove the assigned teacher
      setTimeout(() => location.reload(), 1500);
    })
    .catch((error) => {
      console.error("Error assigning teacher:", error);
      showToast("Failed to assign teacher", "error");
    });
}
