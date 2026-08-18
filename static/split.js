const splitForm =
    document.getElementById(
        "sharedExpenseForm"
    );

const expenseAmountInput =
    document.getElementById(
        "sharedExpenseAmount"
    );

const splitMethodSelect =
    document.getElementById(
        "splitMethod"
    );

const splitRows =
    Array.from(
        document.querySelectorAll(
            ".split-member-row"
        )
    );

const validationBox =
    document.getElementById(
        "splitValidation"
    );

const submitButton =
    document.getElementById(
        "addSplitExpenseButton"
    );

const expenseTotalPreview =
    document.getElementById(
        "expenseTotalPreview"
    );

const splitTotalPreview =
    document.getElementById(
        "splitTotalPreview"
    );

const splitTotalLabel =
    document.getElementById(
        "splitTotalLabel"
    );

const selectedParticipants =
    document.getElementById(
        "selectedParticipants"
    );


function roundMoney(value) {
    return (
        Math.round(
            (
                value
                + Number.EPSILON
            )
            * 100
        )
        / 100
    );
}


function roundPercent(value) {
    return (
        Math.round(
            (
                value
                + Number.EPSILON
            )
            * 100
        )
        / 100
    );
}


function formatMoney(value) {
    return (
        roundMoney(value)
            .toFixed(2)
        + " EGP"
    );
}


function getExpenseAmount() {
    if (!expenseAmountInput) {
        return 0;
    }

    const value = parseFloat(
        expenseAmountInput.value
    );

    if (
        Number.isNaN(value)
        || value <= 0
    ) {
        return 0;
    }

    return roundMoney(value);
}


function getActiveRows() {
    return splitRows.filter(
        function (row) {
            const checkbox =
                row.querySelector(
                    ".participant-checkbox"
                );

            return (
                checkbox
                && checkbox.checked
            );
        }
    );
}


function clearMoneyPreviews() {
    splitRows.forEach(
        function (row) {
            const equalPreview =
                row.querySelector(
                    ".equal-preview"
                );

            const percentagePreview =
                row.querySelector(
                    ".percentage-money-preview"
                );

            if (equalPreview) {
                equalPreview.textContent =
                    "0.00 EGP";
            }

            if (percentagePreview) {
                percentagePreview.textContent =
                    "0.00 EGP";
            }
        }
    );
}


function setValid(message) {
    if (
        !validationBox
        || !submitButton
    ) {
        return;
    }

    validationBox.textContent =
        "✓ " + message;

    validationBox.classList.remove(
        "split-invalid"
    );

    validationBox.classList.add(
        "split-valid"
    );

    submitButton.disabled = false;
}


function setInvalid(message) {
    if (
        !validationBox
        || !submitButton
    ) {
        return;
    }

    validationBox.textContent =
        "⚠ " + message;

    validationBox.classList.remove(
        "split-valid"
    );

    validationBox.classList.add(
        "split-invalid"
    );

    submitButton.disabled = true;
}


function distributeEqualExact(
    activeRows,
    amount
) {
    const count =
        activeRows.length;

    if (count === 0) {
        return;
    }

    const base =
        roundMoney(
            amount / count
        );

    let allocated = 0;

    activeRows.forEach(
        function (row, index) {
            const input =
                row.querySelector(
                    ".exact-split-input"
                );

            if (!input) {
                return;
            }

            let share;

            if (
                index
                === count - 1
            ) {
                share = roundMoney(
                    amount - allocated
                );

            } else {
                share = base;
                allocated += share;
            }

            input.value =
                share.toFixed(2);
        }
    );
}


function distributeEqualPercentages(
    activeRows
) {
    const count =
        activeRows.length;

    if (count === 0) {
        return;
    }

    const base =
        roundPercent(
            100 / count
        );

    let allocated = 0;

    activeRows.forEach(
        function (row, index) {
            const input =
                row.querySelector(
                    ".percentage-split-input"
                );

            if (!input) {
                return;
            }

            let percentage;

            if (
                index
                === count - 1
            ) {
                percentage = roundPercent(
                    100 - allocated
                );

            } else {
                percentage = base;
                allocated += percentage;
            }

            input.value =
                percentage.toFixed(2);
        }
    );
}


