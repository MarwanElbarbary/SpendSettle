import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database.database_manager import DatabaseManager

from services.auth_service import AuthService
from services.wallet_service import WalletService
from services.security_manager import SecurityManager
from services.finance_service import FinanceService
from services.shared_expense_service import SharedExpenseService

from models.user import User

from payments.wallet_payment import WalletPayment
from payments.card_payment import CardPayment


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "digital-wallet-dev-secret"
)


database = DatabaseManager()

auth_service = AuthService(
    database
)

wallet_service = WalletService(
    database
)

finance_service = FinanceService(
    database
)

shared_expense_service = (
    SharedExpenseService(
        database
    )
)


# =====================================
# Helpers
# =====================================

def get_current_user_document():
    if "username" not in session:
        return None

    return database.find_user(
        session["username"]
    )


def balance_is_unlocked():
    return bool(
        session.get(
            "balance_unlocked",
            False
        )
    )


def get_balance_context(user):
    unlocked = balance_is_unlocked()

    return {
        "balance_unlocked": unlocked,
        "wallet_balance": (
            float(user.get("balance", 0))
            if unlocked
            else None
        )
    }


def get_greeting():
    current_hour = datetime.now().hour

    if current_hour < 12:
        return "Good morning"

    if current_hour < 18:
        return "Good afternoon"

    return "Good evening"


def get_wallet_stats(transactions):
    current_month = datetime.now().strftime(
        "%Y-%m"
    )

    incoming_types = {
        "Deposit",
        "Transfer Received"
    }

    outgoing_types = {
        "Withdraw",
        "Transfer Sent",
        "Wallet Payment"
    }

    money_in = 0.0
    money_out = 0.0

    for transaction in transactions:
        transaction_date = transaction.get(
            "date"
        )

        if (
            not transaction_date
            or transaction_date.strftime(
                "%Y-%m"
            ) != current_month
        ):
            continue

        transaction_type = transaction.get(
            "transaction_type",
            ""
        )

        amount = float(
            transaction.get(
                "amount",
                0
            )
        )

        if transaction_type in incoming_types:
            money_in += amount

        elif transaction_type in outgoing_types:
            money_out += amount

    return {
        "money_in": round(
            money_in,
            2
        ),
        "money_out": round(
            money_out,
            2
        ),
        "transaction_count": len(
            transactions
        )
    }


def user_is_group_member(
    user_id,
    group
):
    return any(
        member["user_id"] == user_id
        for member in group.get(
            "members",
            []
        )
    )


def build_group_cards(
    groups,
    user_id
):
    cards = []

    for group in groups:
        expenses = (
            database.get_group_expenses(
                group["group_id"]
            )
        )

        settlements = (
            database.get_group_settlements(
                group["group_id"]
            )
        )

        balances = (
            shared_expense_service
            .calculate_balances(
                group,
                expenses,
                settlements
            )
        )

        current_balance = 0

        for balance in balances:
            if (
                balance["user_id"]
                == str(user_id)
            ):
                current_balance = (
                    balance["balance"]
                )
                break

        total_expenses = sum(
            float(expense["amount"])
            for expense in expenses
        )

        cards.append({
            "group": group,

            "total_expenses":
                total_expenses,

            "expense_count":
                len(expenses),

            "settlement_count":
                len(settlements),

            "current_balance":
                current_balance
        })

    return cards


def parse_split_form():
    split_method = request.form.get(
        "split_method",
        "equal"
    ).strip()

    participants = request.form.getlist(
        "participants"
    )

    custom_values = {}

    if split_method == "exact":
        for username in participants:
            custom_values[username] = (
                request.form.get(
                    f"exact_{username}",
                    ""
                ).strip()
            )

    elif split_method == "percentage":
        for username in participants:
            custom_values[username] = (
                request.form.get(
                    f"percent_{username}",
                    ""
                ).strip()
            )

    return (
        split_method,
        participants,
        custom_values
    )


