from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your-secret-key'

# Order statuses
ORDER_STATUSES = ['Order Received', 'Preparing Food', 'Food Ready', 'Out for Delivery', 'Delivered']

# Delivery service riders with ratings
DELIVERY_SERVICES = {
    'Grab': [
        {'name': 'Juan Dela Cruz', 'rating': 4.8},
        {'name': 'Mark Santos', 'rating': 4.9},
        {'name': 'Carlo Garcia', 'rating': 4.7}
    ],
    'Foodpanda': [
        {'name': 'Pedro Reyes', 'rating': 4.8},
        {'name': 'Miguel Torres', 'rating': 4.9},
        {'name': 'Paolo Silva', 'rating': 4.7}
    ]
}

# Store orders per user
ORDERS = {}

# In-memory chat storage: {session_id: [{'sender': 'user'/'admin', 'message': '...'}]}
CHAT_SESSIONS = {}

def get_service_color(service_name):
    return '#00b14f' if service_name == 'Grab' else '#d70f64'

def format_datetime(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%B %d, %Y %I:%M %p")

@app.template_filter('format_datetime')
def format_datetime_filter(dt_str):
    return format_datetime(dt_str)

@app.template_filter('currency')
def currency_filter(value):
    return f"\u20b1{value:,.2f}"

@app.context_processor
def utility_processor():
    return {
        'now': datetime.now(),
        'ORDER_STATUSES': ORDER_STATUSES
    }

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/menu')
def menu():
    categories = {
        'Burgers': [
            {
                'name': 'Classic Burger',
                'price': 150.00,
                'description': 'Juicy beef patty with fresh lettuce, tomatoes, and special sauce',
                'image': 'burger.jpg'
            }
        ],
        'Chicken': [
            {
                'name': 'Chicken Wings',
                'price': 180.00,
                'description': 'Crispy chicken wings with your choice of sauce',
                'image': 'Chicken Wings.jpg'
            }
        ],
        'Pizza': [
            {
                'name': 'Classic Pizza',
                'price': 250.00,
                'description': 'Traditional pizza with tomato sauce and mozzarella cheese',
                'image': 'pizza.jpg'
            }
        ],
        'Pasta': [
            {
                'name': 'Spaghetti',
                'price': 120.00,
                'description': 'Classic Filipino style sweet spaghetti with meat sauce',
                'image': 'spaghetti.jpg'
            }
        ],
        'Sides': [
            {
                'name': 'French Fries',
                'price': 80.00,
                'description': 'Crispy golden french fries',
                'image': 'fries.jpg'
            },
            {
                'name': 'Hotdog',
                'price': 60.00,
                'description': 'Classic hotdog sandwich',
                'image': 'hotdog.jpg'
            }
        ],
        'Desserts': [
            {
                'name': 'Ice Cream',
                'price': 50.00,
                'description': 'Creamy vanilla ice cream',
                'image': 'Ice Cream.jpg'
            },
            {
                'name': 'Donut',
                'price': 40.00,
                'description': 'Sweet glazed donut',
                'image': 'Donut.jpg'
            }
        ],
        'Drinks': [
            {
                'name': 'Milk Tea',
                'price': 90.00,
                'description': 'Classic milk tea with pearls',
                'image': 'milktea.jpg'
            }
        ]
    }
    return render_template('menu.html', categories=categories)

@app.route('/orders')
def orders():
    user_id = session.get('user_id', 'guest')
    user_orders = ORDERS.get(user_id, {})
    return render_template('orders.html', orders=user_orders)

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0

    for item_name, item_data in cart.items():
        cart_items.append({
            'name': item_name,
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'image': item_data['image'],
            'description': item_data.get('description', ''),
            'total': item_data['price'] * item_data['quantity']
        })
        total += item_data['price'] * item_data['quantity']

    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    item_name = data.get('name')
    quantity = data.get('quantity', 1)

    if not item_name:
        return jsonify({'success': False, 'error': 'Item name is required'}), 400

    cart = session.get('cart', {})
    if item_name in cart:
        cart[item_name]['quantity'] += quantity
    else:
        cart[item_name] = {
            'name': item_name,
            'price': data.get('price'),
            'quantity': quantity,
            'image': data.get('image'),
            'description': data.get('description', '')
        }

    session['cart'] = cart
    return jsonify({'success': True, 'message': 'Item added to cart', 'cart_count': len(cart)})

@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    item_name = data.get('name')
    action = data.get('action')

    if not item_name or not action:
        return jsonify({'success': False, 'error': 'Missing required data'}), 400

    cart = session.get('cart', {})
    if item_name not in cart:
        return jsonify({'success': False, 'error': 'Item not found in cart'}), 404

    if action == 'increase':
        cart[item_name]['quantity'] += 1
    elif action == 'decrease':
        cart[item_name]['quantity'] = max(0, cart[item_name]['quantity'] - 1)
        if cart[item_name]['quantity'] == 0:
            del cart[item_name]

    session['cart'] = cart
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return jsonify({'success': True, 'cart_count': len(cart), 'total': total})

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    item_name = data.get('name')

    if not item_name:
        return jsonify({'success': False, 'error': 'Item name is required'}), 400

    cart = session.get('cart', {})
    if item_name in cart:
        del cart[item_name]
        session['cart'] = cart
        total = sum(item['price'] * item['quantity'] for item in cart.values())
        return jsonify({'success': True, 'message': 'Item removed', 'cart_count': len(cart), 'total': total})

    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart'] = {}
    return jsonify({'success': True, 'message': 'Cart cleared', 'cart_count': 0, 'total': 0})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('menu'))

    cart_items = []
    total = 0
    for item_name, item_data in cart.items():
        cart_items.append({
            'name': item_name,
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'image': item_data['image'],
            'description': item_data.get('description', ''),
            'total': item_data['price'] * item_data['quantity']
        })
        total += item_data['price'] * item_data['quantity']

    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        notes = request.form.get('notes', '')

        if not all([name, phone, address]):
            flash('Please fill in all required fields.', 'error')
            return render_template('checkout.html', cart_items=cart_items, total=total)

        order_id = f'ORDER-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        current_time = datetime.now()
        estimated_delivery = current_time + timedelta(minutes=random.randint(30, 45))

        delivery_service = random.choice(list(DELIVERY_SERVICES.keys()))
        rider = random.choice(DELIVERY_SERVICES[delivery_service])

        order = {
            'order_id': order_id,
            'customer': {
                'name': name,
                'phone': phone,
                'address': address,
                'notes': notes
            },
            'items': cart_items,
            'total': total,
            'status': ORDER_STATUSES[0],
            'status_history': [
                {'status': ORDER_STATUSES[0], 'time': current_time.strftime("%Y-%m-%d %H:%M:%S")}
            ],
            'order_date': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'estimated_delivery': estimated_delivery.strftime("%Y-%m-%d %H:%M:%S"),
            'delivery_service': delivery_service,
            'rider': rider,
            'service_color': get_service_color(delivery_service)
        }

        user_id = session.get('user_id', 'guest')
        if user_id not in ORDERS:
            ORDERS[user_id] = {}
        ORDERS[user_id][order_id] = order

        session['cart'] = {}
        return render_template('order_success.html', order=order)

    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id:
            session['user_id'] = user_id
            flash('Logged in as ' + user_id)
            return redirect(url_for('menu'))
    return '''
        <form method="post">
            <input type="text" name="user_id" placeholder="Enter user ID">
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/order/<order_id>')
def view_order(order_id):
    user_id = session.get('user_id', 'guest')
    user_orders = ORDERS.get(user_id, {})
    order = user_orders.get(order_id)
    if not order:
        return render_template('404.html'), 404
    return render_template('view_order.html', order=order)

@app.route('/order/<order_id>/tracking')
def order_tracking(order_id):
    user_id = session.get('user_id', 'guest')
    user_orders = ORDERS.get(user_id, {})
    order = user_orders.get(order_id)
    if not order:
        return render_template('404.html'), 404
    return render_template('order_tracking.html', order=order, ORDER_STATUSES=ORDER_STATUSES)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    order_id = data.get('order_id')
    session_id = order_id or session.get('user_id', 'guest')
    if not user_message:
        return jsonify({'success': False, 'reply': "Please enter a message."}), 400
    # Save user message with timestamp
    if session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[session_id] = []
    CHAT_SESSIONS[session_id].append({'sender': 'user', 'message': user_message, 'timestamp': datetime.now().isoformat()})
    return jsonify({'success': True, 'reply': ''})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'support123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid username or password.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/api/sessions')
def admin_list_sessions():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    return jsonify({'success': True, 'sessions': list(CHAT_SESSIONS.keys())})

@app.route('/admin/api/messages/<session_id>')
def admin_get_messages(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    messages = CHAT_SESSIONS.get(session_id, [])
    return jsonify({'success': True, 'messages': messages})

@app.route('/admin/api/reply/<session_id>', methods=['POST'])
def admin_reply(session_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400
    if session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[session_id] = []
    CHAT_SESSIONS[session_id].append({'sender': 'admin', 'message': message, 'timestamp': datetime.now().isoformat()})
    return jsonify({'success': True})

@app.route('/admin/support')
def admin_support():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('customer_support.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