function prepareMethodDefaults() {
    if (!splitMethodSelect) {
        return;
    }

    const method =
        splitMethodSelect.value;

    const activeRows =
        getActiveRows();

    if (
        activeRows.length === 0
    ) {
        return;
    }

    if (method === "exact") {
        const amount =
            getExpenseAmount();

        const allEmpty =
            activeRows.every(
                function (row) {
                    const input =
                        row.querySelector(
                            ".exact-split-input"
                        );

                    if (!input) {
                        return true;
                    }

                    const value =
                        parseFloat(
                            input.value
                        );

                    return (
                        input.value === ""
                        || Number.isNaN(value)
                        || value === 0
                    );
                }
            );

        if (
            amount > 0
            && allEmpty
        ) {
            distributeEqualExact(
                activeRows,
                amount
            );
        }
    }

    if (
        method === "percentage"
    ) {
        const allEmpty =
            activeRows.every(
                function (row) {
                    const input =
                        row.querySelector(
                            ".percentage-split-input"
                        );

                    if (!input) {
                        return true;
                    }

                    const value =
                        parseFloat(
                            input.value
                        );

                    return (
                        input.value === ""
                        || Number.isNaN(value)
                        || value === 0
                    );
                }
            );

        if (allEmpty) {
            distributeEqualPercentages(
                activeRows
            );
        }
    }
}


function updateEqualSplit(
    activeRows,
    amount
) {
    const count =
        activeRows.length;

    const base =
        roundMoney(
            amount / count
        );

    let allocated = 0;

    splitRows.forEach(
        function (row) {
            const preview =
                row.querySelector(
                    ".equal-preview"
                );

            const checkbox =
                row.querySelector(
                    ".participant-checkbox"
                );

            if (
                preview
                && checkbox
                && !checkbox.checked
            ) {
                preview.textContent =
                    "Not included";
            }
        }
    );

    activeRows.forEach(
        function (row, index) {
            const preview =
                row.querySelector(
                    ".equal-preview"
                );

            if (!preview) {
                return;
            }

            let share;

            if (
                index
                === count - 1
            ) {
                share = roundMoney(
                    amount - allocated
                );

            } else {
                share = base;
                allocated += share;
            }

            preview.textContent =
                formatMoney(share);
        }
    );

    splitTotalLabel.textContent =
        "Split Total";

    splitTotalPreview.textContent =
        formatMoney(amount);

    setValid(
        "Split is valid. "
        + count
        + " participant"
        + (
            count === 1
                ? ""
                : "s"
        )
        + "."
    );
}


function updateExactSplit(
    activeRows,
    amount
) {
    let total = 0;
    let invalid = false;

    activeRows.forEach(
        function (row) {
            const input =
                row.querySelector(
                    ".exact-split-input"
                );

            if (!input) {
                invalid = true;
                return;
            }

            const value =
                parseFloat(
                    input.value
                );

            if (
                Number.isNaN(value)
                || value <= 0
            ) {
                invalid = true;
                return;
            }

            total += value;
        }
    );

    total =
        roundMoney(total);

    splitTotalLabel.textContent =
        "Split Total";

    splitTotalPreview.textContent =
        formatMoney(total);

    if (invalid) {
        setInvalid(
            "Enter an amount greater than 0 "
            + "for every selected participant."
        );

        return;
    }

    const difference =
        roundMoney(
            amount - total
        );

    if (
        Math.abs(difference)
        > 0.009
    ) {
        if (difference > 0) {
            setInvalid(
                formatMoney(difference)
                + " still needs to be assigned."
            );

        } else {
            setInvalid(
                "Split exceeds expense by "
                + formatMoney(
                    Math.abs(
                        difference
                    )
                )
                + "."
            );
        }

        return;
    }

    setValid(
        "Exact split matches the expense total."
    );
}


function updatePercentageSplit(
    activeRows,
    amount
) {
    let totalPercentage = 0;
    let invalid = false;

    splitRows.forEach(
        function (row) {
            const preview =
                row.querySelector(
                    ".percentage-money-preview"
                );

            const checkbox =
                row.querySelector(
                    ".participant-checkbox"
                );

            if (
                preview
                && checkbox
                && !checkbox.checked
            ) {
                preview.textContent =
                    "Not included";
            }
        }
    );

    activeRows.forEach(
        function (row) {
            const input =
                row.querySelector(
                    ".percentage-split-input"
                );

            const preview =
                row.querySelector(
                    ".percentage-money-preview"
                );

            if (
                !input
                || !preview
            ) {
                invalid = true;
                return;
            }

            const percentage =
                parseFloat(
                    input.value
                );

            if (
                Number.isNaN(
                    percentage
                )
                || percentage <= 0
                || percentage > 100
            ) {
                invalid = true;

                preview.textContent =
                    "0.00 EGP";

                return;
            }

            totalPercentage += (
                percentage
            );

            preview.textContent =
                formatMoney(
                    amount
                    * percentage
                    / 100
                );
        }
    );

    totalPercentage =
        roundPercent(
            totalPercentage
        );

    splitTotalLabel.textContent =
        "Percentage Total";

    splitTotalPreview.textContent =
        totalPercentage.toFixed(2)
        + "%";

    if (invalid) {
        setInvalid(
            "Enter a percentage greater than 0 "
            + "for every selected participant."
        );

        return;
    }

    const difference =
        roundPercent(
            100 - totalPercentage
        );

    if (
        Math.abs(difference)
        > 0.009
    ) {
        if (difference > 0) {
            setInvalid(
                difference.toFixed(2)
                + "% still needs to be assigned."
            );

        } else {
            setInvalid(
                "Percentage total exceeds 100% by "
                + Math.abs(
                    difference
                ).toFixed(2)
                + "%."
            );
        }

        return;
    }

    setValid(
        "Percentage split equals exactly 100%."
    );
}


