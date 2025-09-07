from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from db import DB
from utils import current_user_id

shop_bp = Blueprint("shop", __name__)

@shop_bp.get("/medicines")
def medicines():
    q = request.args.get("q", "")
    with DB() as cur:
        cur.execute("""
            SELECT m.*, SUM(ii.stock_quantity) AS stock
            FROM medicines m
            JOIN inventory_items ii ON m.medicine_id = ii.medicine_id
            GROUP BY m.medicine_id
            HAVING SUM(ii.stock_quantity) > 0
        """)
        medicines = cur.fetchall()
    return render_template("medicines.html", medicines=medicines)

@shop_bp.post("/cart/add")
def cart_add():
    uid = current_user_id()
    if not uid:
        return jsonify({"ok": False, "msg": "Login required"}), 401

    med_id = int(request.form["medicine_id"])
    qty = max(1, int(request.form.get("qty", 1)))

    with DB() as cur:
        cur.execute("SELECT cart_id FROM carts WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO carts(user_id, total_amount) VALUES(%s,0)", (uid,))
            cart_id = cur.lastrowid
        else:
            cart_id = row["cart_id"]

        cur.execute("SELECT quantity FROM cart_items WHERE cart_id=%s AND medicine_id=%s", (cart_id, med_id))
        ex = cur.fetchone()
        if ex:
            cur.execute("UPDATE cart_items SET quantity=quantity+%s WHERE cart_id=%s AND medicine_id=%s", (qty, cart_id, med_id))
        else:
            cur.execute("INSERT INTO cart_items(cart_id, medicine_id, quantity) VALUES(%s,%s,%s)", (cart_id, med_id, qty))

        cur.execute("""
            SELECT SUM(ci.quantity * m.price) AS total
            FROM cart_items ci
            JOIN medicines m ON m.medicine_id = ci.medicine_id
            WHERE ci.cart_id=%s
        """, (cart_id,))
        total = cur.fetchone()["total"] or 0
        cur.execute("UPDATE carts SET total_amount=%s WHERE cart_id=%s", (total, cart_id))

    return jsonify({"ok": True, "msg": "Added to cart"})

@shop_bp.get("/cart")
def cart_page():
    uid = current_user_id()
    if not uid:
        flash("Login required", "error")
        return redirect(url_for("auth.login_page"))  # Redirect to login if not logged in

    with DB() as cur:
        cur.execute("SELECT cart_id, total_amount FROM carts WHERE user_id=%s", (uid,))
        cart = cur.fetchone()
        items = []
        if cart:
            cur.execute("""
                SELECT ci.medicine_id, ci.quantity, m.name, m.price, m.expiry_date
                FROM cart_items ci
                JOIN medicines m ON m.medicine_id=ci.medicine_id
                WHERE ci.cart_id=%s
            """, (cart["cart_id"],))
            items = cur.fetchall()

    return render_template("cart.html", cart=cart, items=items)

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
