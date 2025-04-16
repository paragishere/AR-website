document.addEventListener("DOMContentLoaded", function () {
    const arButton = document.querySelector(".ar-btn");

    if (arButton) {
        arButton.classList.add("show-tooltip");

        // Hide tooltip after 3 seconds
        setTimeout(() => {
            arButton.classList.remove("show-tooltip");
        }, 3000);
    }
});
