from models.transaction import Transaction


class Wallet:
    def __init__(self, balance=0):
        self.__balance = balance
        self.transactions = []

    def get_balance(self):
        return self.__balance

    def sync_balance(self, new_balance):
        self.__balance = new_balance

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def deposit(self, amount):
        if amount <= 0:
            print("Invalid amount")
            return False

        self.__balance += amount

        transaction = Transaction(
            "Deposit",
            amount,
            "Money deposited"
        )

        self.transactions.append(transaction)
        return True

    def withdraw(self, amount):
        if amount <= 0:
            print("Invalid amount")
            return False

        if amount > self.__balance:
            print("Insufficient balance")
            return False

        self.__balance -= amount

        transaction = Transaction(
            "Withdraw",
            amount,
            "Money withdrawn"
        )

        self.transactions.append(transaction)
        return True

    def transfer(self, target_wallet, amount, sender_name, receiver_name):
        if amount <= 0:
            print("Invalid transfer amount")
            return False

        if amount > self.__balance:
            print("Insufficient balance")
            return False

        self.__balance -= amount
        target_wallet.__balance += amount

        sender_transaction = Transaction(
            "Transfer Sent",
            amount,
            f"To {receiver_name}"
        )

        receiver_transaction = Transaction(
            "Transfer Received",
            amount,
            f"From {sender_name}"
        )

        self.transactions.append(sender_transaction)
        target_wallet.transactions.append(receiver_transaction)

        return True

    def show_transactions(self):
        if not self.transactions:
            print("No transactions yet")
            return

        for transaction in self.transactions:
            print(transaction.display())