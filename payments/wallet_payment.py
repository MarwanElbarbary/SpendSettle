from payments.payment_method import PaymentMethod


class WalletPayment(PaymentMethod):

    def __init__(
        self,
        user,
        pin,
        wallet_service
    ):
        self.user = user
        self.pin = pin
        self.wallet_service = wallet_service

    def pay(
        self,
        amount
    ):

        # Check PIN
        if not self.user.check_pin(
            self.pin
        ):

            return {
                "success": False,
                "message": "Incorrect PIN"
            }

        transaction_id = (
            self.wallet_service.make_wallet_payment(
                self.user,
                amount
            )
        )

        if transaction_id:

            return {
                "success": True,

                "message": (
                    f"{amount:g} EGP "
                    f"paid successfully "
                    f"using Wallet"
                ),

                "transaction_id":
                    transaction_id
            }

        return {
            "success": False,
            "message": (
                "Payment failed. "
                "Check your balance."
            )
        }