# =====================================
# Home
# =====================================

@app.route("/")
def home():
    if "username" in session:
        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =====================================
# Register
# =====================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    if "username" in session:
        return redirect(
            url_for("dashboard")
        )

    error = None

    if request.method == "POST":
        name = request.form.get(
            "name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        pin = request.form.get(
            "pin",
            ""
        ).strip()

        confirm_pin = request.form.get(
            "confirm_pin",
            ""
        ).strip()

        if (
            not name
            or not username
            or not phone
            or not pin
            or not confirm_pin
        ):
            error = (
                "Please fill in all fields"
            )

        elif (
            not pin.isdigit()
            or len(pin) != 4
        ):
            error = (
                "PIN must be exactly 4 digits"
            )

        elif pin != confirm_pin:
            error = (
                "PINs do not match"
            )

        else:
            success = (
                auth_service.register(
                    name=name,
                    username=username,
                    phone=phone,
                    pin=pin
                )
            )

            if success:
                flash(
                    (
                        "Account created successfully. "
                        "Please login."
                    ),
                    "success"
                )

                return redirect(
                    url_for("login")
                )

            error = (
                "Username already exists"
            )

    return render_template(
        "register.html",
        error=error
    )


# =====================================
# Login
# =====================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    if "username" in session:
        return redirect(
            url_for("dashboard")
        )

    error = None

    if request.method == "POST":
        username = request.form.get(
            "username",
            ""
        ).strip()

        pin = request.form.get(
            "pin",
            ""
        ).strip()

        if not username or not pin:
            error = (
                "Please enter username and PIN"
            )

        else:
            user = auth_service.login(
                username=username,
                pin=pin
            )

            if user:
                session["username"] = (
                    user.username
                )

                session["balance_unlocked"] = (
                    False
                )

                return redirect(
                    url_for("dashboard")
                )

            error = (
                "Invalid username or PIN"
            )

    return render_template(
        "login.html",
        error=error
    )


# =====================================
# Dashboard
# =====================================

@app.route("/dashboard")
def dashboard():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    transactions = (
        database.get_transactions(
            user["_id"]
        )
    )

    month_info = (
        finance_service
        .get_current_month_info()
    )

    finance_summary = (
        finance_service
        .get_month_summary(
            user_id=user["_id"],
            month=month_info["month"]
        )
    )

    active_groups = (
        database.get_user_groups(
            user["_id"],
            archived=False
        )
    )

    group_cards = (
        build_group_cards(
            active_groups,
            user["_id"]
        )
    )

    shared_owe = 0.0
    shared_owed = 0.0

    for card in group_cards:
        current_balance = float(
            card.get(
                "current_balance",
                0
            )
        )

        if current_balance < 0:
            shared_owe += abs(
                current_balance
            )

        elif current_balance > 0:
            shared_owed += (
                current_balance
            )

    balance_context = (
        get_balance_context(
            user
        )
    )

    return render_template(
        "dashboard.html",

        user=user,

        transactions=transactions,

        wallet_stats=(
            get_wallet_stats(
                transactions
            )
        ),

        greeting=get_greeting(),

        month_info=month_info,

        finance_summary=(
            finance_summary
        ),

        shared_summary={
            "owe": round(
                shared_owe,
                2
            ),
            "owed": round(
                shared_owed,
                2
            ),
            "group_count": len(
                group_cards
            )
        },

        balance_unlocked=(
            balance_context[
                "balance_unlocked"
            ]
        ),

        wallet_balance=(
            balance_context[
                "wallet_balance"
            ]
        )
    )


# =====================================
# Wallet
# =====================================

@app.route("/wallet")
def wallet():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    transactions = (
        database.get_transactions(
            user["_id"]
        )
    )

    balance_context = (
        get_balance_context(
            user
        )
    )

    return render_template(
        "wallet.html",

        user=user,

        transactions=transactions,

        wallet_stats=(
            get_wallet_stats(
                transactions
            )
        ),

        balance_unlocked=(
            balance_context[
                "balance_unlocked"
            ]
        ),

        wallet_balance=(
            balance_context[
                "wallet_balance"
            ]
        )
    )


