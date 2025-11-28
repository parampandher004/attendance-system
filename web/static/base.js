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

  // 1. Send data to Flask backend
  fetch("/api/classes", {
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
        if (SESSION.role === "teacher") {
          data.forEach((period) => {
            let row = document.createElement("tr");
            row.classList.add("status-" + period.status.toLowerCase());

            row.innerHTML = `
            <td>${period.class_name}</td>
            <td>${period.subject_name}</td>
            <td>${period.start_time}</td>
            <td>${period.end_time}</td>
            <td style="overflow: visible;">
              <div class="custom-select-wrapper" id="status-wrapper-${period.id}">
                <input type="hidden" name="status-${period.id}" id="statusValue-${period.id}" value="${period.status}" />

                <div class="custom-select" id="statusSelectButton-${period.id}">
                  ${period.status}
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
              period.status.toLowerCase() === "running" ||
              period.status.toLowerCase() === "completed"
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
            row.classList.add("status-" + period.status.toLowerCase());
            row.innerHTML = `
              <td>${period.subject_name}</td>
              <td>${period.start_time}</td>
              <td>${period.end_time}</td>
              <td>${period.status.toUpperCase()}</td>
            `;
            tbody.appendChild(row);
          });
          setTableDataLabels("periods-table");
        } else if (SESSION.role === "admin") {
          data.forEach((period) => {
            let row = document.createElement("tr");
            row.classList.add("status-" + period.status.toLowerCase());
            row.innerHTML = `
            <td>${period.class_name}</td>
            <td>${period.subject_name}</td>
            <td>${period.teacher_name}</td>
            <td>${period.start_time}</td>
            <td>${period.end_time}</td>
            <td style="overflow: visible;">
              <div class="custom-select-wrapper" id="status-wrapper-${period.id}">
                <input type="hidden" name="status-${period.id}" id="statusValue-${period.id}" value="${period.status}" />

                <div class="custom-select" id="statusSelectButton-${period.id}">
                  ${period.status}
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
              period.status.toLowerCase() === "running" ||
              period.status.toLowerCase() === "completed"
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
  const studentId = e.target.getAttribute("data-id");
  const classId = e.target.getAttribute("data-class-id");
  fetch(`/api/students/${studentId}/enroll`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ class_id: classId }),
  });
}
function handleStudentReject(e) {
  const studentId = e.target.getAttribute("data-id");
  fetch(`/api/students/${studentId}/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function viewStudentImages(studentId, studentName) {
  const uploadModal = document.getElementById("uploadModal");
  uploadModal.style.display = "flex";

  uploadModal.querySelector("#studentIdInput").value = studentId;
  uploadModal.querySelector("#uploadModalTitle").textContent = studentName;
  const uploadModalClose = document.getElementById("closeUploadModal");
  uploadModalClose.onclick = () => (uploadModal.style.display = "none");

  window.onclick = (e) => {
    if (e.target == uploadModal) uploadModal.style.display = "none";
  };

  // fetch(`/api/students/${studentId}/images`)
  //   .then((res) => res.json())
  //   .then((data) => {
  //     const tbody = document.getElementById("studentImageList");
  //     tbody.innerHTML = "";
  //     data.forEach((image) => {
  //       tbody.innerHTML += `
  //         <tr>
  //           <td><img src="${image}" alt="Student Image" /></td>
  //         </tr>
  //       `;
  //     });
  //     document.getElementById("studentImageModal").style.display = "flex";
  //   });
}
