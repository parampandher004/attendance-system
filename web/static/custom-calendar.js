document.addEventListener("DOMContentLoaded", () => {
  // Find all calendar wrappers on the page and initialize each one.
  const calendarWrappers = document.querySelectorAll(".calendar-wrapper");
  calendarWrappers.forEach(initializeCalendar);
});

/**
 * Initializes a single calendar component.
 * @param {HTMLElement} wrapper - The main container element for a calendar instance.
 */
function initializeCalendar(wrapper) {
  const dateInput = wrapper.querySelector(".date-input");
  const calendarEl = wrapper.querySelector(".calendar-container");
  const monthYearEl = wrapper.querySelector(".month-year");
  const calendarGrid = wrapper.querySelector(".calendar-grid");
  const prevMonthBtn = wrapper.querySelector(".prev-month-btn");
  const nextMonthBtn = wrapper.querySelector(".next-month-btn");
  const dayInput = wrapper.querySelector(".day-input"); // Hidden input for the day name

  if (
    !dateInput ||
    !calendarEl ||
    !monthYearEl ||
    !calendarGrid ||
    !prevMonthBtn ||
    !nextMonthBtn
  ) {
    console.error("A calendar instance is missing required elements.", wrapper);
    return;
  }

  const today = new Date();
  let currentMonth = today.getMonth();
  let currentYear = today.getFullYear();

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const dayNames = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];

  // Renders the calendar grid for the given month and year
  function renderCalendar(month, year) {
    monthYearEl.textContent = `${monthNames[month]} ${year}`;
    calendarGrid.innerHTML = `
      <div class="day-label">Sun</div><div class="day-label">Mon</div><div class="day-label">Tue</div>
      <div class="day-label">Wed</div><div class="day-label">Thu</div><div class="day-label">Fri</div>
      <div class="day-label">Sat</div>
    `;

    const firstDayOfMonth = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    for (let i = 0; i < firstDayOfMonth; i++) {
      calendarGrid.insertAdjacentHTML(
        "beforeend",
        '<div class="day-cell empty"></div>'
      );
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dayCell = document.createElement("div");
      dayCell.className = "day-cell";
      dayCell.textContent = day;

      if (
        day === today.getDate() &&
        month === today.getMonth() &&
        year === today.getFullYear()
      ) {
        dayCell.classList.add("today");
      }

      dayCell.addEventListener("click", () => selectDate(day, month, year));
      calendarGrid.appendChild(dayCell);
    }
  }

  // Handles the selection of a date
  function selectDate(day, month, year) {
    const selectedDate = new Date(year, month, day);
    const dateString = `${String(day).padStart(2, "0")}/${String(
      month + 1
    ).padStart(2, "0")}/${year}`;

    dateInput.value = dateString;
    if (dayInput) {
      dayInput.value = dayNames[selectedDate.getDay()];
    }

    calendarEl.classList.remove("show");

    // Trigger a custom event that other scripts can listen for
    dateInput.dispatchEvent(
      new CustomEvent("dateSelected", { detail: { date: dateString } })
    );
  }

  // Navigates the calendar
  function changeMonth(direction) {
    currentMonth += direction;
    if (currentMonth > 11) {
      currentMonth = 0;
      currentYear++;
    } else if (currentMonth < 0) {
      currentMonth = 11;
      currentYear--;
    }
    renderCalendar(currentMonth, currentYear);
  }

  // --- Event Listeners ---
  dateInput.addEventListener("click", (e) => {
    e.stopPropagation();
    // Hide all other open calendars before showing this one
    document.querySelectorAll(".calendar-container.show").forEach((cal) => {
      if (cal !== calendarEl) cal.classList.remove("show");
    });
    calendarEl.classList.toggle("show");
  });

  prevMonthBtn.addEventListener("click", () => changeMonth(-1));
  nextMonthBtn.addEventListener("click", () => changeMonth(1));

  renderCalendar(currentMonth, currentYear);
}

/**
 * Resets a calendar instance to its default state.
 * Clears the date input and any associated hidden inputs.
 * @param {HTMLElement} wrapper - The main container element for the calendar instance to reset.
 */
function resetCalendar(wrapper) {
  const dateInput = wrapper.querySelector(".date-input");
  const dayInput = wrapper.querySelector(".day-input");

  if (dateInput) {
    dateInput.value = ""; // Clear the visible input
  }

  if (dayInput) {
    dayInput.value = ""; // Clear the hidden day name input
  }

  // Trigger the custom event with an empty date detail.
  // This allows filter functions to react and show all data.
  if (dateInput) {
    dateInput.dispatchEvent(
      new CustomEvent("dateSelected", { detail: { date: "" } })
    );
  }
}

// Global listener to close any open calendar when clicking outside
document.addEventListener("click", (e) => {
  const openCalendar = document.querySelector(".calendar-container.show");
  if (openCalendar && !openCalendar.parentElement.contains(e.target)) {
    openCalendar.classList.remove("show");
  }
});
