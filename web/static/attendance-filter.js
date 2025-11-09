document.addEventListener("DOMContentLoaded", () => {
  // Listen for date selection on the student filter calendar
  const stFilterDateInput = document.getElementById("stFilterDateInput");
  if (stFilterDateInput) {
    stFilterDateInput.addEventListener("dateSelected", (e) => {
      // Call your filter function when a date is selected
      studentApplyFilters(e.detail.date, null, "st_date_filter");
    });
  }
});
