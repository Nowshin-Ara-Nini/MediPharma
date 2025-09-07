from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from db import DB

pharmacist_bp = Blueprint("pharmacist", __name__)

@pharmacist_bp.get("/pharmacist_dashboard")
def pharmacist_dashboard():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    return render_template("pharmacist_dashboard.html")

@pharmacist_bp.get("/pharmacist_profile")
def pharmacist_profile():
    with DB() as cur:
        cur.execute("SELECT * FROM pharmacists WHERE user_id=%s", (session["uid"],))
        profile = cur.fetchone()
    return render_template("pharmacist_profile.html", profile=profile)

@pharmacist_bp.get("/pharmacist_medicines")
def pharmacist_medicines():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))

    with DB() as cur:
        # Fetch all medicines uploaded by companies with their stock quantity
        cur.execute("""
            SELECT
                c.user_id AS company_id,
                u.name AS company_name,
                m.medicine_id,
                m.name,
                m.description,
                m.price,
                m.production_date,
                m.expiry_date,
                COALESCE(SUM(ii.stock_quantity), 0) AS stock
            FROM inventories i
            JOIN companies c       ON c.user_id = i.company_id
            JOIN users u           ON u.user_id = c.user_id
            JOIN inventory_items ii ON ii.inventory_id = i.inventory_id
            JOIN medicines m        ON m.medicine_id = ii.medicine_id
            GROUP BY c.user_id, u.name, m.medicine_id, m.name, m.description, m.price, m.production_date, m.expiry_date
            ORDER BY m.name, u.name
        """)
        medicines = cur.fetchall()

    return render_template("pharmacist_medicines.html", medicines=medicines)

@pharmacist_bp.get("/pharmacist_orders")
def pharmacist_orders():
    with DB() as cur:
        # Single query to get orders with their items
        cur.execute("""
            SELECT 
                o.order_id, o.customer_id, o.total_amount, o.status,
                o.created_at, o.payment_method,
                oi.medicine_id, oi.quantity, m.name as medicine_name
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN medicines m ON oi.medicine_id = m.medicine_id
            WHERE o.status = 'pending'
            ORDER BY o.order_id
        """)
        
        # Group items by order
        orders_dict = {}
        for row in cur.fetchall():
            order_id = row['order_id']
            if order_id not in orders_dict:
                orders_dict[order_id] = {
                    'order_id': order_id,
                    'customer_id': row['customer_id'],
                    'total_amount': row['total_amount'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'payment_method': row['payment_method'],
                    'items': []
                }
            
            if row['medicine_id']:  # Only add if there are items
                orders_dict[order_id]['items'].append({
                    'medicine_id': row['medicine_id'],
                    'quantity': row['quantity'],
                    'name': row['medicine_name']
                })
        
        orders = list(orders_dict.values())
    
    return render_template("pharmacist_orders.html", orders=orders)

@pharmacist_bp.get("/pharmacist_notifications", endpoint="notifications")
def pharmacist_notifications():
    with DB() as cur:
        cur.execute("SELECT * FROM notifications WHERE pharmacist_id=%s", (session["uid"],))
        notifications = cur.fetchall()
    return render_template("notifications.html", notifications=notifications)

@pharmacist_bp.get("/pharmacist_refund_policy", endpoint="refund_policy")
def pharmacist_refund_policy():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))
    return render_template("refund_policy.html")

