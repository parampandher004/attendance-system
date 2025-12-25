function createTimePicker(hourId, minuteId, hiddenId) {
  const hourSelect = document.getElementById(hourId);
  const minuteSelect = document.getElementById(minuteId);
  const hiddenInput = document.getElementById(hiddenId);

  if (!hourSelect || !minuteSelect || !hiddenInput) {
    console.error(
      `Failed to initialize time picker: Missing elements for IDs ${hourId}, ${minuteId}, or ${hiddenId}`
    );
    return;
  }

  // --- 1. Populate Dropdowns ---

  // Populate Hours (00 to 23)
  for (let i = 0; i < 24; i++) {
    const hour = String(i).padStart(2, "0");
    const option = document.createElement("option");
    option.value = hour;
    option.textContent = hour;
    hourSelect.appendChild(option);
  }

  // Populate Minutes (00 to 59, in 5-minute increments)
  for (let i = 0; i < 60; i += 5) {
    const minute = String(i).padStart(2, "0");
    const option = document.createElement("option");
    option.value = minute;
    option.textContent = minute;
    minuteSelect.appendChild(option);
  }

  // --- 2. Logic to Update Hidden Input ---

  function updateHiddenTimeValue() {
    const hour = hourSelect.value;
    const minute = minuteSelect.value;
    const timeString = `${hour}:${minute}`;

    // Set the final value for the form submission
    hiddenInput.value = timeString;
  }

  // --- 3. Initial Setup and Event Listeners ---

  // Set initial values based on the hidden input's default value
  const initialValue = hiddenInput.value || "00:00";
  const [initialHour, initialMinute] = initialValue.split(":");

  // Ensure initial values exist in the dropdowns before setting
  if (hourSelect.querySelector(`option[value="${initialHour}"]`)) {
    hourSelect.value = initialHour;
  }
  if (minuteSelect.querySelector(`option[value="${initialMinute}"]`)) {
    minuteSelect.value = initialMinute;
  }

  // Add listeners
  hourSelect.addEventListener("change", updateHiddenTimeValue);
  minuteSelect.addEventListener("change", updateHiddenTimeValue);

  // Ensure the hidden input is correctly initialized on load
  updateHiddenTimeValue();
}

/**
 * Master Initialization Function
 * Finds all time picker wrappers and initializes them.
 */
function initializeAllTimePickers() {
  const wrappers = document.querySelectorAll(".js-time-picker");

  wrappers.forEach((wrapper) => {
    const hourId = wrapper.dataset.hourId;
    const minuteId = wrapper.dataset.minuteId;
    const hiddenId = wrapper.dataset.hiddenId;

    // Use the factory function to create each instance
    createTimePicker(hourId, minuteId, hiddenId);
  });
}

// Run the master initialization function when the DOM is ready
document.addEventListener("DOMContentLoaded", initializeAllTimePickers);
