from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date, timedelta
from db import DB
from utils import current_user_id, EXPIRY_SOON_DAYS

shop_bp = Blueprint("shop", __name__)

# Helpers

def _stock_for_medicine(cur, medicine_id):
    cur.execute(
        """
        SELECT COALESCE(SUM(ii.stock_quantity),0) AS stock
        FROM inventory_items ii
        JOIN inventories i ON i.inventory_id = ii.inventory_id
        WHERE ii.medicine_id=%s
        """,
        (medicine_id,)
    )
    r = cur.fetchone()
    return int(r["stock"]) if r else 0

@shop_bp.get("/")
def home_redirect():
    return redirect(url_for("shop.medicines"))

@shop_bp.get("/medicines")
def medicines():
    q = request.args.get("q", "")
    price = request.args.get("price") # "0-100", "1001+" etc
    sort = request.args.get("sort", "name")
    stock_filter = request.args.get("stock", "")
    hide_expired = request.args.get("hide_expired", "1") == "1"

    where = []
    params = []
    if q:
        where.append("(m.name LIKE %s OR m.description LIKE %s)")
        like = f"%{q}%"; params += [like, like]
    if price:
        if "+" in price:
            low = int(price.replace("+", ""))
            where.append("m.price >= %s"); params.append(low)
        else:
            low, high = [int(x) for x in price.split("-")]
            where.append("m.price BETWEEN %s AND %s"); params += [low, high]
    if hide_expired:
        where.append("(m.expiry_date IS NULL OR m.expiry_date >= CURDATE())")

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    order_sql = {
        "name": "m.name ASC",
        "price-low": "m.price ASC",
        "price-high": "m.price DESC",
        "expiry": "m.expiry_date ASC",
    }.get(sort, "m.name ASC")

    with DB() as cur:
        cur.execute(f"SELECT m.* FROM medicines m{where_sql} ORDER BY {order_sql} LIMIT 100", tuple(params))
        meds = cur.fetchall()
        for m in meds:
            m["stock"] = _stock_for_medicine(cur, m["medicine_id"])
            if stock_filter == "in-stock" and m["stock"] <= 0:
                m["_hide"] = True
            elif stock_filter == "low-stock" and not (0 < m["stock"] <= 10):
                m["_hide"] = True
            m["expiry_soon"] = bool(m.get("expiry_date") and m["expiry_date"] <= (date.today()+timedelta(days=EXPIRY_SOON_DAYS)))
        meds = [m for m in meds if not m.get("_hide")]
    return render_template("medicines.html", meds=meds, q=q, price=price, sort=sort, stock_filter=stock_filter, hide_expired=hide_expired)

@shop_bp.post("/cart/add")
def cart_add():
    uid = current_user_id()
    if not uid:
        return jsonify({"ok": False, "msg": "Login required"}), 401
    med_id = int(request.form["medicine_id"]) ; qty = max(1, int(request.form.get("qty", 1)))
    with DB() as cur:
        # ensure cart
        cur.execute("SELECT cart_id FROM carts WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO carts(user_id,total_amount) VALUES(%s,0)", (uid,))
            cart_id = cur.lastrowid
        else:
            cart_id = row["cart_id"]
        # upsert item
        cur.execute("SELECT quantity FROM cart_items WHERE cart_id=%s AND medicine_id=%s", (cart_id, med_id))
        ex = cur.fetchone()
        if ex:
            cur.execute("UPDATE cart_items SET quantity=quantity+%s WHERE cart_id=%s AND medicine_id=%s", (qty, cart_id, med_id))
        else:
            cur.execute("INSERT INTO cart_items(cart_id, medicine_id, quantity) VALUES(%s,%s,%s)", (cart_id, med_id, qty))
        # recalc total
        cur.execute(
            """
            SELECT SUM(ci.quantity*m.price) AS total
            FROM cart_items ci JOIN medicines m ON m.medicine_id=ci.medicine_id
            WHERE ci.cart_id=%s
            """, (cart_id,)
        )
        total = cur.fetchone()["total"] or 0
        cur.execute("UPDATE carts SET total_amount=%s WHERE cart_id=%s", (total, cart_id))
    return jsonify({"ok": True, "msg": "Added to cart"})

@shop_bp.get("/cart")
def cart_page():
    uid = current_user_id()
    if not uid:
        flash("Login required", "error"); return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT cart_id, total_amount FROM carts WHERE user_id=%s", (uid,))
        cart = cur.fetchone()
        items = []
        if cart:
            cur.execute(
                """
                SELECT ci.medicine_id, ci.quantity, m.name, m.price, m.expiry_date
                FROM cart_items ci JOIN medicines m ON m.medicine_id=ci.medicine_id
                WHERE ci.cart_id=%s
                """,
                (cart["cart_id"],)
            )
            items = cur.fetchall()
    return render_template("cart.html", cart=cart, items=items)

