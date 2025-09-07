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
    # Check if user is logged in
    if 'uid' not in session or session.get('role') != 'customer':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"ok": False, "msg": "Login required"}), 401
        flash("Login required", "error")
        return redirect(url_for("auth.login_page"))
    
    uid = session["uid"]
    
    try:
        med_id = int(request.form["medicine_id"])
        qty = max(1, int(request.form.get("qty", 1)))
    except (ValueError, KeyError):
        return jsonify({"ok": False, "msg": "Invalid input"}), 400

    with DB() as cur:
        # Get or create cart
        cur.execute("SELECT cart_id FROM carts WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO carts(user_id, total_amount) VALUES(%s,0)", (uid,))
            cart_id = cur.lastrowid
        else:
            cart_id = row["cart_id"]

        # Check if item already exists in cart
        cur.execute("SELECT quantity FROM cart_items WHERE cart_id=%s AND medicine_id=%s", (cart_id, med_id))
        ex = cur.fetchone()
        if ex:
            cur.execute("UPDATE cart_items SET quantity=quantity+%s WHERE cart_id=%s AND medicine_id=%s", (qty, cart_id, med_id))
        else:
            cur.execute("INSERT INTO cart_items(cart_id, medicine_id, quantity) VALUES(%s,%s,%s)", (cart_id, med_id, qty))

        # Update cart total
        cur.execute("""
            SELECT SUM(ci.quantity * m.price) AS total
            FROM cart_items ci
            JOIN medicines m ON m.medicine_id = ci.medicine_id
            WHERE ci.cart_id=%s
        """, (cart_id,))
        total = cur.fetchone()["total"] or 0
        cur.execute("UPDATE carts SET total_amount=%s WHERE cart_id=%s", (total, cart_id))

    # Always return JSON for AJAX requests
    return jsonify({"ok": True, "msg": "Added to cart"})

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
            return redirect(url_for("customer.medicines_catalog"))

        cart_id = cart['cart_id']

        # Get the items in the cart
        cur.execute("""
            SELECT m.medicine_id, m.name, m.description, m.price, ci.quantity
            FROM cart_items ci
            JOIN medicines m ON ci.medicine_id = m.medicine_id
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
