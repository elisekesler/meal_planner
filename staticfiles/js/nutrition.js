document.addEventListener("DOMContentLoaded", function () {
    const calculateButton = document.getElementById("calculate-nutrition");
    const ingredientRows = document.querySelectorAll(".ingredient-row");
    const caloriesInput = document.getElementById("calories");
    const proteinInput = document.getElementById("protein");
    const carbsInput = document.getElementById("carbs");
    const fatInput = document.getElementById("fat");

    calculateButton.addEventListener("click", function () {
        let totalCalories = 0;
        let totalProtein = 0;
        let totalCarbs = 0;
        let totalFat = 0;

        const promises = Array.from(ingredientRows).map((row) => {
        const ingredientName = row.querySelector("[name='ingredient_name[]']").value.trim();
            const amount = parseFloat(row.querySelector("[name='ingredient_amount[]']").value) || 0;

            if (ingredientName && amount) {
                return fetch(`/api/ingredient/${encodeURIComponent(ingredientName)}/`)
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.success) {
                            totalCalories += data.calories * amount;
                            totalProtein += data.protein * amount;
                            totalCarbs += data.carbs * amount;
                            totalFat += data.fat * amount;
                        }
                    });
            }
        });

        Promise.all(promises).then(() => {
            caloriesInput.value = totalCalories.toFixed(2);
            proteinInput.value = totalProtein.toFixed(2);
            carbsInput.value = totalCarbs.toFixed(2);
            fatInput.value = totalFat.toFixed(2);
        });
    });
});
