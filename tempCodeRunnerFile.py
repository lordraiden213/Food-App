from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Dummy item data
items = [
    {"name": "Burger", "price": 89, "image": "burger.jpg"},
    {"name": "Pizza", "price": 149, "image": "pizza.jpg"},
    {"name": "Milk Tea", "price": 99, "image": "milktea.jpg"},
    {"name": "Fries", "price": 59, "image": "fries.jpg"},
    {"name": "Hotdog", "price": 79, "image": "hotdog.jpg"},
    {"name": "Spaghetti", "price": 129, "image": "spaghetti.jpg"},
    {"name": "Donut", "price": 45, "image": "donut.jpg"},
]

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/menu')
def menu():
    return render_template("menu.html", items=items)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    item_name = data.get('item_name')
    quantity = int(data.get('quantity', 1))

    cart = session.get('cart', [])

    for item in cart:
        if item['name'] == item_name:
            item['quantity'] += quantity
            break
    else:
        cart.append({'name': item_name, 'quantity': quantity})

    session['cart'] = cart
    total_items = sum(i['quantity'] for i in cart)
    return jsonify({'success': True, 'cart_count': total_items})

@app.route('/cart')
def cart():
    return render_template("cart.html", cart=session.get('cart', []))

@app.route('/remove/<item_name>')
def remove_from_cart(item_name):
    cart = session.get('cart', [])
    updated_cart = [item for item in cart if item['name'] != item_name]
    session['cart'] = updated_cart
    return redirect(url_for('cart'))

@app.route('/cart-count')
def cart_count():
    cart = session.get('cart', [])
    count = sum(item['quantity'] for item in cart)
    return jsonify({'count': count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
