"""Data models for the application."""


class User:
    """Represents a user in the system."""

    _id_counter = 0

    def __init__(self, name: str, email: str):
        User._id_counter += 1
        self.id = User._id_counter
        self.name = name
        self.email = email

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"


class Product:
    """Represents a product in the system."""

    _id_counter = 0

    def __init__(self, name: str, price: float):
        Product._id_counter += 1
        self.id = Product._id_counter
        self.name = name
        self.price = price

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name}, price={self.price})"


# TODO: Add Order model
# TODO: Add Category model

