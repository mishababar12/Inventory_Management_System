from abc import ABC, abstractmethod
from datetime import datetime
import json

# ---------- Custom Exceptions ----------
class InventoryError(Exception): pass

class DuplicateProductError(InventoryError): pass
class OutOfStockError(InventoryError): pass
class InvalidProductDataError(InventoryError): pass

# ---------- Abstract Product Base Class ----------
class Product(ABC):
    def __init__(self, product_id, name, price, quantity_in_stock):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._quantity_in_stock = quantity_in_stock

    def restock(self, amount):
        self._quantity_in_stock += amount

    def sell(self, quantity):
        if quantity > self._quantity_in_stock:
            raise OutOfStockError(f"Only {self._quantity_in_stock} items in stock.")
        self._quantity_in_stock -= quantity

    def get_total_value(self):
        return self._price * self._quantity_in_stock

    @abstractmethod
    def __str__(self):
        pass

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "product_id": self._product_id,
            "name": self._name,
            "price": self._price,
            "quantity_in_stock": self._quantity_in_stock
        }

# ---------- Subclasses ----------
class Electronics(Product):
    def __init__(self, product_id, name, price, quantity_in_stock, warranty_years, brand):
        super().__init__(product_id, name, price, quantity_in_stock)
        self.warranty_years = warranty_years
        self.brand = brand

    def __str__(self):
        return f"[Electronics] {self._name} ({self._product_id}) - Brand: {self.brand}, Warranty: {self.warranty_years} yrs, Stock: {self._quantity_in_stock}, Price: {self._price}"

    def to_dict(self):
        base = super().to_dict()
        base.update({"warranty_years": self.warranty_years, "brand": self.brand})
        return base

class Grocery(Product):
    def __init__(self, product_id, name, price, quantity_in_stock, expiry_date):
        super().__init__(product_id, name, price, quantity_in_stock)
        self.expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()

    def is_expired(self):
        return datetime.now().date() > self.expiry_date

    def __str__(self):
        status = "Expired" if self.is_expired() else "Fresh"
        return f"[Grocery] {self._name} ({self._product_id}) - Expires: {self.expiry_date} ({status}), Stock: {self._quantity_in_stock}, Price: {self._price}"

    def to_dict(self):
        base = super().to_dict()
        base.update({"expiry_date": self.expiry_date.isoformat()})
        return base

class Clothing(Product):
    def __init__(self, product_id, name, price, quantity_in_stock, size, material):
        super().__init__(product_id, name, price, quantity_in_stock)
        self.size = size
        self.material = material

    def __str__(self):
        return f"[Clothing] {self._name} ({self._product_id}) - Size: {self.size}, Material: {self.material}, Stock: {self._quantity_in_stock}, Price: {self._price}"

    def to_dict(self):
        base = super().to_dict()
        base.update({"size": self.size, "material": self.material})
        return base

# ---------- Inventory Class ----------
class Inventory:
    def __init__(self):
        self._products = {}

    def add_product(self, product):
        if product._product_id in self._products:
            raise DuplicateProductError("Product ID already exists.")
        self._products[product._product_id] = product

    def remove_product(self, product_id):
        if product_id in self._products:
            del self._products[product_id]

    def search_by_name(self, name):
        return [p for p in self._products.values() if name.lower() in p._name.lower()]

    def search_by_type(self, product_type):
        return [p for p in self._products.values() if p.__class__.__name__.lower() == product_type.lower()]

    def list_all_products(self):
        return list(self._products.values())

    def sell_product(self, product_id, quantity):
        if product_id in self._products:
            self._products[product_id].sell(quantity)

    def restock_product(self, product_id, quantity):
        if product_id in self._products:
            self._products[product_id].restock(quantity)

    def total_inventory_value(self):
        return sum(p.get_total_value() for p in self._products.values())

    def remove_expired_products(self):
        to_remove = [pid for pid, p in self._products.items()
                     if isinstance(p, Grocery) and p.is_expired()]
        for pid in to_remove:
            del self._products[pid]

    def save_to_file(self, filename):
        with open(filename, "w") as f:
            json.dump([p.to_dict() for p in self._products.values()], f, indent=4)

    def load_from_file(self, filename):
        with open(filename, "r") as f:
            data = json.load(f)

        self._products.clear()
        for item in data:
            p_type = item["type"]
            try:
                if p_type == "Electronics":
                    product = Electronics(
                        item["product_id"], item["name"], item["price"],
                        item["quantity_in_stock"], item["warranty_years"], item["brand"]
                    )
                elif p_type == "Grocery":
                    product = Grocery(
                        item["product_id"], item["name"], item["price"],
                        item["quantity_in_stock"], item["expiry_date"]
                    )
                elif p_type == "Clothing":
                    product = Clothing(
                        item["product_id"], item["name"], item["price"],
                        item["quantity_in_stock"], item["size"], item["material"]
                    )
                else:
                    raise InvalidProductDataError(f"Unknown type: {p_type}")
                self.add_product(product)
            except KeyError:
                raise InvalidProductDataError("Missing fields in product data")

# ---------- CLI Menu (Command Line Interface) ----------
def main():
    inventory = Inventory()

    while True:
        print("\n========= Inventory Menu ========\n")
        print("1. Add Product")
        print("2. Sell Product")
        print("3. Search by Name")
        print("4. List All Products")
        print("5. Restock Product")
        print("6. Remove Expired Products")
        print("7. Save to File")
        print("8. Load from File")
        print("9. Total Inventory Value")
        print("0. Exit")

        choice = input("Enter choice: ")

        try:
            if choice == "1":
                ptype = input("Type (Electronics/Grocery/Clothing): ").strip()
                pid = input("Product ID: ")
                name = input("Name: ")
                price = float(input("Price: "))
                qty = int(input("Quantity: "))

                if ptype.lower() == "electronics":
                    brand = input("Brand: ")
                    warranty = int(input("Warranty (years): "))
                    product = Electronics(pid, name, price, qty, warranty, brand)
                elif ptype.lower() == "grocery":
                    expiry = input("Expiry Date (YYYY-MM-DD): ")
                    product = Grocery(pid, name, price, qty, expiry)
                elif ptype.lower() == "clothing":
                    size = input("Size: ")
                    material = input("Material: ")
                    product = Clothing(pid, name, price, qty, size, material)
                else:
                    print("Invalid product type.")
                    continue

                inventory.add_product(product)
                print("Product added.")

            elif choice == "2":
                pid = input("Product ID to sell: ")
                qty = int(input("Quantity: "))
                inventory.sell_product(pid, qty)
                print("Product sold.")

            elif choice == "3":
                name = input("Enter product name to search: ")
                results = inventory.search_by_name(name)
                for p in results:
                    print(p)

            elif choice == "4":
                for p in inventory.list_all_products():
                    print(p)

            elif choice == "5":
                pid = input("Product ID to restock: ")
                qty = int(input("Quantity to add: "))
                inventory.restock_product(pid, qty)
                print("Product restocked.")

            elif choice == "6":
                inventory.remove_expired_products()
                print("Expired groceries removed.")

            elif choice == "7":
                filename = input("Filename to save: ")
                inventory.save_to_file(filename)
                print("Inventory saved.")

            elif choice == "8":
                filename = input("Filename to load: ")
                inventory.load_from_file(filename)
                print("Inventory loaded.")

            elif choice == "9":
                value = inventory.total_inventory_value()
                print(f"Total inventory value: {value}")

            elif choice == "0":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Try again.")
        except InventoryError as e:
            print(f"Error: {e}")
        except Exception as ex:
            print(f"Unexpected error: {ex}")

if __name__ == "__main__":
    main()
