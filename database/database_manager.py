import os
from datetime import datetime

from pymongo import (
    MongoClient,
    ReturnDocument,
    ASCENDING
)

from pymongo.errors import (
    PyMongoError,
    DuplicateKeyError
)


class DatabaseManager:

    def __init__(self):
        mongo_uri = os.environ.get(
            "MONGODB_URI"
        )

        if not mongo_uri:
            raise RuntimeError(
                "MONGODB_URI environment variable is not set"
            )

        self.client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000
        )

        self.db = self.client[
            os.environ.get(
                "MONGODB_DB_NAME",
                "digital_wallet"
            )
        ]

        self.users = self.db["users"]
        self.transactions = self.db["transactions"]

        self.expenses = self.db["expenses"]
        self.budgets = self.db["budgets"]

        self.groups = self.db["groups"]
        self.group_expenses = self.db["group_expenses"]
        self.group_settlements = self.db["group_settlements"]

        # =====================================
        # Indexes
        # =====================================

        self.users.create_index(
            "username",
            unique=True
        )

        self.transactions.create_index(
            "transaction_id",
            unique=True,
            sparse=True
        )

        self.expenses.create_index(
            "expense_id",
            unique=True
        )

        self.expenses.create_index([
            ("user_id", ASCENDING),
            ("date", ASCENDING)
        ])

        self.budgets.create_index(
            [
                ("user_id", ASCENDING),
                ("month", ASCENDING)
            ],
            unique=True
        )

        self.groups.create_index(
            "group_id",
            unique=True
        )

        self.groups.create_index(
            "members.user_id"
        )

        self.group_expenses.create_index(
            "expense_id",
            unique=True
        )

        self.group_expenses.create_index([
            ("group_id", ASCENDING),
            ("date", ASCENDING)
        ])

        self.group_settlements.create_index(
            "settlement_id",
            unique=True
        )

        self.group_settlements.create_index([
            ("group_id", ASCENDING),
            ("date", ASCENDING)
        ])

    # =====================================
    # Connection
    # =====================================

    def test_connection(self):
        try:
            self.client.admin.command("ping")
            return True

        except PyMongoError as error:
            print(
                "MongoDB Connection Error:",
                error
            )
            return False

    # =====================================
    # Users
    # =====================================

    def add_user(self, user_data):
        try:
            result = self.users.insert_one(
                user_data
            )
            return result.inserted_id

        except DuplicateKeyError:
            return None

    def find_user(self, username):
        return self.users.find_one({
            "username": username
        })

    def update_user_pin(
        self,
        username,
        new_pin_hash
    ):
        result = self.users.update_one(
            {
                "username": username
            },
            {
                "$set": {
                    "pin_hash": new_pin_hash
                }
            }
        )

        return result.modified_count > 0

    # =====================================
    # Wallet
    # =====================================

    def deposit(
        self,
        user_id,
        amount
    ):
        user = self.users.find_one_and_update(
            {
                "_id": user_id
            },
            {
                "$inc": {
                    "balance": amount
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if user:
            return user["balance"]

        return None

    def withdraw(
        self,
        user_id,
        amount
    ):
        user = self.users.find_one_and_update(
            {
                "_id": user_id,
                "balance": {
                    "$gte": amount
                }
            },
            {
                "$inc": {
                    "balance": -amount
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if user:
            return user["balance"]

        return None

    def transfer_funds(
        self,
        sender_id,
        receiver_id,
        amount
    ):
        sender = self.users.find_one_and_update(
            {
                "_id": sender_id,
                "balance": {
                    "$gte": amount
                }
            },
            {
                "$inc": {
                    "balance": -amount
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if not sender:
            return None

        receiver = self.users.find_one_and_update(
            {
                "_id": receiver_id
            },
            {
                "$inc": {
                    "balance": amount
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if not receiver:
            self.users.update_one(
                {
                    "_id": sender_id
                },
                {
                    "$inc": {
                        "balance": amount
                    }
                }
            )

            return None

        return {
            "sender_balance": sender["balance"],
            "receiver_balance": receiver["balance"]
        }

    # =====================================
    # Transactions
    # =====================================

    def add_transaction(
        self,
        user_id,
        transaction_type,
        amount,
        description,
        date=None,
        transaction_id=None,
        status="Completed"
    ):
        transaction_data = {
            "user_id": user_id,
            "transaction_id": transaction_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "description": description,
            "status": status,
            "date": date or datetime.now()
        }

        result = self.transactions.insert_one(
            transaction_data
        )

        return result.inserted_id

    def get_transactions(
        self,
        user_id
    ):
        return list(
            self.transactions.find(
                {
                    "user_id": user_id
                }
            ).sort(
                "date",
                -1
            )
        )

    def get_transaction_by_id(
        self,
        user_id,
        transaction_id
    ):
        return self.transactions.find_one({
            "user_id": user_id,
            "transaction_id": transaction_id
        })

    # =====================================
    # Personal Expenses
    # =====================================

    def add_expense(
        self,
        user_id,
        expense_id,
        category,
        amount,
        note=""
    ):
        expense_data = {
            "user_id": user_id,
            "expense_id": expense_id,
            "category": category,
            "amount": amount,
            "note": note,
            "date": datetime.now()
        }

        result = self.expenses.insert_one(
            expense_data
        )

        return result.inserted_id

    # =====================================
    # Month
    # =====================================

    @staticmethod
    def get_month_range(month):
        start_date = datetime.strptime(
            month,
            "%Y-%m"
        )

        if start_date.month == 12:
            end_date = start_date.replace(
                year=start_date.year + 1,
                month=1
            )

        else:
            end_date = start_date.replace(
                month=start_date.month + 1
            )

        return start_date, end_date

    def get_expenses(
        self,
        user_id,
        month
    ):
        start_date, end_date = (
            self.get_month_range(month)
        )

        return list(
            self.expenses.find(
                {
                    "user_id": user_id,
                    "date": {
                        "$gte": start_date,
                        "$lt": end_date
                    }
                }
            ).sort(
                "date",
                -1
            )
        )

    # =====================================
    # Budget
    # =====================================

    def set_monthly_budget(
        self,
        user_id,
        month,
        amount
    ):
        result = self.budgets.update_one(
            {
                "user_id": user_id,
                "month": month
            },
            {
                "$set": {
                    "amount": amount,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )

        return (
            result.modified_count > 0
            or result.upserted_id is not None
            or result.matched_count > 0
        )

    def get_monthly_budget(
        self,
        user_id,
        month
    ):
        return self.budgets.find_one({
            "user_id": user_id,
            "month": month
        })

    # =====================================
    # Finance History
    # =====================================

    def get_available_finance_months(
        self,
        user_id
    ):
        months = set()

        budget_documents = self.budgets.find(
            {
                "user_id": user_id
            },
            {
                "_id": 0,
                "month": 1
            }
        )

        for document in budget_documents:
            month = document.get("month")

            if month:
                months.add(month)

        expense_documents = self.expenses.find(
            {
                "user_id": user_id
            },
            {
                "_id": 0,
                "date": 1
            }
        )

        for document in expense_documents:
            expense_date = document.get(
                "date"
            )

            if expense_date:
                months.add(
                    expense_date.strftime(
                        "%Y-%m"
                    )
                )

        return sorted(
            months,
            reverse=True
        )

    # =====================================
    # Groups
    # =====================================

    def create_group(
        self,
        group_data
    ):
        group_data["created_at"] = (
            datetime.now()
        )

        group_data.setdefault(
            "archived",
            False
        )

        result = self.groups.insert_one(
            group_data
        )

        return result.inserted_id

    def get_group_by_id(
        self,
        group_id
    ):
        return self.groups.find_one({
            "group_id": group_id
        })

    def get_user_groups(
        self,
        user_id,
        archived=False
    ):
        query = {
            "members.user_id": user_id
        }

        if archived:
            query["archived"] = True

        else:
            query["archived"] = {
                "$ne": True
            }

        return list(
            self.groups.find(
                query
            ).sort(
                "created_at",
                -1
            )
        )

    def add_group_member(
        self,
        group_id,
        member_data
    ):
        result = self.groups.update_one(
            {
                "group_id": group_id,
                "members.user_id": {
                    "$ne": member_data[
                        "user_id"
                    ]
                }
            },
            {
                "$push": {
                    "members": member_data
                }
            }
        )

        return result.modified_count > 0

    def update_group_name(
        self,
        group_id,
        owner_id,
        new_name
    ):
        result = self.groups.update_one(
            {
                "group_id": group_id,
                "owner_id": owner_id
            },
            {
                "$set": {
                    "name": new_name
                }
            }
        )

        return (
            result.modified_count > 0
            or result.matched_count > 0
        )

    def archive_group(
        self,
        group_id,
        owner_id
    ):
        result = self.groups.update_one(
            {
                "group_id": group_id,
                "owner_id": owner_id
            },
            {
                "$set": {
                    "archived": True,
                    "archived_at":
                        datetime.now()
                }
            }
        )

        return result.modified_count > 0

    def restore_group(
        self,
        group_id,
        owner_id
    ):
        result = self.groups.update_one(
            {
                "group_id": group_id,
                "owner_id": owner_id
            },
            {
                "$set": {
                    "archived": False
                },
                "$unset": {
                    "archived_at": ""
                }
            }
        )

        return result.modified_count > 0

    def delete_group_and_data(
        self,
        group_id,
        owner_id
    ):
        group = self.groups.find_one({
            "group_id": group_id,
            "owner_id": owner_id
        })

        if not group:
            return False

        self.group_expenses.delete_many({
            "group_id": group_id
        })

        self.group_settlements.delete_many({
            "group_id": group_id
        })

        result = self.groups.delete_one({
            "group_id": group_id,
            "owner_id": owner_id
        })

        return result.deleted_count > 0

    # =====================================
    # Group Expenses
    # =====================================

    def add_group_expense(
        self,
        expense_data
    ):
        expense_data["date"] = (
            datetime.now()
        )

        result = (
            self.group_expenses.insert_one(
                expense_data
            )
        )

        return result.inserted_id

    def get_group_expenses(
        self,
        group_id
    ):
        return list(
            self.group_expenses.find(
                {
                    "group_id": group_id
                }
            ).sort(
                "date",
                -1
            )
        )

    def get_group_expense_by_id(
        self,
        group_id,
        expense_id
    ):
        return self.group_expenses.find_one({
            "group_id": group_id,
            "expense_id": expense_id
        })

    def update_group_expense(
        self,
        group_id,
        expense_id,
        update_data
    ):
        result = self.group_expenses.update_one(
            {
                "group_id": group_id,
                "expense_id": expense_id
            },
            {
                "$set": update_data
            }
        )

        return (
            result.modified_count > 0
            or result.matched_count > 0
        )

    def delete_group_expense(
        self,
        group_id,
        expense_id
    ):
        result = self.group_expenses.delete_one({
            "group_id": group_id,
            "expense_id": expense_id
        })

        return result.deleted_count > 0

    # =====================================
    # Group Settlements
    # =====================================

    def add_group_settlement(
        self,
        settlement_data
    ):
        result = (
            self.group_settlements.insert_one(
                settlement_data
            )
        )

        return result.inserted_id

    def get_group_settlements(
        self,
        group_id
    ):
        return list(
            self.group_settlements.find(
                {
                    "group_id": group_id
                }
            ).sort(
                "date",
                -1
            )
        )

    def has_group_settlements(
        self,
        group_id
    ):
        return (
            self.group_settlements.count_documents(
                {
                    "group_id": group_id
                }
            )
            > 0
        )

    # =====================================
    # Close
    # =====================================

    def close_connection(self):
        self.client.close()