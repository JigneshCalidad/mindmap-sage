"""Service module for handling business logic."""

from typing import List, Optional
from models import User, Product


class UserService:
    """Service for managing users."""

    def __init__(self):
        self.users: List[User] = []

    def create_user(self, name: str, email: str) -> User:
        """Create a new user."""
        user = User(name=name, email=email)
        self.users.append(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        for user in self.users:
            if user.id == user_id:
                return user
        return None

    def list_users(self) -> List[User]:
        """List all users."""
        return self.users.copy()


class ProductService:
    """Service for managing products."""

    def __init__(self):
        self.products: List[Product] = []

    def add_product(self, name: str, price: float) -> Product:
        """Add a new product."""
        product = Product(name=name, price=price)
        self.products.append(product)
        return product

    def find_product(self, product_id: int) -> Optional[Product]:
        """Find product by ID."""
        for product in self.products:
            if product.id == product_id:
                return product
        return None


# TODO: Add authentication service
# TODO: Implement caching layer

