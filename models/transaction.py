from datetime import datetime
from uuid import uuid4


class Transaction:

    def __init__(
        self,
        transaction_type,
        amount,
        description="",
        status="Completed"
    ):
        self.transaction_id = (
            "TXN-" + uuid4().hex[:10].upper()
        )

        self.transaction_type = transaction_type
        self.amount = amount
        self.description = description
        self.status = status
        self.date = datetime.now()

    def display(self):
        return (
            f"{self.transaction_id} | "
            f"{self.transaction_type} | "
            f"{self.amount} EGP | "
            f"{self.status} | "
            f"{self.description} | "
            f"{self.date.strftime('%d/%m/%Y %H:%M')}"
        )