    document.addEventListener('DOMContentLoaded', function () {
        // Get references to the elements
        const employerCheckbox = document.getElementById('employer-checkbox');
        const companyField = document.getElementById('company-field');

        // Add an event listener to the checkbox
        employerCheckbox.addEventListener('change', function () {
            if (this.checked) {
                // If checked, show the company field
                companyField.style.display = 'block';
                companyField.required = true; // Make it required
            } else {
                // If unchecked, hide it
                companyField.style.display = 'none';
                companyField.required = false; // Make it not required
                companyField.value = ''; // Clear the value
            }
        });
    });