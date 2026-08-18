from models.transaction import Transaction


class WalletService:

    def __init__(self, database):
        self.database = database

    # =====================================
    # Deposit
    # =====================================

    def deposit(
        self,
        user,
        amount
    ):

        if amount <= 0:
            print("Invalid amount")
            return None

        new_balance = self.database.deposit(
            user.id,
            amount
        )

        if new_balance is None:
            print("Deposit failed")
            return None

        # Update wallet object
        user.wallet.sync_balance(
            new_balance
        )

        # Create transaction
        transaction = Transaction(
            "Deposit",
            amount,
            "Money deposited"
        )

        user.wallet.add_transaction(
            transaction
        )

        # Save in MongoDB
        self.database.add_transaction(
            user_id=user.id,
            transaction_type="Deposit",
            amount=amount,
            description="Money deposited",
            date=transaction.date,
            transaction_id=transaction.transaction_id,
            status=transaction.status
        )

        print("Deposit successful")

        return transaction.transaction_id

    # =====================================
    # Withdraw
    # =====================================

    def withdraw(
        self,
        user,
        amount
    ):

        if amount <= 0:
            print("Invalid amount")
            return None

        if amount > user.wallet.get_balance():
            print("Insufficient balance")
            return None

        new_balance = self.database.withdraw(
            user.id,
            amount
        )

        if new_balance is None:
            print("Withdraw failed")
            return None

        user.wallet.sync_balance(
            new_balance
        )

        transaction = Transaction(
            "Withdraw",
            amount,
            "Money withdrawn"
        )

        user.wallet.add_transaction(
            transaction
        )

        self.database.add_transaction(
            user_id=user.id,
            transaction_type="Withdraw",
            amount=amount,
            description="Money withdrawn",
            date=transaction.date,
            transaction_id=transaction.transaction_id,
            status=transaction.status
        )

        print("Withdraw successful")

        return transaction.transaction_id

    # =====================================
    # Transfer
    # =====================================

    def transfer(
        self,
        sender_user,
        receiver_username,
        amount,
        pin
    ):

        if amount <= 0:
            print("Invalid transfer amount")
            return None

        # Check PIN
        if not sender_user.check_pin(pin):

            print("Incorrect PIN")
            return None

        # Prevent transfer to yourself
        if (
            sender_user.username
            == receiver_username
        ):

            print(
                "You cannot transfer money to yourself"
            )

            return None

        # Find receiver
        receiver = self.database.find_user(
            receiver_username
        )

        if not receiver:

            print("Receiver not found")
            return None

        # Check balance
        if (
            amount
            > sender_user.wallet.get_balance()
        ):

            print("Insufficient balance")
            return None

        # Transfer balances in MongoDB
        result = self.database.transfer_funds(
            sender_id=sender_user.id,
            receiver_id=receiver["_id"],
            amount=amount
        )

        if not result:

            print("Transfer failed")
            return None

        # Update sender wallet object
        sender_user.wallet.sync_balance(
            result["sender_balance"]
        )

        # -----------------------------
        # Sender Transaction
        # -----------------------------

        sender_transaction = Transaction(
            "Transfer Sent",
            amount,
            f"To {receiver['name']}"
        )

        sender_user.wallet.add_transaction(
            sender_transaction
        )

        self.database.add_transaction(
            user_id=sender_user.id,
            transaction_type="Transfer Sent",
            amount=amount,
            description=f"To {receiver['name']}",
            date=sender_transaction.date,
            transaction_id=(
                sender_transaction.transaction_id
            ),
            status=sender_transaction.status
        )

        # -----------------------------
        # Receiver Transaction
        # -----------------------------

        receiver_transaction = Transaction(
            "Transfer Received",
            amount,
            f"From {sender_user.name}"
        )

        self.database.add_transaction(
            user_id=receiver["_id"],
            transaction_type="Transfer Received",
            amount=amount,
            description=f"From {sender_user.name}",
            date=receiver_transaction.date,
            transaction_id=(
                receiver_transaction.transaction_id
            ),
            status=receiver_transaction.status
        )

        print(
            f"Transfer successful: "
            f"{amount} EGP sent to "
            f"{receiver['name']}"
        )

        return (
            sender_transaction.transaction_id
        )

    # =====================================
    # Wallet Payment
    # =====================================

    def make_wallet_payment(
        self,
        user,
        amount
    ):

        if amount <= 0:

            print("Invalid payment amount")
            return None

        if amount > user.wallet.get_balance():

            print("Insufficient balance")
            return None

        # Deduct from balance
        new_balance = self.database.withdraw(
            user.id,
            amount
        )

        if new_balance is None:

            print("Payment failed")
            return None

        # Update Wallet object
        user.wallet.sync_balance(
            new_balance
        )

        transaction = Transaction(
            "Wallet Payment",
            amount,
            "Payment using wallet"
        )

        user.wallet.add_transaction(
            transaction
        )

        self.database.add_transaction(
            user_id=user.id,
            transaction_type="Wallet Payment",
            amount=amount,
            description="Payment using wallet",
            date=transaction.date,
            transaction_id=transaction.transaction_id,
            status=transaction.status
        )

        print("Wallet payment successful")

        return transaction.transaction_id

    # =====================================
    # Transaction History
    # =====================================

    def show_transactions(
        self,
        user
    ):

        transactions = (
            self.database.get_transactions(
                user.id
            )
        )

        print(
            "\n--- Transaction History ---"
        )

        if not transactions:

            print("No transactions yet")
            return

        for transaction in transactions:

            print(
                transaction.get(
                    "transaction_id",
                    "OLD"
                ),
                "|",
                transaction[
                    "transaction_type"
                ],
                "|",
                transaction["amount"],
                "EGP |",
                transaction[
                    "description"
                ],
                "|",
                transaction.get(
                    "status",
                    "Completed"
                ),
                "|",
                transaction[
                    "date"
                ].strftime(
                    "%d/%m/%Y %H:%M"
                )
            )