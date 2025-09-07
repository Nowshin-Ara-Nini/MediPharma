from flask import Blueprint, render_template, request, jsonify, redirect, session, url_for, flash
from db import DB
from utils import current_user_id

shop_bp = Blueprint("shop", __name__)

@shop_bp.get("/medicines")
def medicines():
    with DB() as cur:
        # Fetch medicines from the catalog, joining with the `medicines` table to get details
        cur.execute("""
            SELECT m.medicine_id, m.name, m.description, m.price
            FROM medicines_catalog mc
            JOIN medicines m ON m.medicine_id = mc.medicine_id
        """)
        medicines = cur.fetchall()

    return render_template("medicines.html", medicines=medicines)

@shop_bp.post("/cart/add")
def cart_add():
    uid = current_user_id()
    if not uid:
        return jsonify({"ok": False, "msg": "Login required"}), 401

    med_id = int(request.form["medicine_id"])
    qty = max(1, int(request.form.get("qty", 1)))  # Default to 1 if no quantity is provided

    with DB() as cur:
        # Check if the user already has a cart
        cur.execute("SELECT cart_id FROM carts WHERE user_id=%s", (uid,))
        row = cur.fetchone()

        if not row:
            # If the user doesn't have a cart, create a new one
            cur.execute("INSERT INTO carts(user_id, total_amount) VALUES(%s, 0)", (uid,))
            cart_id = cur.lastrowid
        else:
            cart_id = row["cart_id"]

        # Check if the item is already in the cart
        cur.execute("SELECT quantity FROM cart_items WHERE cart_id=%s AND medicine_id=%s", (cart_id, med_id))
        ex = cur.fetchone()

        if ex:
            # If the item exists, increase the quantity by the requested amount
            new_quantity = ex["quantity"] + qty
            cur.execute("UPDATE cart_items SET quantity=%s WHERE cart_id=%s AND medicine_id=%s", (new_quantity, cart_id, med_id))
        else:
            # If the item doesn't exist, add it to the cart with the requested quantity
            cur.execute("INSERT INTO cart_items(cart_id, medicine_id, quantity) VALUES(%s, %s, %s)", (cart_id, med_id, qty))

        # Recalculate the total amount in the cart
        cur.execute("""
            SELECT SUM(ci.quantity * m.price) AS total
            FROM cart_items ci
            JOIN medicines m ON m.medicine_id = ci.medicine_id
            WHERE ci.cart_id=%s
        """, (cart_id,))
        total = cur.fetchone()["total"] or 0

        # Update the total amount in the carts table
        cur.execute("UPDATE carts SET total_amount=%s WHERE cart_id=%s", (total, cart_id))

    return jsonify({"ok": True, "msg": "Added to cart", "total": total})