function updateSplit() {
    if (
        !splitMethodSelect
        || !expenseAmountInput
    ) {
        return;
    }

    const method =
        splitMethodSelect.value;

    const amount =
        getExpenseAmount();

    const activeRows =
        getActiveRows();

    if (selectedParticipants) {
        selectedParticipants.textContent =
            activeRows.length;
    }

    if (expenseTotalPreview) {
        expenseTotalPreview.textContent =
            formatMoney(amount);
    }

    splitRows.forEach(
        function (row) {
            const checkbox =
                row.querySelector(
                    ".participant-checkbox"
                );

            const exactArea =
                row.querySelector(
                    ".exact-split-area"
                );

            const percentageArea =
                row.querySelector(
                    ".percentage-split-area"
                );

            const equalArea =
                row.querySelector(
                    ".equal-split-value"
                );

            const exactInput =
                row.querySelector(
                    ".exact-split-input"
                );

            const percentageInput =
                row.querySelector(
                    ".percentage-split-input"
                );

            if (!checkbox) {
                return;
            }

            if (checkbox.checked) {
                row.classList.remove(
                    "not-included"
                );

                if (exactInput) {
                    exactInput.disabled = false;
                }

                if (percentageInput) {
                    percentageInput.disabled = false;
                }

            } else {
                row.classList.add(
                    "not-included"
                );

                if (exactInput) {
                    exactInput.disabled = true;
                }

                if (percentageInput) {
                    percentageInput.disabled = true;
                }
            }

            if (equalArea) {
                equalArea.classList.toggle(
                    "hidden",
                    method !== "equal"
                );
            }

            if (exactArea) {
                exactArea.classList.toggle(
                    "hidden",
                    method !== "exact"
                );
            }

            if (percentageArea) {
                percentageArea.classList.toggle(
                    "hidden",
                    method !== "percentage"
                );
            }
        }
    );

    if (amount <= 0) {
        setInvalid(
            "Enter an expense amount."
        );

        if (splitTotalPreview) {
            splitTotalPreview.textContent =
                "0.00 EGP";
        }

        clearMoneyPreviews();
        return;
    }

    if (
        activeRows.length === 0
    ) {
        setInvalid(
            "Select at least one participant."
        );

        if (splitTotalPreview) {
            splitTotalPreview.textContent =
                "0.00 EGP";
        }

        return;
    }

    if (method === "equal") {
        updateEqualSplit(
            activeRows,
            amount
        );

        return;
    }

    if (method === "exact") {
        updateExactSplit(
            activeRows,
            amount
        );

        return;
    }

    updatePercentageSplit(
        activeRows,
        amount
    );
}


function initializeSplitBuilder() {
    expenseAmountInput.addEventListener(
        "input",
        updateSplit
    );

    splitMethodSelect.addEventListener(
        "change",
        function () {
            prepareMethodDefaults();
            updateSplit();
        }
    );

    splitRows.forEach(
        function (row) {
            const checkbox =
                row.querySelector(
                    ".participant-checkbox"
                );

            const exactInput =
                row.querySelector(
                    ".exact-split-input"
                );

            const percentageInput =
                row.querySelector(
                    ".percentage-split-input"
                );

            if (checkbox) {
                checkbox.addEventListener(
                    "change",
                    function () {
                        prepareMethodDefaults();
                        updateSplit();
                    }
                );
            }

            if (exactInput) {
                exactInput.addEventListener(
                    "input",
                    updateSplit
                );
            }

            if (percentageInput) {
                percentageInput.addEventListener(
                    "input",
                    updateSplit
                );
            }
        }
    );

    updateSplit();

    splitForm.addEventListener(
        "submit",
        function (event) {
            updateSplit();

            if (
                submitButton
                && submitButton.disabled
            ) {
                event.preventDefault();
            }
        }
    );
}


if (
    splitForm
    && expenseAmountInput
    && splitMethodSelect
    && validationBox
    && submitButton
) {
    initializeSplitBuilder();
}