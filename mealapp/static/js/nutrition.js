function debugElement(element, label) {
    console.log('DEBUG ' + label + ':');
    console.log('  - tagName:', element.tagName);
    console.log('  - name:', element.name);
    console.log('  - value:', element.value);
    console.log('  - HTML:', element.outerHTML);
}


document.addEventListener("DOMContentLoaded", function () {
    const calculateButton = document.getElementById("calculate-nutrition");
    const servingsInput = document.querySelector("input[name='servings']");

    if (calculateButton) {
        calculateButton.addEventListener("click", calculateNutrition);
    }

    // Add listeners to ingredient inputs to update nutrition when they change
    document.addEventListener("click", function(e) {
        if (e.target && e.target.matches("button[type='button'][onclick*='addIngredientRow']")) {
            // Add listeners to new ingredient rows after they're created
            setTimeout(addListenersToIngredientRows, 100);
        }
    });

    // Initialize listeners for existing ingredient rows
    addListenersToIngredientRows();

    function addListenersToIngredientRows() {
        const ingredientInputs = document.querySelectorAll(".ingredient-row input, .ingredient-row select");
        ingredientInputs.forEach(input => {
            if (!input.dataset.hasListener) {
                input.addEventListener("change", function() {
                    if (calculateButton && calculateButton.dataset.autoCalculate === "true") {
                        calculateNutrition();
                    }
                });
                input.dataset.hasListener = "true";
            }
        });
    }

function calculateNutrition() {
    const ingredientRows = document.querySelectorAll(".ingredient-row");
    console.log("Found " + ingredientRows.length + " ingredient rows");

    // Debug each row's structure
    ingredientRows.forEach((row, index) => {
        console.log(`Row ${index + 1} HTML:`, row.outerHTML);

        const nameInput = row.querySelector("[name='ingredient_name[]']");
        const amountInput = row.querySelector("[name='ingredient_amount[]']");
        const unitSelect = row.querySelector("[name='ingredient_unit[]']");

        if (nameInput) debugElement(nameInput, `Row ${index + 1} Name Input`);
        else console.log(`Row ${index + 1}: No name input found`);

        if (amountInput) debugElement(amountInput, `Row ${index + 1} Amount Input`);
        else console.log(`Row ${index + 1}: No amount input found`);

        if (unitSelect) debugElement(unitSelect, `Row ${index + 1} Unit Select`);
        else console.log(`Row ${index + 1}: No unit select found`);
    });
        const caloriesInput = document.getElementById("calories");
        const proteinInput = document.getElementById("protein");
        const carbsInput = document.getElementById("carbs");
        const fatInput = document.getElementById("fat");
        const servings = parseInt(servingsInput?.value || 1);

        // Reset totals
        let totalCalories = 0;
        let totalProtein = 0;
        let totalCarbs = 0;
        let totalFat = 0;

        // Show calculating state
        if (caloriesInput) caloriesInput.value = "Calculating...";
        if (proteinInput) proteinInput.value = "Calculating...";
        if (carbsInput) carbsInput.value = "Calculating...";
        if (fatInput) fatInput.value = "Calculating...";

        // Debug info
        console.log("Starting nutrition calculation with " + ingredientRows.length + " ingredients");

        const promises = Array.from(ingredientRows).map((row, index) => {
            const nameInput = row.querySelector("[name='ingredient_name[]']");
            const amountInput = row.querySelector("[name='ingredient_amount[]']");
            const unitSelect = row.querySelector("[name='ingredient_unit[]']");

            if (!nameInput || !amountInput || !unitSelect) {
                console.warn("Ingredient row " + index + " is missing required fields");
                return Promise.resolve();
            }

            const ingredientName = nameInput.value.trim();
            const amount = parseFloat(amountInput.value) || 0;
            const unit = unitSelect.value;

            // Debug info - log each ingredient we're processing
            console.log(`Processing ingredient #${index + 1}: ${amount} ${unit} of ${ingredientName}`);

            if (ingredientName && amount && unit) {
                // Use the API with unit conversion - make sure to include unit parameter
                const url = `/api/ingredient/${encodeURIComponent(ingredientName)}/?amount=${amount}&unit=${encodeURIComponent(unit)}`;
                console.log("Fetching nutrition from: " + url);

                return fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            totalCalories += data.calories;
                            totalProtein += data.protein;
                            totalCarbs += data.carbs;
                            totalFat += data.fat;

                            // Debug output
                            console.log(`${ingredientName}: ${amount} ${unit} → ${data.converted_amount} ${data.base_unit}`);
                            console.log(`  Calories: ${data.calories}, Protein: ${data.protein}, Carbs: ${data.carbs}, Fat: ${data.fat}`);
                        } else {
                            console.warn(`Error for ${ingredientName}: ${data.error}`);
                        }
                    })
                    .catch(error => {
                        console.error(`Network error for ${ingredientName}:`, error);
                    });
            } else {
                console.warn(`Skipping incomplete ingredient: ${ingredientName} (amount: ${amount}, unit: ${unit})`);
                return Promise.resolve();
            }
        });

        Promise.all(promises).then(() => {
            // Calculate per serving
            if (servings > 0) {
                totalCalories = totalCalories / servings;
                totalProtein = totalProtein / servings;
                totalCarbs = totalCarbs / servings;
                totalFat = totalFat / servings;
            }

            // Log the final totals
            console.log("Calculation complete. Per serving totals:");
            console.log(`Calories: ${totalCalories.toFixed(1)}`);
            console.log(`Protein: ${totalProtein.toFixed(1)}g`);
            console.log(`Carbs: ${totalCarbs.toFixed(1)}g`);
            console.log(`Fat: ${totalFat.toFixed(1)}g`);

            // Update the form fields
            if (caloriesInput) caloriesInput.value = totalCalories.toFixed(1);
            if (proteinInput) proteinInput.value = totalProtein.toFixed(1);
            if (carbsInput) carbsInput.value = totalCarbs.toFixed(1);
            if (fatInput) fatInput.value = totalFat.toFixed(1);
        });
    }

    // Optional: Add toggle for auto-calculation
    const toggleContainer = document.createElement("div");
    toggleContainer.style.marginBottom = "15px";
    toggleContainer.innerHTML = `
        <label>
            <input type="checkbox" id="auto-calculate-nutrition">
            Auto-calculate nutrition when ingredients change
        </label>
    `;

    if (calculateButton) {
        calculateButton.parentNode.insertBefore(toggleContainer, calculateButton);

        const autoCalculateCheckbox = document.getElementById("auto-calculate-nutrition");
        autoCalculateCheckbox.addEventListener("change", function() {
            calculateButton.dataset.autoCalculate = this.checked;
            if (this.checked) {
                calculateNutrition();
            }
        });
    }
});