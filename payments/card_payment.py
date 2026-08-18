from payments.payment_method import PaymentMethod
from models.transaction import Transaction


class CardPayment(PaymentMethod):

    def __init__(
        self,
        user,
        card_number,
        database
    ):
        self.user = user
        self.card_number = card_number
        self.database = database

    def pay(
        self,
        amount
    ):

        card_number = (
            self.card_number.replace(
                " ",
                ""
            )
        )

        # Check amount
        if amount <= 0:

            return {
                "success": False,
                "message":
                    "Invalid payment amount"
            }

        # Validate card number
        if (
            not card_number.isdigit()
            or len(card_number) < 13
            or len(card_number) > 19
        ):

            return {
                "success": False,
                "message":
                    "Invalid card number"
            }

        last_four = card_number[-4:]

        # Create transaction
        transaction = Transaction(
            "Card Payment",
            amount,
            f"Card ending with {last_four}"
        )

        # Save only last 4 digits
        self.database.add_transaction(
            user_id=self.user.id,
            transaction_type="Card Payment",
            amount=amount,
            description=(
                f"Card ending with {last_four}"
            ),
            date=transaction.date,
            transaction_id=(
                transaction.transaction_id
            ),
            status=transaction.status
        )

        return {
            "success": True,

            "message": (
                f"{amount:g} EGP "
                f"paid successfully "
                f"using Card ****{last_four}"
            ),

            "transaction_id":
                transaction.transaction_id
        }