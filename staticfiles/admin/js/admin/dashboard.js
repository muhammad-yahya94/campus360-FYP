
// Function to close modal by simulating a click on modal backdrop
function close_modal() {
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.click();
    }
}

// Toggle sidebar visibility
document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    if (toggleButton && sidebar) {
        toggleButton.addEventListener("click", function () {
            if (sidebar.classList.contains("!hidden")) {
                sidebar.classList.remove("!hidden");
                sidebar.classList.add("!block");
            } else {
                sidebar.classList.remove("!block");
                sidebar.classList.add("!hidden");
            }
        });
    }
});

// Toggle entire attribute (add/remove)
function toggleAttr(element, attr, val) {
    if (element.hasAttribute(attr)) {
        element.removeAttribute(attr);
    } else {
        element.setAttribute(attr, val);
    }
}

// Toggle attribute value between two values
function toggleAttrVal(element, attr, val1, val2) {
    const current = element.getAttribute(attr);
    if (current === val1) {
        element.setAttribute(attr, val2);
    } else if (current === val2) {
        element.setAttribute(attr, val1);
    } else {
        element.setAttribute(attr, val1);
    }
}
