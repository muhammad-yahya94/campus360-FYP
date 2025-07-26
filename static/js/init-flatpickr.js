document.addEventListener('DOMContentLoaded', function() {
    flatpickr("input[type=datetime-local]", {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
    });
    flatpickr("input[type=date]", {
        dateFormat: "Y-m-d",
    });
});
