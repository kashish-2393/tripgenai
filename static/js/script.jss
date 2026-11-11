const startDate = document.getElementById("start_date");
const endDate = document.getElementById("end_date");

const today = new Date().toISOString().split("T")[0];

startDate.min = today;
endDate.min = today;

startDate.addEventListener("change", function () {

    endDate.min = startDate.value;

    if (endDate.value && endDate.value < startDate.value) {
        endDate.value = startDate.value;
    }

});


// Loading Screen

const tripForm = document.getElementById("tripForm");
const loadingScreen = document.getElementById("loadingScreen");
const generateBtn = document.getElementById("generateBtn");

tripForm.addEventListener("submit", function () {

    loadingScreen.classList.add("active");

    generateBtn.disabled = true;
    generateBtn.innerText = "Generating Your Trip...";

});
