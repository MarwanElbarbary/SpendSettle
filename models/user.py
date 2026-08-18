from models.wallet import Wallet
from services.security_manager import SecurityManager


class User:
    def __init__(
        self,
        name,
        username,
        phone,
        pin=None,
        user_id=None,
        balance=0,
        pin_hash=None
    ):
        self.id = user_id
        self.name = name
        self.username = username
        self.phone = phone

        if pin_hash:
            self.__pin_hash = pin_hash
        elif pin:
            self.__pin_hash = SecurityManager.hash_pin(pin)
        else:
            self.__pin_hash = None

        self.wallet = Wallet(balance)

    @classmethod
    def from_document(cls, document):
        return cls(
            user_id=document["_id"],
            name=document["name"],
            username=document["username"],
            phone=document["phone"],
            pin_hash=document["pin_hash"],
            balance=document.get("balance", 0)
        )

    def check_pin(self, entered_pin):
        return SecurityManager.verify_pin(
            entered_pin,
            self.__pin_hash
        )

    def display_info(self):
        print("\n--- User Information ---")
        print("Name:", self.name)
        print("Username:", self.username)
        print("Phone:", self.phone)
        print("Balance:", self.wallet.get_balance(), "EGP")