# =====================================
# Balance Privacy
# =====================================

@app.route(
    "/balance/unlock",
    methods=["POST"]
)
def unlock_balance():
    user_document = (
        get_current_user_document()
    )

    if not user_document:
        session.clear()

        return redirect(
            url_for("login")
        )

    pin = request.form.get(
        "pin",
        ""
    ).strip()

    next_page = request.form.get(
        "next_page",
        "dashboard"
    ).strip()

    allowed_pages = {
        "dashboard",
        "wallet",
        "profile"
    }

    if next_page not in allowed_pages:
        next_page = "dashboard"

    user = User.from_document(
        user_document
    )

    if not user.check_pin(pin):
        session["balance_unlocked"] = (
            False
        )

        flash(
            "Incorrect PIN",
            "error"
        )

        return redirect(
            url_for(next_page)
        )

    session["balance_unlocked"] = True

    flash(
        "Balance unlocked",
        "success"
    )

    return redirect(
        url_for(next_page)
    )


@app.route(
    "/balance/hide",
    methods=["POST"]
)
def hide_balance():
    if "username" not in session:
        return redirect(
            url_for("login")
        )

    next_page = request.form.get(
        "next_page",
        "dashboard"
    ).strip()

    allowed_pages = {
        "dashboard",
        "wallet",
        "profile"
    }

    if next_page not in allowed_pages:
        next_page = "dashboard"

    session["balance_unlocked"] = False

    return redirect(
        url_for(next_page)
    )


# =====================================
# My Money
# =====================================

@app.route("/finance")
def finance():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    month_info = (
        finance_service
        .get_current_month_info()
    )

    current_month = (
        month_info["month"]
    )

    summary = (
        finance_service
        .get_month_summary(
            user_id=user["_id"],
            month=current_month
        )
    )

    history = (
        finance_service.get_history(
            user["_id"]
        )
    )

    return render_template(
        "finance.html",

        user=user,

        current_month=current_month,

        month_info=month_info,

        categories=(
            finance_service.CATEGORIES
        ),

        summary=summary,

        history=history
    )


# =====================================
# Finance History
# =====================================

@app.route(
    "/finance/history/<month>"
)
def finance_history(month):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    if not finance_service.is_valid_month(
        month
    ):
        flash(
            "Invalid month",
            "error"
        )

        return redirect(
            url_for("finance")
        )

    available_months = (
        database
        .get_available_finance_months(
            user["_id"]
        )
    )

    if month not in available_months:
        flash(
            "Monthly record not found",
            "error"
        )

        return redirect(
            url_for("finance")
        )

    summary = (
        finance_service
        .get_month_summary(
            user_id=user["_id"],
            month=month
        )
    )

    month_label = (
        finance_service
        .get_month_label(
            month
        )
    )

    current_month = (
        datetime.now().strftime(
            "%Y-%m"
        )
    )

    return render_template(
        "finance_history.html",

        user=user,

        month=month,

        month_label=month_label,

        summary=summary,

        is_current=(
            month == current_month
        )
    )


# =====================================
# Add Personal Expense
# =====================================

@app.route(
    "/finance/add-expense",
    methods=["POST"]
)
def add_expense():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    category = request.form.get(
        "category",
        ""
    ).strip()

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    note = request.form.get(
        "note",
        ""
    ).strip()

    try:
        amount = float(amount_text)

    except ValueError:
        flash(
            "Please enter a valid amount",
            "error"
        )

        return redirect(
            url_for("finance")
        )

    if amount <= 0:
        flash(
            (
                "Expense amount must be "
                "greater than zero"
            ),
            "error"
        )

        return redirect(
            url_for("finance")
        )

    expense_id = (
        finance_service.add_expense(
            user_id=user["_id"],
            category=category,
            amount=amount,
            note=note
        )
    )

    if expense_id:
        flash(
            (
                f"{amount:g} EGP expense "
                f"added successfully"
            ),
            "success"
        )

    else:
        flash(
            "Failed to add expense",
            "error"
        )

    return redirect(
        url_for("finance")
    )


