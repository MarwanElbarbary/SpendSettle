from services.security_manager import SecurityManager
from models.user import User
class AuthService:
    def __init__(self, database):
        self.database = database

    def register(self, name, username, phone, pin):

        # Check empty fields
        if not name or not username or not phone or not pin:
            print("All fields are required")
            return False

        # PIN validation
        if not pin.isdigit() or len(pin) != 4:
            print("PIN must be exactly 4 digits")
            return False

        # Check username
        existing_user = self.database.find_user(username)

        if existing_user:
            print("Username already exists")
            return False

        # Hash PIN
        pin_hash = SecurityManager.hash_pin(pin)

        user_data = {
            "name": name,
            "username": username,
            "phone": phone,
            "pin_hash": pin_hash,
            "balance": 0
        }

        user_id = self.database.add_user(user_data)

        if user_id:
            print("Registration successful")
            return True

        print("Registration failed")
        return False

    def login(self, username, pin):

        user = self.database.find_user(username)

        if not user:
            print("User not found")
            return None

        if not SecurityManager.verify_pin(
            pin,
            user["pin_hash"]
        ):
            print("Incorrect PIN")
            return None

        print("Login successful")

        return User.from_document(user)