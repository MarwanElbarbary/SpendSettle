from datetime import datetime
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP
)
from uuid import uuid4

from models.user import User
from models.transaction import Transaction


class SharedExpenseService:

    MONEY_STEP = Decimal("0.01")
    PERCENT_STEP = Decimal("0.01")

    def __init__(self, database):
        self.database = database

    # =====================================
    # Helpers
    # =====================================

    @classmethod
    def _money(cls, value):
        try:
            return Decimal(
                str(value)
            ).quantize(
                cls.MONEY_STEP,
                rounding=ROUND_HALF_UP
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError
        ):
            return None

    @classmethod
    def _percentage(cls, value):
        try:
            return Decimal(
                str(value)
            ).quantize(
                cls.PERCENT_STEP,
                rounding=ROUND_HALF_UP
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError
        ):
            return None

    def _build_expense_fields(
        self,
        group,
        paid_by_username,
        description,
        amount,
        split_method,
        participant_usernames,
        custom_values
    ):
        amount_decimal = self._money(
            amount
        )

        if (
            amount_decimal is None
            or amount_decimal <= 0
        ):
            return {
                "success": False,
                "message":
                    "Expense amount must be greater than zero"
            }

        description = (
            description.strip()
        )

        if not description:
            return {
                "success": False,
                "message":
                    "Expense description is required"
            }

        member_map = {
            member["username"]: member
            for member in group["members"]
        }

        payer = member_map.get(
            paid_by_username
        )

        if not payer:
            return {
                "success": False,
                "message":
                    "Selected payer is not a group member"
            }

        participant_usernames = (
            participant_usernames or []
        )

        participants = []
        seen = set()

        for username in participant_usernames:
            if username in seen:
                continue

            seen.add(username)

            member = member_map.get(
                username
            )

            if not member:
                return {
                    "success": False,
                    "message":
                        "Invalid participant detected"
                }

            participants.append(
                member
            )

        if not participants:
            return {
                "success": False,
                "message":
                    "Select at least one participant"
            }

        split_method = (
            split_method
            .strip()
            .lower()
        )

        if split_method not in {
            "equal",
            "exact",
            "percentage"
        }:
            return {
                "success": False,
                "message":
                    "Invalid split method"
            }

        custom_values = (
            custom_values or {}
        )

        splits = []

        # =================================
        # Equal
        # =================================

        if split_method == "equal":
            count = len(
                participants
            )

            base_share = (
                amount_decimal
                / Decimal(count)
            ).quantize(
                self.MONEY_STEP,
                rounding=ROUND_HALF_UP
            )

            allocated = Decimal(
                "0.00"
            )

            for index, member in enumerate(
                participants
            ):
                if index == count - 1:
                    share = (
                        amount_decimal
                        - allocated
                    ).quantize(
                        self.MONEY_STEP,
                        rounding=ROUND_HALF_UP
                    )

                else:
                    share = base_share
                    allocated += share

                splits.append({
                    "user_id":
                        member["user_id"],

                    "username":
                        member["username"],

                    "name":
                        member["name"],

                    "share":
                        float(share)
                })

            method_label = "Equal"

        # =================================
        # Exact
        # =================================

        elif split_method == "exact":
            split_total = Decimal(
                "0.00"
            )

            for member in participants:
                value = self._money(
                    custom_values.get(
                        member["username"],
                        ""
                    )
                )

                if (
                    value is None
                    or value <= 0
                ):
                    return {
                        "success": False,
                        "message": (
                            "Enter a valid amount "
                            f"for {member['name']}"
                        )
                    }

                split_total += value

                splits.append({
                    "user_id":
                        member["user_id"],

                    "username":
                        member["username"],

                    "name":
                        member["name"],

                    "share":
                        float(value)
                })

            split_total = (
                split_total.quantize(
                    self.MONEY_STEP,
                    rounding=ROUND_HALF_UP
                )
            )

            if split_total != amount_decimal:
                difference = (
                    amount_decimal
                    - split_total
                ).quantize(
                    self.MONEY_STEP,
                    rounding=ROUND_HALF_UP
                )

                return {
                    "success": False,
                    "message": (
                        "Exact split total must equal "
                        f"{amount_decimal:.2f} EGP. "
                        f"Difference: {difference:.2f} EGP"
                    )
                }

            method_label = (
                "Exact Amount"
            )

        # =================================
        # Percentage
        # =================================

        else:
            percentage_total = Decimal(
                "0.00"
            )

            percentages = []

            for member in participants:
                percentage = (
                    self._percentage(
                        custom_values.get(
                            member["username"],
                            ""
                        )
                    )
                )

                if (
                    percentage is None
                    or percentage <= 0
                    or percentage > 100
                ):
                    return {
                        "success": False,
                        "message": (
                            "Enter a valid percentage "
                            f"for {member['name']}"
                        )
                    }

                percentage_total += (
                    percentage
                )

                percentages.append(
                    (
                        member,
                        percentage
                    )
                )

            percentage_total = (
                percentage_total.quantize(
                    self.PERCENT_STEP,
                    rounding=ROUND_HALF_UP
                )
            )

            if (
                percentage_total
                != Decimal("100.00")
            ):
                return {
                    "success": False,
                    "message":
                        "Percentage split must equal exactly 100%"
                }

            allocated = Decimal(
                "0.00"
            )

            for index, item in enumerate(
                percentages
            ):
                member, percentage = item

                if (
                    index
                    == len(percentages) - 1
                ):
                    share = (
                        amount_decimal
                        - allocated
                    ).quantize(
                        self.MONEY_STEP,
                        rounding=ROUND_HALF_UP
                    )

                else:
                    share = (
                        amount_decimal
                        * percentage
                        / Decimal("100")
                    ).quantize(
                        self.MONEY_STEP,
                        rounding=ROUND_HALF_UP
                    )

                    allocated += share

                splits.append({
                    "user_id":
                        member["user_id"],

                    "username":
                        member["username"],

                    "name":
                        member["name"],

                    "share":
                        float(share),

                    "percentage":
                        float(percentage)
                })

            method_label = (
                "Percentage"
            )

        return {
            "success": True,

            "fields": {
                "description":
                    description,

                "amount":
                    float(amount_decimal),

                "paid_by_user_id":
                    payer["user_id"],

                "paid_by_username":
                    payer["username"],

                "paid_by_name":
                    payer["name"],

                "split_method":
                    method_label,

                "participant_count":
                    len(participants),

                "splits":
                    splits
            }
        }

    # =====================================
    # Create Group
    # =====================================

    def create_group(
        self,
        owner,
        group_name
    ):
        group_name = (
            group_name.strip()
        )

        if not group_name:
            return {
                "success": False,
                "message":
                    "Group name is required"
            }

        group_id = (
            "GRP-"
            + uuid4().hex[:10].upper()
        )

        group_data = {
            "group_id": group_id,
            "name": group_name,

            "owner_id":
                owner["_id"],

            "owner_username":
                owner["username"],

            "archived":
                False,

            "members": [
                {
                    "user_id":
                        owner["_id"],

                    "username":
                        owner["username"],

                    "name":
                        owner["name"]
                }
            ]
        }

        self.database.create_group(
            group_data
        )

        return {
            "success": True,
            "group_id": group_id,
            "message":
                "Group created successfully"
        }

    # =====================================
    # Add Member
    # =====================================

    def add_member(
        self,
        group_id,
        username,
        current_user_id
    ):
        username = (
            username.strip()
        )

        if not username:
            return {
                "success": False,
                "message":
                    "Username is required"
            }

        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if group.get(
            "archived",
            False
        ):
            return {
                "success": False,
                "message":
                    "Archived groups cannot be modified"
            }

        if (
            group["owner_id"]
            != current_user_id
        ):
            return {
                "success": False,
                "message":
                    "Only the group owner can add members"
            }

        user = (
            self.database.find_user(
                username
            )
        )

        if not user:
            return {
                "success": False,
                "message":
                    "User not found"
            }

        for member in group["members"]:
            if (
                member["user_id"]
                == user["_id"]
            ):
                return {
                    "success": False,
                    "message":
                        "User is already in this group"
                }

        member_data = {
            "user_id":
                user["_id"],

            "username":
                user["username"],

            "name":
                user["name"]
        }

        success = (
            self.database
            .add_group_member(
                group_id=group_id,
                member_data=member_data
            )
        )

        if success:
            return {
                "success": True,
                "message":
                    f"{user['name']} added successfully"
            }

        return {
            "success": False,
            "message":
                "Failed to add member"
        }

    # =====================================
    # Add Expense
    # =====================================

    def add_expense(
        self,
        group_id,
        paid_by_username,
        description,
        amount,
        current_user_id,
        split_method="equal",
        participant_usernames=None,
        custom_values=None
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if group.get(
            "archived",
            False
        ):
            return {
                "success": False,
                "message":
                    "Archived groups cannot accept new expenses"
            }

        current_member = None

        for member in group["members"]:
            if (
                member["user_id"]
                == current_user_id
            ):
                current_member = member
                break

        if not current_member:
            return {
                "success": False,
                "message":
                    "You are not a member of this group"
            }

        result = (
            self._build_expense_fields(
                group=group,

                paid_by_username=(
                    paid_by_username
                ),

                description=description,

                amount=amount,

                split_method=split_method,

                participant_usernames=(
                    participant_usernames
                ),

                custom_values=custom_values
            )
        )

        if not result["success"]:
            return result

        expense_id = (
            "GEXP-"
            + uuid4().hex[:10].upper()
        )

        expense_data = {
            "expense_id":
                expense_id,

            "group_id":
                group_id,

            **result["fields"],

            "created_by_user_id":
                current_user_id,

            "created_by_username":
                current_member["username"],

            "created_by_name":
                current_member["name"]
        }

        self.database.add_group_expense(
            expense_data
        )

        return {
            "success": True,

            "expense_id":
                expense_id,

            "message": (
                "Shared expense added "
                "successfully"
            )
        }

    # =====================================
    # Expense Modification Permission
    # =====================================

    def can_modify_expense(
        self,
        group,
        expense,
        current_user_id
    ):
        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if not expense:
            return {
                "success": False,
                "message":
                    "Expense not found"
            }

        if group.get(
            "archived",
            False
        ):
            return {
                "success": False,
                "message":
                    "Archived group expenses cannot be changed"
            }

        is_member = any(
            member["user_id"]
            == current_user_id
            for member in group["members"]
        )

        if not is_member:
            return {
                "success": False,
                "message":
                    "You are not a member of this group"
            }

        # Important ledger protection
        if (
            self.database
            .has_group_settlements(
                group["group_id"]
            )
        ):
            return {
                "success": False,
                "message": (
                    "Expense editing is locked because "
                    "wallet settlements have already "
                    "been made in this group"
                )
            }

        is_owner = (
            group["owner_id"]
            == current_user_id
        )

        is_creator = (
            expense.get(
                "created_by_user_id"
            )
            == current_user_id
        )

        if not (
            is_owner
            or is_creator
        ):
            return {
                "success": False,
                "message": (
                    "Only the group owner or "
                    "the expense creator can change it"
                )
            }

        return {
            "success": True,
            "message":
                "Expense can be modified"
        }

    # =====================================
    # Edit Expense
    # =====================================

    def edit_expense(
        self,
        group_id,
        expense_id,
        current_user,
        paid_by_username,
        description,
        amount,
        split_method,
        participant_usernames,
        custom_values
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        expense = (
            self.database
            .get_group_expense_by_id(
                group_id,
                expense_id
            )
        )

        permission = (
            self.can_modify_expense(
                group,
                expense,
                current_user["_id"]
            )
        )

        if not permission["success"]:
            return permission

        result = (
            self._build_expense_fields(
                group=group,

                paid_by_username=(
                    paid_by_username
                ),

                description=description,

                amount=amount,

                split_method=split_method,

                participant_usernames=(
                    participant_usernames
                ),

                custom_values=custom_values
            )
        )

        if not result["success"]:
            return result

        update_data = {
            **result["fields"],

            "updated_at":
                datetime.now(),

            "last_edited_by_user_id":
                current_user["_id"],

            "last_edited_by_username":
                current_user["username"]
        }

        success = (
            self.database
            .update_group_expense(
                group_id,
                expense_id,
                update_data
            )
        )

        return {
            "success": success,

            "message": (
                "Expense updated successfully"
                if success
                else
                "Could not update expense"
            )
        }

    # =====================================
    # Delete Expense
    # =====================================

    def delete_expense(
        self,
        group_id,
        expense_id,
        current_user
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        expense = (
            self.database
            .get_group_expense_by_id(
                group_id,
                expense_id
            )
        )

        permission = (
            self.can_modify_expense(
                group,
                expense,
                current_user["_id"]
            )
        )

        if not permission["success"]:
            return permission

        success = (
            self.database
            .delete_group_expense(
                group_id,
                expense_id
            )
        )

        return {
            "success": success,

            "message": (
                "Expense deleted successfully"
                if success
                else
                "Could not delete expense"
            )
        }

    # =====================================
    # Calculate Balances
    # =====================================

    def calculate_balances(
        self,
        group,
        expenses,
        settlements=None
    ):
        if settlements is None:
            settlements = []

        balances = {}
        member_info = {}

        for member in group["members"]:
            key = str(
                member["user_id"]
            )

            balances[key] = 0.0

            member_info[key] = {
                "name":
                    member["name"],

                "username":
                    member["username"]
            }

        # Expenses
        for expense in expenses:
            payer_key = str(
                expense[
                    "paid_by_user_id"
                ]
            )

            if payer_key in balances:
                balances[payer_key] += (
                    float(
                        expense["amount"]
                    )
                )

            for split in expense.get(
                "splits",
                []
            ):
                member_key = str(
                    split["user_id"]
                )

                if member_key in balances:
                    balances[
                        member_key
                    ] -= float(
                        split["share"]
                    )

        # Settlements
        for settlement in settlements:
            sender_key = str(
                settlement[
                    "from_user_id"
                ]
            )

            receiver_key = str(
                settlement[
                    "to_user_id"
                ]
            )

            amount = float(
                settlement["amount"]
            )

            if sender_key in balances:
                balances[
                    sender_key
                ] += amount

            if receiver_key in balances:
                balances[
                    receiver_key
                ] -= amount

        result = []

        for user_id, balance in (
            balances.items()
        ):
            result.append({
                "user_id": user_id,

                "name":
                    member_info[
                        user_id
                    ]["name"],

                "username":
                    member_info[
                        user_id
                    ]["username"],

                "balance":
                    round(
                        balance,
                        2
                    )
            })

        return result

    # =====================================
    # Calculate Debts
    # =====================================

    def calculate_debts(
        self,
        balances
    ):
        creditors = []
        debtors = []

        for member in balances:
            balance = round(
                member["balance"],
                2
            )

            if balance > 0.009:
                creditors.append({
                    "name":
                        member["name"],

                    "username":
                        member["username"],

                    "amount":
                        balance
                })

            elif balance < -0.009:
                debtors.append({
                    "name":
                        member["name"],

                    "username":
                        member["username"],

                    "amount":
                        abs(balance)
                })

        creditors.sort(
            key=lambda item: item[
                "amount"
            ],
            reverse=True
        )

        debtors.sort(
            key=lambda item: item[
                "amount"
            ],
            reverse=True
        )

        debts = []

        creditor_index = 0
        debtor_index = 0

        while (
            creditor_index
            < len(creditors)
            and
            debtor_index
            < len(debtors)
        ):
            creditor = creditors[
                creditor_index
            ]

            debtor = debtors[
                debtor_index
            ]

            amount = round(
                min(
                    creditor["amount"],
                    debtor["amount"]
                ),
                2
            )

            if amount > 0:
                debts.append({
                    "from_name":
                        debtor["name"],

                    "from_username":
                        debtor["username"],

                    "to_name":
                        creditor["name"],

                    "to_username":
                        creditor["username"],

                    "amount":
                        amount
                })

            creditor["amount"] = round(
                creditor["amount"]
                - amount,
                2
            )

            debtor["amount"] = round(
                debtor["amount"]
                - amount,
                2
            )

            if (
                creditor["amount"]
                <= 0.009
            ):
                creditor_index += 1

            if (
                debtor["amount"]
                <= 0.009
            ):
                debtor_index += 1

        return debts

    # =====================================
    # Current Group Debts
    # =====================================

    def get_group_debts(
        self,
        group
    ):
        expenses = (
            self.database
            .get_group_expenses(
                group["group_id"]
            )
        )

        settlements = (
            self.database
            .get_group_settlements(
                group["group_id"]
            )
        )

        balances = (
            self.calculate_balances(
                group,
                expenses,
                settlements
            )
        )

        return self.calculate_debts(
            balances
        )

    # =====================================
    # Partial / Full Settlement
    # =====================================

    def settle_debt(
        self,
        group_id,
        payer_document,
        receiver_username,
        amount,
        pin
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if group.get(
            "archived",
            False
        ):
            return {
                "success": False,
                "message":
                    "Archived groups cannot accept settlements"
            }

        payer_is_member = any(
            member["user_id"]
            == payer_document["_id"]
            for member in group["members"]
        )

        if not payer_is_member:
            return {
                "success": False,
                "message":
                    "You are not a member of this group"
            }

        payer_user = (
            User.from_document(
                payer_document
            )
        )

        if not payer_user.check_pin(
            pin
        ):
            return {
                "success": False,
                "message":
                    "Incorrect PIN"
            }

        # Always calculate the debt again
        # from the database.
        debts = (
            self.get_group_debts(
                group
            )
        )

        target_debt = None

        for debt in debts:
            if (
                debt["from_username"]
                == payer_document[
                    "username"
                ]
                and
                debt["to_username"]
                == receiver_username
            ):
                target_debt = debt
                break

        if not target_debt:
            return {
                "success": False,
                "message":
                    "No outstanding debt found"
            }

        debt_amount = self._money(
            target_debt["amount"]
        )

        payment_amount = self._money(
            amount
        )

        if (
            payment_amount is None
            or payment_amount <= 0
        ):
            return {
                "success": False,
                "message":
                    "Payment amount must be greater than zero"
            }

        if (
            payment_amount
            > debt_amount
        ):
            return {
                "success": False,
                "message": (
                    "You cannot pay more than "
                    f"{debt_amount:.2f} EGP"
                )
            }

        receiver = (
            self.database.find_user(
                receiver_username
            )
        )

        if not receiver:
            return {
                "success": False,
                "message":
                    "Receiver account not found"
            }

        payment_float = float(
            payment_amount
        )

        transfer_result = (
            self.database.transfer_funds(
                sender_id=(
                    payer_document["_id"]
                ),

                receiver_id=(
                    receiver["_id"]
                ),

                amount=payment_float
            )
        )

        if not transfer_result:
            return {
                "success": False,
                "message":
                    "Insufficient wallet balance"
            }

        remaining = (
            debt_amount
            - payment_amount
        ).quantize(
            self.MONEY_STEP,
            rounding=ROUND_HALF_UP
        )

        settlement_id = (
            "SET-"
            + uuid4().hex[:10].upper()
        )

        settlement_date = (
            datetime.now()
        )

        settlement_data = {
            "settlement_id":
                settlement_id,

            "group_id":
                group_id,

            "from_user_id":
                payer_document["_id"],

            "from_username":
                payer_document[
                    "username"
                ],

            "from_name":
                payer_document["name"],

            "to_user_id":
                receiver["_id"],

            "to_username":
                receiver["username"],

            "to_name":
                receiver["name"],

            "amount":
                payment_float,

            "was_partial":
                remaining > 0,

            "remaining_after":
                float(remaining),

            "date":
                settlement_date
        }

        try:
            self.database.add_group_settlement(
                settlement_data
            )

        except Exception:
            self.database.transfer_funds(
                sender_id=receiver["_id"],

                receiver_id=(
                    payer_document["_id"]
                ),

                amount=payment_float
            )

            return {
                "success": False,
                "message":
                    "Settlement could not be recorded"
            }

        # Existing Dashboard already knows
        # Transfer Sent / Transfer Received,
        # so settlements will also display
        # with the correct + / - sign.

        sent_transaction = Transaction(
            "Transfer Sent",
            payment_float,
            (
                f"Group settlement to "
                f"{receiver['name']} "
                f"for {group['name']}"
            )
        )

        sent_transaction.date = (
            settlement_date
        )

        self.database.add_transaction(
            user_id=(
                payer_document["_id"]
            ),

            transaction_type=(
                "Transfer Sent"
            ),

            amount=payment_float,

            description=(
                f"Group settlement to "
                f"{receiver['name']} "
                f"for {group['name']}"
            ),

            date=settlement_date,

            transaction_id=(
                sent_transaction
                .transaction_id
            ),

            status="Completed"
        )

        received_transaction = Transaction(
            "Transfer Received",
            payment_float,
            (
                f"Group settlement from "
                f"{payer_document['name']} "
                f"for {group['name']}"
            )
        )

        received_transaction.date = (
            settlement_date
        )

        self.database.add_transaction(
            user_id=receiver["_id"],

            transaction_type=(
                "Transfer Received"
            ),

            amount=payment_float,

            description=(
                f"Group settlement from "
                f"{payer_document['name']} "
                f"for {group['name']}"
            ),

            date=settlement_date,

            transaction_id=(
                received_transaction
                .transaction_id
            ),

            status="Completed"
        )

        if remaining > 0:
            message = (
                f"{payment_amount:.2f} EGP paid "
                f"to {receiver['name']}. "
                f"Remaining debt: "
                f"{remaining:.2f} EGP"
            )

        else:
            message = (
                f"{payment_amount:.2f} EGP paid "
                f"to {receiver['name']}. "
                "Debt settled completely."
            )

        return {
            "success": True,
            "message": message
        }

    # =====================================
    # Rename Group
    # =====================================

    def rename_group(
        self,
        group_id,
        owner_id,
        new_name
    ):
        new_name = (
            new_name.strip()
        )

        if not new_name:
            return {
                "success": False,
                "message":
                    "Group name is required"
            }

        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if (
            group["owner_id"]
            != owner_id
        ):
            return {
                "success": False,
                "message":
                    "Only the owner can rename this group"
            }

        success = (
            self.database.update_group_name(
                group_id,
                owner_id,
                new_name
            )
        )

        return {
            "success": success,

            "message": (
                "Group renamed successfully"
                if success
                else
                "Could not rename group"
            )
        }

    # =====================================
    # Archive Group
    # =====================================

    def archive_group(
        self,
        group_id,
        owner_id
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if (
            group["owner_id"]
            != owner_id
        ):
            return {
                "success": False,
                "message":
                    "Only the owner can archive this group"
            }

        debts = (
            self.get_group_debts(
                group
            )
        )

        if debts:
            return {
                "success": False,
                "message": (
                    "Settle all outstanding debts "
                    "before archiving the group"
                )
            }

        success = (
            self.database.archive_group(
                group_id,
                owner_id
            )
        )

        return {
            "success": success,

            "message": (
                "Group archived successfully"
                if success
                else
                "Could not archive group"
            )
        }

    # =====================================
    # Restore Group
    # =====================================

    def restore_group(
        self,
        group_id,
        owner_id
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if (
            group["owner_id"]
            != owner_id
        ):
            return {
                "success": False,
                "message":
                    "Only the owner can restore this group"
            }

        success = (
            self.database.restore_group(
                group_id,
                owner_id
            )
        )

        return {
            "success": success,

            "message": (
                "Group restored successfully"
                if success
                else
                "Could not restore group"
            )
        }

    # =====================================
    # Delete Group
    # =====================================

    def delete_group(
        self,
        group_id,
        owner_document,
        pin
    ):
        group = (
            self.database.get_group_by_id(
                group_id
            )
        )

        if not group:
            return {
                "success": False,
                "message":
                    "Group not found"
            }

        if (
            group["owner_id"]
            != owner_document["_id"]
        ):
            return {
                "success": False,
                "message":
                    "Only the owner can delete this group"
            }

        owner_user = (
            User.from_document(
                owner_document
            )
        )

        if not owner_user.check_pin(
            pin
        ):
            return {
                "success": False,
                "message":
                    "Incorrect PIN"
            }

        debts = (
            self.get_group_debts(
                group
            )
        )

        if debts:
            return {
                "success": False,
                "message": (
                    "Settle all outstanding debts "
                    "before deleting the group"
                )
            }

        success = (
            self.database
            .delete_group_and_data(
                group_id,
                owner_document["_id"]
            )
        )

        return {
            "success": success,

            "message": (
                "Group deleted permanently"
                if success
                else
                "Could not delete group"
            )
        }