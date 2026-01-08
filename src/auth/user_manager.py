
import json
import os
import hashlib
from datetime import datetime
from src.user.portfolio_manager import PortfolioManager

class UserManager:
    def __init__(self, storage_file="data/users.json"):
        self.storage_file = storage_file
        self.users = {}
        # Initialize Portfolio Manager
        self.portfolio_manager = PortfolioManager()
        self._load_users()

    def _load_users(self):
        """Loads users from JSON file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
        else:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            self.users = {}
            
        # Seed default user if empty to prevent lockout during migration
        if not self.users:
            print("Seeding default 'test' user...")
            self.register("test", "pass", "Test", "User", "test@example.com")

    def _save_users(self):
        """Saves users to JSON file."""
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4)
        except Exception as e:
            print(f"Error saving users: {e}")

    def _hash_password(self, password):
        """Basic hashing for security (prototype level)."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password, name, surname, email):
        """Registers a new user. Returns (Success, Message)."""
        if username in self.users:
            return False, "El nombre de usuario ya existe."
        
        # Basic validation
        if not username or not password:
            return False, "Usuario y contraseña son obligatorios."

        self.users[username] = {
            "username": username,
            "password_hash": self._hash_password(password),
            "name": name,
            "surname": surname,
            "email": email,
            "joined_at": datetime.now().isoformat(),
            "preferences": {
                "leagues": ['SP1', 'SP2', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1', 'N1'], # Default all
                "seasons": ['2526', '2425']
            }
        }
        self._save_users()
        return True, "Registro exitoso."

    def authenticate(self, username, password):
        """Authenticates a user. Returns User dict or None."""
        user = self.users.get(username)
        if not user:
            return None
        
        if user.get("password_hash") == self._hash_password(password):
            return user
        return None

    def update_profile(self, username, data):
        """Updates user profile data (name, surname, email, preferences)."""
        if username not in self.users:
            return False, "Usuario no encontrado."
        
        user = self.users[username]
        
        # Update allowed fields
        if "name" in data: user["name"] = data["name"]
        if "surname" in data: user["surname"] = data["surname"]
        if "email" in data: user["email"] = data["email"]
        if "preferences" in data: user["preferences"] = data["preferences"]
        
        self.users[username] = user
        self._save_users()
        return True, "Perfil actualizado."

    def get_user(self, username):
        return self.users.get(username)