@shop_bp.post("/cart/update")
def cart_update():
    uid = current_user_id()
    if not uid:
        return redirect(url_for("auth.login_page"))
    med_id = int(request.form["medicine_id"]) ; qty = int(request.form["qty"]) ; qty = max(0, qty)
    with DB() as cur:
        cur.execute("SELECT cart_id FROM carts WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        if not row: return redirect(url_for("shop.cart_page"))
        cart_id = row["cart_id"]
        if qty==0:
            cur.execute("DELETE FROM cart_items WHERE cart_id=%s AND medicine_id=%s", (cart_id, med_id))
        else:
            cur.execute("UPDATE cart_items SET quantity=%s WHERE cart_id=%s AND medicine_id=%s", (qty, cart_id, med_id))
        # recalc
        cur.execute(
            "SELECT SUM(ci.quantity*m.price) AS total FROM cart_items ci JOIN medicines m ON m.medicine_id=ci.medicine_id WHERE ci.cart_id=%s",
            (cart_id,)
        )
        total = cur.fetchone()["total"] or 0
        cur.execute("UPDATE carts SET total_amount=%s WHERE cart_id=%s", (total, cart_id))
    flash("Cart updated", "success")
    return redirect(url_for("shop.cart_page"))

@shop_bp.post("/wishlist/toggle")
def wishlist_toggle():
    uid = current_user_id()
    if not uid:
        return jsonify({"ok": False, "msg": "Login required"}), 401
    med_id = int(request.form["medicine_id"]) 
    with DB() as cur:
        # ensure wishlist
        cur.execute("SELECT wishlist_id FROM wishlists WHERE user_id=%s", (uid,))
        wl = cur.fetchone()
        if not wl:
            cur.execute("INSERT INTO wishlists(user_id, product_status) VALUES(%s,0)", (uid,))
            wishlist_id = cur.lastrowid
        else:
            wishlist_id = wl["wishlist_id"]
        # toggle
        cur.execute("SELECT 1 FROM wishlist_items WHERE wishlist_id=%s AND medicine_id=%s", (wishlist_id, med_id))
        if cur.fetchone():
            cur.execute("DELETE FROM wishlist_items WHERE wishlist_id=%s AND medicine_id=%s", (wishlist_id, med_id))
            added = False
        else:
            cur.execute("INSERT INTO wishlist_items(wishlist_id, medicine_id) VALUES(%s,%s)", (wishlist_id, med_id))
            added = True
    return jsonify({"ok": True, "added": added})

@shop_bp.get("/wishlist")
def wishlist_page():
    uid = current_user_id()
    if not uid: 
        flash("Login required", "error"); return redirect(url_for("auth.login_page"))
    with DB() as cur:
        cur.execute("SELECT wishlist_id FROM wishlists WHERE user_id=%s", (uid,))
        wl = cur.fetchone()
        items = []
        if wl:
            cur.execute(
                """
                SELECT m.medicine_id, m.name, m.price, m.expiry_date
                FROM wishlist_items wi JOIN medicines m ON m.medicine_id=wi.medicine_id
                WHERE wi.wishlist_id=%s
                """, (wl["wishlist_id"],)
            )
            items = cur.fetchall()
    return render_template("wishlist.html", items=items)

@shop_bp.post("/checkout")
def checkout_submit():
    uid = current_user_id()
    if not uid:
        flash("Login required", "error"); return redirect(url_for("auth.login_page"))
    method = request.form.get("method")
    address = request.form.get("address")
    with DB() as cur:
        cur.execute("SELECT cart_id, total_amount FROM carts WHERE user_id=%s", (uid,))
        cart = cur.fetchone()
        if not cart:
            flash("Cart is empty", "error"); return redirect(url_for("shop.cart_page"))
        cur.execute(
            "INSERT INTO payments(cart_id, customer_id, method, status, transaction_id) VALUES(%s,%s,%s,%s,%s)",
            (cart["cart_id"], uid, method, "successful" if method in ("cod","wallet") else "initiated", None)
        )
        order_id = cur.lastrowid
        # (Optional) reduce stock — out of scope since no direct order_items; demo only
        # clear cart
        cur.execute("DELETE FROM cart_items WHERE cart_id=%s", (cart["cart_id"],))
        cur.execute("UPDATE carts SET total_amount=0 WHERE cart_id=%s", (cart["cart_id"],))
    flash(f"Order #{order_id} placed!", "success")
    return redirect(url_for("index"))