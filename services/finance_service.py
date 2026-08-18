from calendar import monthrange
from datetime import date, datetime
from uuid import uuid4


class FinanceService:

    CATEGORIES = [
        "Food",
        "Transport",
        "Bills",
        "Shopping",
        "Entertainment",
        "Health",
        "Education",
        "Subscriptions",
        "Other"
    ]

    def __init__(self, database):
        self.database = database

    # =====================================
    # Add Expense
    # =====================================

    def add_expense(
        self,
        user_id,
        category,
        amount,
        note=""
    ):

        if amount <= 0:
            return None

        if category not in self.CATEGORIES:
            category = "Other"

        expense_id = (
            "EXP-"
            + uuid4().hex[:10].upper()
        )

        self.database.add_expense(
            user_id=user_id,
            expense_id=expense_id,
            category=category,
            amount=amount,
            note=note
        )

        return expense_id

    # =====================================
    # Set Budget
    # =====================================

    def set_budget(
        self,
        user_id,
        month,
        amount
    ):

        if amount <= 0:
            return False

        return (
            self.database.set_monthly_budget(
                user_id=user_id,
                month=month,
                amount=amount
            )
        )

    # =====================================
    # Validate Month
    # =====================================

    @staticmethod
    def is_valid_month(month):

        try:

            datetime.strptime(
                month,
                "%Y-%m"
            )

            return True

        except ValueError:

            return False

    # =====================================
    # Month Label
    # =====================================

    @staticmethod
    def get_month_label(month):

        month_date = datetime.strptime(
            month,
            "%Y-%m"
        )

        return month_date.strftime(
            "%B %Y"
        )

    # =====================================
    # Current Month Information
    # =====================================

    def get_current_month_info(self):

        today = date.today()

        days_in_month = monthrange(
            today.year,
            today.month
        )[1]

        days_remaining = (
            days_in_month
            - today.day
        )

        month_end = date(
            today.year,
            today.month,
            days_in_month
        )

        progress_percentage = (
            today.day
            / days_in_month
            * 100
        )

        return {
            "month":
                today.strftime("%Y-%m"),

            "label":
                today.strftime("%B %Y"),

            "day_of_month":
                today.day,

            "days_in_month":
                days_in_month,

            "days_remaining":
                days_remaining,

            "end_date":
                month_end.strftime(
                    "%d %B %Y"
                ),

            "progress_percentage":
                progress_percentage
        }

    # =====================================
    # Monthly Summary
    # =====================================

    def get_month_summary(
        self,
        user_id,
        month
    ):

        expenses = (
            self.database.get_expenses(
                user_id=user_id,
                month=month
            )
        )

        budget_document = (
            self.database.get_monthly_budget(
                user_id=user_id,
                month=month
            )
        )

        budget = 0.0

        if budget_document:

            budget = float(
                budget_document.get(
                    "amount",
                    0
                )
            )

        total_spent = sum(
            float(expense["amount"])
            for expense in expenses
        )

        if budget > 0:

            remaining = (
                budget
                - total_spent
            )

            percentage = (
                total_spent
                / budget
                * 100
            )

        else:

            remaining = 0.0
            percentage = 0.0

        category_totals = {}

        for expense in expenses:

            category = expense.get(
                "category",
                "Other"
            )

            category_totals[category] = (
                category_totals.get(
                    category,
                    0
                )
                + float(
                    expense["amount"]
                )
            )

        category_breakdown = []

        for category, amount in sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True
        ):

            if total_spent > 0:

                category_percentage = (
                    amount
                    / total_spent
                    * 100
                )

            else:

                category_percentage = 0

            category_breakdown.append({
                "category":
                    category,

                "amount":
                    amount,

                "percentage":
                    category_percentage
            })

        highest_category = None

        if category_breakdown:

            highest_category = (
                category_breakdown[0]
            )

        return {
            "budget":
                budget,

            "total_spent":
                total_spent,

            "remaining":
                remaining,

            "percentage":
                percentage,

            "expense_count":
                len(expenses),

            "expenses":
                expenses,

            "category_breakdown":
                category_breakdown,

            "highest_category":
                highest_category
        }

    # =====================================
    # Monthly History
    # =====================================

    def get_history(
        self,
        user_id
    ):

        months = (
            self.database
            .get_available_finance_months(
                user_id
            )
        )

        current_month = (
            datetime.now().strftime(
                "%Y-%m"
            )
        )

        history = []

        for month in months:

            summary = (
                self.get_month_summary(
                    user_id=user_id,
                    month=month
                )
            )

            history.append({
                "month":
                    month,

                "label":
                    self.get_month_label(
                        month
                    ),

                "budget":
                    summary["budget"],

                "total_spent":
                    summary[
                        "total_spent"
                    ],

                "remaining":
                    summary[
                        "remaining"
                    ],

                "expense_count":
                    summary[
                        "expense_count"
                    ],

                "is_current":
                    month
                    == current_month
            })

        return history