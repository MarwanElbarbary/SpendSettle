import hashlib


class SecurityManager:

    @staticmethod
    def hash_pin(pin):
        return hashlib.sha256(pin.encode()).hexdigest()

    @staticmethod
    def verify_pin(entered_pin, stored_pin_hash):
        entered_pin_hash = SecurityManager.hash_pin(entered_pin)

        return entered_pin_hash == stored_pin_hash