@shop_bp.get("/cart")
def cart_page():
    if session.get("role") != "customer":
        return redirect(url_for("auth.login_page"))

    with DB() as cur:
        # Get the cart for the current customer
        cur.execute("""
            SELECT cart_id FROM carts WHERE user_id = %s
        """, (session["uid"],))
        cart = cur.fetchone()

        if not cart:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("shop.medicines"))

        cart_id = cart['cart_id']

        # Get the items in the cart with stock information
        cur.execute("""
            SELECT 
                m.medicine_id, 
                m.name, 
                m.description, 
                m.price, 
                ci.quantity,
                ii.stock_quantity
            FROM cart_items ci
            JOIN medicines m ON ci.medicine_id = m.medicine_id
            JOIN inventory_items ii ON ci.medicine_id = ii.medicine_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        cart_items = cur.fetchall()

        # Calculate the total amount in the cart
        cur.execute("""
            SELECT total_amount FROM carts WHERE cart_id = %s
        """, (cart_id,))
        total_amount = cur.fetchone()['total_amount']

    return render_template("cart.html", cart_items=cart_items, total_amount=total_amount)

@shop_bp.get("/wishlist")
def wishlist_page():
    uid = current_user_id()
    if not uid:
        flash("Login required", "error")
        return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT wishlist_id FROM wishlists WHERE user_id=%s", (uid,))
        wishlist = cur.fetchone()
        items = []
        if wishlist:
            cur.execute("""
                SELECT wi.medicine_id, m.name, m.price, m.expiry_date
                FROM wishlist_items wi
                JOIN medicines m ON m.medicine_id=wi.medicine_id
                WHERE wi.wishlist_id=%s
            """, (wishlist["wishlist_id"],))
            items = cur.fetchall()
    return render_template("wishlist.html", wishlist=wishlist, items=items)

# Payment page route
@shop_bp.route('/payment', methods=['GET', 'POST'])
def payment_page():
    uid = current_user_id()  # Get the logged-in customer ID

    if not uid:
        flash("You need to be logged in to make a payment.", "error")
        return redirect(url_for('auth.login_page'))

    if request.method == 'POST':
        print("Processing payment...")

        payment_method = request.form.get('payment_method')  # Payment method (card, bKash, etc.)
        print(f"Payment method: {payment_method}")

        # Check if payment details are provided (card, bKash, etc.)
        if payment_method == 'card':
            card_number = request.form.get('card_number')
            card_holder = request.form.get('card_holder')
            expiry_date = request.form.get('expiry_date')
            cvv = request.form.get('cvv')
            if not all([card_number, card_holder, expiry_date, cvv]):
                flash("Please fill all card details", "error")
                return render_template('payment.html')

        elif payment_method in ['bkash', 'nagad']:
            number = request.form.get(f'{payment_method}_number')
            transaction_id = request.form.get(f'{payment_method}_transaction_id')
            if not all([number, transaction_id]):
                flash(f"Please fill all {payment_method} details", "error")
                return render_template('payment.html')

        with DB() as cur:
            # Get cart details
            cur.execute("""
                SELECT cart_id, total_amount FROM carts WHERE user_id = %s
            """, (uid,))
            cart = cur.fetchone()

            if not cart:
                flash("Your cart is empty. Add items to the cart first.", "error")
                return redirect(url_for('shop.cart_page'))

            cart_id = cart['cart_id']
            total_amount = cart['total_amount']

            # Insert order into orders table
            cur.execute("""
                INSERT INTO orders (customer_id, total_amount, status, payment_method)
                VALUES (%s, %s, 'pending', %s)
            """, (uid, total_amount, payment_method))
            order_id = cur.lastrowid  # Get the last inserted order_id

            # Insert items into order_items table
            cur.execute("""
                SELECT medicine_id, quantity FROM cart_items WHERE cart_id = %s
            """, (cart_id,))
            items = cur.fetchall()

            for item in items:
                cur.execute("""
                    INSERT INTO order_items (order_id, medicine_id, quantity)
                    VALUES (%s, %s, %s)
                """, (order_id, item['medicine_id'], item['quantity']))

                # Update stock in inventory
                cur.execute("""
                    UPDATE inventory_items
                    SET stock_quantity = stock_quantity - %s
                    WHERE medicine_id = %s
                """, (item['quantity'], item['medicine_id']))

            # Clear cart after successful order creation
            cur.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
            cur.execute("UPDATE carts SET total_amount = 0 WHERE cart_id = %s", (cart_id,))

            # Insert payment details into the payments table
            cur.execute("""
                INSERT INTO payments (order_id, cart_id, customer_id, method, status)
                VALUES (%s, %s, %s, %s, 'initiated')
            """, (order_id, cart_id, uid, payment_method))

        flash("Your order has been confirmed!", "success")
        return redirect(url_for('shop.home_page'))

    return render_template('payment.html')

@shop_bp.route('/')
def home_page():
    return render_template('home.html')

@shop_bp.post('/cart/update/<int:medicine_id>')
def update_cart_item(medicine_id):
    uid = current_user_id()

    if not uid:
        return jsonify({"ok": False, "msg": "Login required"}), 401

    # Get the new quantity from the request body
    data = request.get_json()
    new_quantity = data.get('quantity')

    if new_quantity is None or new_quantity < 1:
        return jsonify({"ok": False, "msg": "Invalid quantity"}), 400

    with DB() as cur:
        # Get the cart ID
        cur.execute("SELECT cart_id FROM carts WHERE user_id = %s", (uid,))
        cart = cur.fetchone()

        if not cart:
            return jsonify({"ok": False, "msg": "No cart found"}), 404

        cart_id = cart['cart_id']

        # Update the quantity of the item in the cart
        cur.execute("""
            UPDATE cart_items
            SET quantity = %s
            WHERE cart_id = %s AND medicine_id = %s
        """, (new_quantity, cart_id, medicine_id))

        # Update the total amount in the cart
        cur.execute("""
            SELECT SUM(ci.quantity * m.price) AS total
            FROM cart_items ci
            JOIN medicines m ON m.medicine_id = ci.medicine_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        total = cur.fetchone()['total'] or 0

        # Update the total amount in the carts table
        cur.execute("""
            UPDATE carts
            SET total_amount = %s
            WHERE cart_id = %s
        """, (total, cart_id))
    return jsonify({"ok": True, "msg": "Cart updated","new_total": total})

@shop_bp.post('/cart/remove/<int:medicine_id>')
def remove_cart_item(medicine_id):
    uid = current_user_id()

    if not uid:
        return jsonify({"ok": False, "msg": "Login required"}), 401

    with DB() as cur:
        # Get the cart ID
        cur.execute("SELECT cart_id FROM carts WHERE user_id = %s", (uid,))
        cart = cur.fetchone()

        if not cart:
            return jsonify({"ok": False, "msg": "No cart found"}), 404

        cart_id = cart['cart_id']

        # Remove the item from the cart
        cur.execute("""
            DELETE FROM cart_items
            WHERE cart_id = %s AND medicine_id = %s
        """, (cart_id, medicine_id))

        # Update the total amount in the cart
        cur.execute("""
            SELECT SUM(ci.quantity * m.price) AS total
            FROM cart_items ci
            JOIN medicines m ON m.medicine_id = ci.medicine_id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        total = cur.fetchone()['total'] or 0

        # Update the total amount in the carts table
        cur.execute("""
            UPDATE carts
            SET total_amount = %s
            WHERE cart_id = %s
        """, (total, cart_id))

    return jsonify({"ok": True, "msg": "Item removed from cart","new_total": total})