# =====================================
# Set Budget
# =====================================

@app.route(
    "/finance/set-budget",
    methods=["POST"]
)
def set_budget():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    amount_text = request.form.get(
        "budget",
        ""
    ).strip()

    try:
        amount = float(amount_text)

    except ValueError:
        flash(
            "Please enter a valid budget amount",
            "error"
        )

        return redirect(
            url_for("finance")
        )

    if amount <= 0:
        flash(
            "Budget must be greater than zero",
            "error"
        )

        return redirect(
            url_for("finance")
        )

    current_month = (
        datetime.now().strftime(
            "%Y-%m"
        )
    )

    success = (
        finance_service.set_budget(
            user_id=user["_id"],
            month=current_month,
            amount=amount
        )
    )

    if success:
        flash(
            "Monthly budget updated successfully",
            "success"
        )

    else:
        flash(
            "Failed to update budget",
            "error"
        )

    return redirect(
        url_for("finance")
    )


# =====================================
# Groups
# =====================================

@app.route("/groups")
def groups_page():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    active_groups = (
        database.get_user_groups(
            user["_id"],
            archived=False
        )
    )

    archived_groups = (
        database.get_user_groups(
            user["_id"],
            archived=True
        )
    )

    active_group_cards = (
        build_group_cards(
            active_groups,
            user["_id"]
        )
    )

    archived_group_cards = (
        build_group_cards(
            archived_groups,
            user["_id"]
        )
    )

    return render_template(
        "groups.html",

        user=user,

        active_group_cards=(
            active_group_cards
        ),

        archived_group_cards=(
            archived_group_cards
        )
    )


# =====================================
# Create Group
# =====================================

@app.route(
    "/groups/create",
    methods=["POST"]
)
def create_group():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    group_name = request.form.get(
        "group_name",
        ""
    ).strip()

    result = (
        shared_expense_service
        .create_group(
            owner=user,
            group_name=group_name
        )
    )

    if result["success"]:
        flash(
            result["message"],
            "success"
        )

        return redirect(
            url_for(
                "group_detail",
                group_id=(
                    result["group_id"]
                )
            )
        )

    flash(
        result["message"],
        "error"
    )

    return redirect(
        url_for("groups_page")
    )


# =====================================
# Group Detail
# =====================================