@pharmacist_bp.route("/request_stock", methods=["POST"])
def request_stock():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))

    pharmacist_id = session["uid"]
    company_id = request.form.get("company_id", type=int)
    medicine_id = request.form.get("medicine_id", type=int)
    quantity = request.form.get("quantity", type=int)

    # Check if the pharmacist is trying to request medicine that's already in another inventory
    with DB() as cur:
        cur.execute("""
            SELECT i.pharmacist_id
            FROM inventories i
            JOIN inventory_items ii ON ii.inventory_id = i.inventory_id
            WHERE ii.medicine_id = %s AND i.pharmacist_id != %s
        """, (medicine_id, pharmacist_id))

        # If a result is found, that means another pharmacist already has this medicine
        existing_pharmacist = cur.fetchone()
        if existing_pharmacist:
            flash("Someone already has this medicine in their inventory.", "warning")
            return redirect(url_for("pharmacist.pharmacist_medicines"))

    # Check if the pharmacist is requesting at least 50
    if quantity < 50:
        flash("Minimum request quantity is 50.", "error")
        return redirect(url_for("pharmacist.pharmacist_medicines"))

    # Check if this pharmacist already has this medicine in their inventory
    with DB() as cur:
        cur.execute("""
            SELECT ii.stock_quantity
            FROM inventories i
            JOIN inventory_items ii ON ii.inventory_id = i.inventory_id
            WHERE i.pharmacist_id = %s AND ii.medicine_id = %s
        """, (pharmacist_id, medicine_id))

        row = cur.fetchone()
        if row:
            # If the pharmacist already has stock, we just update the quantity
            new_quantity = row["stock_quantity"] + quantity
            cur.execute("""
                UPDATE inventory_items
                SET stock_quantity = %s
                WHERE inventory_id IN (
                    SELECT inventory_id FROM inventories WHERE pharmacist_id = %s
                ) AND medicine_id = %s
            """, (new_quantity, pharmacist_id, medicine_id))
        else:
            # If not, create a new inventory entry for the pharmacist
            cur.execute("""
                INSERT INTO inventories (company_id, pharmacist_id) VALUES (%s, %s)
            """, (company_id, pharmacist_id))
            inventory_id = cur.lastrowid

            # Now add the medicine to the pharmacist's inventory
            cur.execute("""
                INSERT INTO inventory_items (inventory_id, medicine_id, stock_quantity)
                VALUES (%s, %s, %s)
            """, (inventory_id, medicine_id, quantity))

    flash("Your stock request is successful", "success")
    return redirect(url_for("pharmacist.pharmacist_medicines"))

@pharmacist_bp.route("/upload_medicine_to_catalog", methods=["POST"])
def upload_medicine_to_catalog():
    if session.get("role") != "pharmacist":
        return redirect(url_for("auth.login_page"))

    medicine_id = request.form.get("medicine_id", type=int)
    company_id = request.form.get("company_id", type=int)

    with DB() as cur:
        # Check if the medicine already exists in the catalog
        cur.execute("""
            SELECT 1 FROM medicines_catalog WHERE medicine_id = %s
        """, (medicine_id,))
        if cur.fetchone():
            flash("This medicine is already available in the catalog.", "warning")
        else:
            # Insert into the medicines catalog for customers
            cur.execute("""
                INSERT INTO medicines_catalog (medicine_id, company_id)
                VALUES (%s, %s)
            """, (medicine_id, company_id))
            flash("Medicine added to the catalog successfully.", "success")
    
    return redirect(url_for("pharmacist.pharmacist_medicines"))

@pharmacist_bp.route('/orders/fulfill/<int:order_id>', methods=['POST'])
def fulfill_order(order_id):
    with DB() as cur:
        # Update the order status to 'fulfilled'
        cur.execute("""
            UPDATE orders
            SET status = 'fulfilled'
            WHERE order_id = %s
        """, (order_id,))

        # Get all items in the order
        cur.execute("""
            SELECT medicine_id, quantity
            FROM order_items
            WHERE order_id = %s
        """, (order_id,))
        items = cur.fetchall()

        # Update the stock in the inventory for each item in the order
        for item in items:
            cur.execute("""
                UPDATE inventory_items
                SET stock_quantity = stock_quantity - %s
                WHERE medicine_id = %s
            """, (item['quantity'], item['medicine_id']))

    # Redirect pharmacist to the "My Orders" page after fulfilling the order
    return redirect(url_for('pharmacist.my_orders'))

@pharmacist_bp.route('/my_orders')
def my_orders():
    with DB() as cur:
        # First, let's debug what's actually in the orders table
        cur.execute("SELECT * FROM orders WHERE status = 'pending'")
        raw_orders = cur.fetchall()  # ADD PARENTHESES HERE
        print(f"DEBUG: Raw pending orders: {raw_orders}")
        
        # Fetch orders with customer information
        cur.execute("""
            SELECT o.order_id, o.customer_id, o.total_amount, o.status, 
                   o.created_at, o.payment_method, u.name as customer_name
            FROM orders o
            LEFT JOIN users u ON o.customer_id = u.user_id
            WHERE o.status = 'pending'
            ORDER BY o.created_at DESC
        """)
        orders = cur.fetchall()  # ADD PARENTHESES HERE
        print(f"DEBUG: Processed orders: {orders}")

        # For each order, fetch the corresponding items
        for order in orders:
            cur.execute("""
                SELECT oi.medicine_id, oi.quantity, m.name, m.price
                FROM order_items oi
                JOIN medicines m ON oi.medicine_id = m.medicine_id
                WHERE oi.order_id = %s
            """, (order['order_id'],))
            order_items = cur.fetchall()  # ADD PARENTHESES HERE
            order['items'] = order_items
            print(f"DEBUG: Order {order['order_id']} items: {order_items}")

    return render_template('pharmacist_orders.html', orders=orders)
