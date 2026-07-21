products = [
    "Bananas",
    "Avocados",
    "Spinach",
    "Red Bell Peppers",
    "Yellow Onions",
    "Garlic",
    "Lemons",
    "Russet Potatoes",
    "Cherry Tomatoes",
    "Fresh Strawberries",
    "Large White Eggs",
    "Whole Milk",
    "Unsalted Butter",
    "Plain Greek Yogurt",
    "Sharp Cheddar Cheese",
    "Cream Cheese",
    "Sour Cream",
    "Oat Milk",
    "Boneless Skinless Chicken Breasts",
    "80/20 Ground Beef",
    "Center-Cut Bacon",
    "Atlantic Salmon Fillets",
    "Large Shrimp",
    "Oven-Roasted Turkey Breast",
    "Genoa Salami",
    "Long-Grain White Rice",
    "Spaghetti Pasta",
    "All-Purpose Flour",
    "Granulated White Sugar",
    "Old-Fashioned Rolled Oats",
    "Peanut Butter",
    "Strawberry Jam",
    "Extra Virgin Olive Oil",
    "Balsamic Vinegar",
    "Soy Sauce",
    "Diced Tomatoes",
    "Canned Black Beans",
    "Chicken Broth",
    "Tuna in Water",
    "Sliced White Sandwich Bread",
    "Flour Tortillas",
    "Plain Bagels",
    "Corn Flakes Cereal",
    "Frozen Sweet Corn",
    "Frozen French Fries",
    "Vanilla Ice Cream",
    "Cheese Pizza",
    "Salted Potato Chips",
    "Dark Chocolate Bar",
    "Ground Coffee"
]

import datetime
import random

# Fix: Use datetime.datetime.now() instead of datetime.now()
now = datetime.datetime.now()
ts = int(now.timestamp())
random.seed(ts)

def make_shoping_cart():
    global products
    cart=[]
    mask = random.randint(0, (1 << len(products)) - 1) 
    for i in range(len(products)):
        if mask & (1 << i):
            cart.append(products[i])
    with open("data.txt", "a") as file: 
        for c in cart:
            file.write(c + ",")
        file.write("\n")

for i in range(2001):
    make_shoping_cart()