@app.route(
    "/groups/<group_id>"
)
def group_detail(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    group = (
        database.get_group_by_id(
            group_id
        )
    )

    if not group:
        flash(
            "Group not found",
            "error"
        )

        return redirect(
            url_for("groups_page")
        )

    if not user_is_group_member(
        user["_id"],
        group
    ):
        flash(
            (
                "You do not have access "
                "to this group"
            ),
            "error"
        )

        return redirect(
            url_for("groups_page")
        )

    expenses = (
        database.get_group_expenses(
            group_id
        )
    )

    settlements = (
        database.get_group_settlements(
            group_id
        )
    )

    balances = (
        shared_expense_service
        .calculate_balances(
            group,
            expenses,
            settlements
        )
    )

    debts = (
        shared_expense_service
        .calculate_debts(
            balances
        )
    )

    current_user_balance = 0

    for balance in balances:
        if (
            balance["user_id"]
            == str(user["_id"])
        ):
            current_user_balance = (
                balance["balance"]
            )
            break

    total_expenses = sum(
        float(expense["amount"])
        for expense in expenses
    )

    is_owner = (
        group["owner_id"]
        == user["_id"]
    )

    has_settlements = (
        len(settlements) > 0
    )

    expense_editing_locked = (
        group.get(
            "archived",
            False
        )
        or has_settlements
    )

    return render_template(
        "group_detail.html",

        user=user,

        group=group,

        expenses=expenses,

        settlements=settlements,

        balances=balances,

        debts=debts,

        current_user_balance=(
            current_user_balance
        ),

        total_expenses=(
            total_expenses
        ),

        is_owner=is_owner,

        is_archived=group.get(
            "archived",
            False
        ),

        has_settlements=(
            has_settlements
        ),

        expense_editing_locked=(
            expense_editing_locked
        )
    )


# =====================================
# Add Member
# =====================================

@app.route(
    "/groups/<group_id>/add-member",
    methods=["POST"]
)
def add_group_member(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    username = request.form.get(
        "username",
        ""
    ).strip()

    result = (
        shared_expense_service
        .add_member(
            group_id=group_id,
            username=username,
            current_user_id=(
                user["_id"]
            )
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Add Group Expense
# =====================================

@app.route(
    "/groups/<group_id>/add-expense",
    methods=["POST"]
)
def add_group_expense(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    paid_by_username = (
        request.form.get(
            "paid_by",
            ""
        ).strip()
    )

    description = request.form.get(
        "description",
        ""
    ).strip()

    amount = request.form.get(
        "amount",
        ""
    ).strip()

    (
        split_method,
        participants,
        custom_values
    ) = parse_split_form()

    result = (
        shared_expense_service
        .add_expense(
            group_id=group_id,

            paid_by_username=(
                paid_by_username
            ),

            description=description,

            amount=amount,

            current_user_id=(
                user["_id"]
            ),

            split_method=split_method,

            participant_usernames=(
                participants
            ),

            custom_values=(
                custom_values
            )
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Edit Group Expense
# =====================================

@app.route(
    "/groups/<group_id>/expenses/<expense_id>/edit",
    methods=["GET", "POST"]
)
def edit_group_expense(
    group_id,
    expense_id
):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    group = (
        database.get_group_by_id(
            group_id
        )
    )

    if not group:
        flash(
            "Group not found",
            "error"
        )

        return redirect(
            url_for("groups_page")
        )

    if not user_is_group_member(
        user["_id"],
        group
    ):
        flash(
            "You do not have access to this group",
            "error"
        )

        return redirect(
            url_for("groups_page")
        )

    expense = (
        database.get_group_expense_by_id(
            group_id,
            expense_id
        )
    )

    permission = (
        shared_expense_service
        .can_modify_expense(
            group,
            expense,
            user["_id"]
        )
    )

    if not permission["success"]:
        flash(
            permission["message"],
            "error"
        )

        return redirect(
            url_for(
                "group_detail",
                group_id=group_id
            )
        )

    if request.method == "POST":
        paid_by_username = (
            request.form.get(
                "paid_by",
                ""
            ).strip()
        )

        description = (
            request.form.get(
                "description",
                ""
            ).strip()
        )

        amount = request.form.get(
            "amount",
            ""
        ).strip()

        (
            split_method,
            participants,
            custom_values
        ) = parse_split_form()

        result = (
            shared_expense_service
            .edit_expense(
                group_id=group_id,

                expense_id=expense_id,

                current_user=user,

                paid_by_username=(
                    paid_by_username
                ),

                description=description,

                amount=amount,

                split_method=(
                    split_method
                ),

                participant_usernames=(
                    participants
                ),

                custom_values=(
                    custom_values
                )
            )
        )

        flash(
            result["message"],
            (
                "success"
                if result["success"]
                else "error"
            )
        )

        if result["success"]:
            return redirect(
                url_for(
                    "group_detail",
                    group_id=group_id
                )
            )

        return redirect(
            url_for(
                "edit_group_expense",
                group_id=group_id,
                expense_id=expense_id
            )
        )

    split_method_label = (
        expense.get(
            "split_method",
            "Equal"
        )
    )

    if split_method_label == "Percentage":
        split_method = "percentage"

    elif split_method_label == "Exact Amount":
        split_method = "exact"

    else:
        split_method = "equal"

    participant_usernames = [
        split["username"]
        for split in expense.get(
            "splits",
            []
        )
    ]

    exact_values = {
        split["username"]:
            float(
                split["share"]
            )
        for split in expense.get(
            "splits",
            []
        )
    }

    percentage_values = {}

    for split in expense.get(
        "splits",
        []
    ):
        if "percentage" in split:
            percentage_values[
                split["username"]
            ] = float(
                split["percentage"]
            )

    return render_template(
        "edit_group_expense.html",

        user=user,

        group=group,

        expense=expense,

        split_method=split_method,

        participant_usernames=(
            participant_usernames
        ),

        exact_values=exact_values,

        percentage_values=(
            percentage_values
        )
    )


# =====================================
# Delete Group Expense
# =====================================

@app.route(
    "/groups/<group_id>/expenses/<expense_id>/delete",
    methods=["POST"]
)
def delete_group_expense(
    group_id,
    expense_id
):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    result = (
        shared_expense_service
        .delete_expense(
            group_id=group_id,

            expense_id=expense_id,

            current_user=user
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Partial / Full Settlement
# =====================================

@app.route(
    "/groups/<group_id>/settle",
    methods=["POST"]
)
def settle_group_debt(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    receiver_username = (
        request.form.get(
            "receiver_username",
            ""
        ).strip()
    )

    amount = request.form.get(
        "amount",
        ""
    ).strip()

    pin = request.form.get(
        "pin",
        ""
    ).strip()

    if (
        not receiver_username
        or not amount
        or not pin
    ):
        flash(
            (
                "Payment amount, receiver "
                "and PIN are required"
            ),
            "error"
        )

        return redirect(
            url_for(
                "group_detail",
                group_id=group_id
            )
        )

    result = (
        shared_expense_service
        .settle_debt(
            group_id=group_id,

            payer_document=user,

            receiver_username=(
                receiver_username
            ),

            amount=amount,

            pin=pin
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Rename Group
# =====================================

@app.route(
    "/groups/<group_id>/rename",
    methods=["POST"]
)
def rename_group(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    new_name = request.form.get(
        "group_name",
        ""
    ).strip()

    result = (
        shared_expense_service
        .rename_group(
            group_id=group_id,

            owner_id=user["_id"],

            new_name=new_name
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Archive Group
# =====================================

@app.route(
    "/groups/<group_id>/archive",
    methods=["POST"]
)
def archive_group(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    result = (
        shared_expense_service
        .archive_group(
            group_id,
            user["_id"]
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    if result["success"]:
        return redirect(
            url_for("groups_page")
        )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Restore Group
# =====================================

@app.route(
    "/groups/<group_id>/restore",
    methods=["POST"]
)
def restore_group(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    result = (
        shared_expense_service
        .restore_group(
            group_id,
            user["_id"]
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Delete Group
# =====================================

@app.route(
    "/groups/<group_id>/delete",
    methods=["POST"]
)
def delete_group(group_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    pin = request.form.get(
        "pin",
        ""
    ).strip()

    result = (
        shared_expense_service
        .delete_group(
            group_id=group_id,

            owner_document=user,

            pin=pin
        )
    )

    flash(
        result["message"],
        (
            "success"
            if result["success"]
            else "error"
        )
    )

    if result["success"]:
        return redirect(
            url_for("groups_page")
        )

    return redirect(
        url_for(
            "group_detail",
            group_id=group_id
        )
    )


# =====================================
# Profile
# =====================================

@app.route("/profile")
def profile():
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    transactions = (
        database.get_transactions(
            user["_id"]
        )
    )

    balance_context = (
        get_balance_context(
            user
        )
    )

    return render_template(
        "profile.html",

        user=user,

        transaction_count=(
            len(transactions)
        ),

        balance_unlocked=(
            balance_context[
                "balance_unlocked"
            ]
        ),

        wallet_balance=(
            balance_context[
                "wallet_balance"
            ]
        )
    )


# =====================================
# Change PIN
# =====================================

@app.route(
    "/change-pin",
    methods=["POST"]
)
def change_pin():
    user_document = (
        get_current_user_document()
    )

    if not user_document:
        session.clear()

        return redirect(
            url_for("login")
        )

    current_pin = request.form.get(
        "current_pin",
        ""
    ).strip()

    new_pin = request.form.get(
        "new_pin",
        ""
    ).strip()

    confirm_pin = request.form.get(
        "confirm_pin",
        ""
    ).strip()

    if (
        not current_pin
        or not new_pin
        or not confirm_pin
    ):
        flash(
            "Please fill in all PIN fields",
            "error"
        )

        return redirect(
            url_for("profile")
        )

    user = User.from_document(
        user_document
    )

    if not user.check_pin(
        current_pin
    ):
        flash(
            "Current PIN is incorrect",
            "error"
        )

        return redirect(
            url_for("profile")
        )

    if (
        not new_pin.isdigit()
        or len(new_pin) != 4
    ):
        flash(
            "New PIN must be exactly 4 digits",
            "error"
        )

        return redirect(
            url_for("profile")
        )

    if new_pin != confirm_pin:
        flash(
            "New PINs do not match",
            "error"
        )

        return redirect(
            url_for("profile")
        )

    if current_pin == new_pin:
        flash(
            (
                "New PIN must be different "
                "from current PIN"
            ),
            "error"
        )

        return redirect(
            url_for("profile")
        )

    new_pin_hash = (
        SecurityManager.hash_pin(
            new_pin
        )
    )

    success = (
        database.update_user_pin(
            username=session[
                "username"
            ],

            new_pin_hash=(
                new_pin_hash
            )
        )
    )

    if success:
        session["balance_unlocked"] = (
            False
        )

        flash(
            "PIN changed successfully",
            "success"
        )

    else:
        flash(
            "PIN change failed",
            "error"
        )

    return redirect(
        url_for("profile")
    )


# =====================================
# Deposit
# =====================================

@app.route(
    "/deposit",
    methods=["POST"]
)
def deposit():
    user_document = (
        get_current_user_document()
    )

    if not user_document:
        session.clear()

        return redirect(
            url_for("login")
        )

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    try:
        amount = float(amount_text)

    except ValueError:
        flash(
            "Please enter a valid amount",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    if amount <= 0:
        flash(
            "Amount must be greater than zero",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    user = User.from_document(
        user_document
    )

    transaction_id = (
        wallet_service.deposit(
            user,
            amount
        )
    )

    if transaction_id:
        return redirect(
            url_for(
                "receipt",
                transaction_id=(
                    transaction_id
                )
            )
        )

    flash(
        "Deposit failed",
        "error"
    )

    return redirect(
        url_for("wallet")
    )


# =====================================
# Withdraw
# =====================================

@app.route(
    "/withdraw",
    methods=["POST"]
)
def withdraw():
    user_document = (
        get_current_user_document()
    )

    if not user_document:
        session.clear()

        return redirect(
            url_for("login")
        )

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    pin = request.form.get(
        "pin",
        ""
    ).strip()

    try:
        amount = float(amount_text)

    except ValueError:
        flash(
            "Please enter a valid amount",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    if amount <= 0:
        flash(
            "Amount must be greater than zero",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    user = User.from_document(
        user_document
    )

    if not user.check_pin(pin):
        flash(
            "Incorrect PIN",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    if (
        amount
        > user.wallet.get_balance()
    ):
        flash(
            "Insufficient balance",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    transaction_id = (
        wallet_service.withdraw(
            user,
            amount
        )
    )

    if transaction_id:
        return redirect(
            url_for(
                "receipt",
                transaction_id=(
                    transaction_id
                )
            )
        )

    flash(
        "Withdraw failed",
        "error"
    )

    return redirect(
        url_for("wallet")
    )


# =====================================
# Transfer
# =====================================

@app.route(
    "/transfer",
    methods=["POST"]
)
def transfer():
    user_document = (
        get_current_user_document()
    )

    if not user_document:
        session.clear()

        return redirect(
            url_for("login")
        )

    receiver_username = (
        request.form.get(
            "receiver_username",
            ""
        ).strip()
    )

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    pin = request.form.get(
        "pin",
        ""
    ).strip()

    try:
        amount = float(amount_text)

    except ValueError:
        flash(
            "Please enter a valid amount",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    if amount <= 0:
        flash(
            "Amount must be greater than zero",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    user = User.from_document(
        user_document
    )

    transaction_id = (
        wallet_service.transfer(
            sender_user=user,

            receiver_username=(
                receiver_username
            ),

            amount=amount,

            pin=pin
        )
    )

    if transaction_id:
        return redirect(
            url_for(
                "receipt",
                transaction_id=(
                    transaction_id
                )
            )
        )

    flash(
        (
            "Transfer failed. Check username, "
            "PIN, and balance."
        ),
        "error"
    )

    return redirect(
        url_for("wallet")
    )


# =====================================
# Payment
# =====================================

@app.route(
    "/payment",
    methods=["POST"]
)
def make_payment():
    user_document = (
        get_current_user_document()
    )

    if not user_document:
        session.clear()

        return redirect(
            url_for("login")
        )

    payment_type = request.form.get(
        "payment_method",
        ""
    ).strip()

    amount_text = request.form.get(
        "amount",
        ""
    ).strip()

    pin = request.form.get(
        "pin",
        ""
    ).strip()

    card_number = request.form.get(
        "card_number",
        ""
    ).strip()

    try:
        amount = float(amount_text)

    except ValueError:
        flash(
            "Please enter a valid payment amount",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    if amount <= 0:
        flash(
            "Amount must be greater than zero",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    user = User.from_document(
        user_document
    )

    if payment_type == "wallet":
        if not pin:
            flash(
                "Please enter your PIN",
                "error"
            )

            return redirect(
                url_for("wallet")
            )

        payment_method = WalletPayment(
            user=user,
            pin=pin,
            wallet_service=(
                wallet_service
            )
        )

    elif payment_type == "card":
        if not card_number:
            flash(
                "Please enter card number",
                "error"
            )

            return redirect(
                url_for("wallet")
            )

        payment_method = CardPayment(
            user=user,
            card_number=card_number,
            database=database
        )

    else:
        flash(
            "Please select a payment method",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    result = payment_method.pay(
        amount
    )

    if result["success"]:
        transaction_id = result.get(
            "transaction_id"
        )

        if transaction_id:
            return redirect(
                url_for(
                    "receipt",
                    transaction_id=(
                        transaction_id
                    )
                )
            )

        flash(
            result["message"],
            "success"
        )

    else:
        flash(
            result["message"],
            "error"
        )

    return redirect(
        url_for("wallet")
    )


# =====================================
# Receipt
# =====================================

@app.route(
    "/receipt/<transaction_id>"
)
def receipt(transaction_id):
    user = (
        get_current_user_document()
    )

    if not user:
        session.clear()

        return redirect(
            url_for("login")
        )

    transaction = (
        database.get_transaction_by_id(
            user_id=user["_id"],

            transaction_id=(
                transaction_id
            )
        )
    )

    if not transaction:
        flash(
            "Transaction receipt not found",
            "error"
        )

        return redirect(
            url_for("wallet")
        )

    return render_template(
        "receipt.html",
        user=user,
        transaction=transaction
    )


# =====================================
# Logout
# =====================================

@app.route("/logout")
def logout():
    session.clear()

    return redirect(
        url_for("login")
    )


# =====================================
# Run
# =====================================

if __name__ == "__main__":
    if database.test_connection():
        print(
            "MongoDB connected successfully"
        )

        app.run(
            host="127.0.0.1",
            port=5000,
            debug=True
        )

    else:
        print(
            "MongoDB connection failed"
        )