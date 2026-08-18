// =========================================
// MODALS
// =========================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);

    if (!modal) {
        return;
    }

    modal.classList.add("active");
    document.body.classList.add("modal-open");
}


function closeModal(modalId) {
    const modal = document.getElementById(modalId);

    if (!modal) {
        return;
    }

    modal.classList.remove("active");
    document.body.classList.remove("modal-open");
}


// =========================================
// CLOSE MODAL WITH ESCAPE
// =========================================

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {

        document
            .querySelectorAll(".modal.active")
            .forEach(function (modal) {
                modal.classList.remove("active");
            });

        document.body.classList.remove("modal-open");
    }
});


// =========================================
// PAYMENT METHOD FIELDS
// =========================================

function togglePaymentFields() {

    const paymentMethod =
        document.getElementById("paymentMethod");

    const walletField =
        document.getElementById("walletPinField");

    const cardField =
        document.getElementById("cardNumberField");


    if (!paymentMethod || !walletField || !cardField) {
        return;
    }


    walletField.style.display = "none";
    cardField.style.display = "none";


    if (paymentMethod.value === "wallet") {
        walletField.style.display = "flex";
    }


    if (paymentMethod.value === "card") {
        cardField.style.display = "flex";
    }
}


// =========================================
// CARD NUMBER FORMATTING
// =========================================

document.addEventListener("input", function (event) {

    if (event.target.name !== "card_number") {
        return;
    }

    let value = event.target.value
        .replace(/\D/g, "")
        .substring(0, 16);

    value = value
        .replace(/(.{4})/g, "$1 ")
        .trim();

    event.target.value = value;
});


// =========================================
// PAGE READY
// =========================================

document.addEventListener("DOMContentLoaded", function () {
    togglePaymentFields();
});