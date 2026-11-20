import os, io, csv
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
import pandas as pd

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "shopscope-local-dev-key-change-before-deploy")
db_url = os.getenv("DATABASE_URL", "sqlite:///shopscope.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, nullable=False, index=True)
    customer_id = db.Column(db.String(80), nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    product = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    region = db.Column(db.String(100), nullable=False, default="India")

def seed_data():
    if Order.query.first():
        return
    import random
    random.seed(21)
    products = [
        ("Wireless Headphones","Electronics",2499),("Smart Watch","Electronics",3999),
        ("Bluetooth Speaker","Electronics",1799),("Running Shoes","Fashion",2299),
        ("Cotton T-Shirt","Fashion",699),("Backpack","Accessories",1299),
        ("Water Bottle","Home & Living",499),("Desk Lamp","Home & Living",999),
        ("Skin Care Set","Beauty",1499),("Coffee Maker","Home & Living",3499)
    ]
    names = ["Aarav Sharma","Diya Patel","Ishaan Reddy","Ananya Singh","Vivaan Kumar","Meera Nair","Aditya Rao","Sana Khan","Arjun Das","Kavya Iyer","Reyansh Gupta","Ira Joshi","Kabir Mehta","Tara Bose","Rohan Verma"]
    regions = ["Hyderabad","Bengaluru","Mumbai","Delhi","Chennai","Pune"]
    today = datetime.now().date()
    rows = []
    for i in range(420):
        dt = today - timedelta(days=random.randint(0, 179))
        cid = f"C{random.randint(1, 180):04d}"
        p, cat, price = random.choice(products)
        qty = random.randint(1, 3)
        rows.append(Order(order_date=dt, customer_id=cid,
            customer_name=random.choice(names), product=p, category=cat,
            quantity=qty, unit_price=price, total=qty*price,
            region=random.choice(regions)))
    db.session.add_all(rows)
    db.session.commit()

def dashboard_data():
    total_orders = db.session.query(func.count(Order.id)).scalar() or 0
    revenue = db.session.query(func.sum(Order.total)).scalar() or 0
    customers = db.session.query(func.count(func.distinct(Order.customer_id))).scalar() or 0
    units = db.session.query(func.sum(Order.quantity)).scalar() or 0
    aov = revenue / total_orders if total_orders else 0

    monthly_rows = db.session.query(
        func.strftime("%Y-%m", Order.order_date).label("month"),
        func.sum(Order.total).label("revenue")
    ).group_by("month").order_by("month").all() if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"] else db.session.query(
        func.to_char(Order.order_date, "YYYY-MM").label("month"),
        func.sum(Order.total).label("revenue")
    ).group_by("month").order_by("month").all()
    category_rows = db.session.query(Order.category, func.sum(Order.total)).group_by(Order.category).order_by(desc(func.sum(Order.total))).all()
    product_rows = db.session.query(Order.product, func.sum(Order.total).label("revenue"), func.sum(Order.quantity).label("units")).group_by(Order.product).order_by(desc("revenue")).limit(8).all()
    region_rows = db.session.query(Order.region, func.count(Order.id)).group_by(Order.region).order_by(desc(func.count(Order.id))).all()
    customer_counts = db.session.query(Order.customer_id, func.count(Order.id).label("orders"), func.sum(Order.total).label("spend")).group_by(Order.customer_id).all()
    repeat = sum(1 for x in customer_counts if x.orders > 1)
    new_customers = max(customers-repeat, 0)
    segments = {"High value":0,"Regular":0,"Occasional":0}
    for c in customer_counts:
        if c.spend >= 10000: segments["High value"] += 1
        elif c.spend >= 4000: segments["Regular"] += 1
        else: segments["Occasional"] += 1
    return {
        "orders": total_orders, "revenue": round(revenue,2), "customers": customers,
        "units": units, "aov": round(aov,2), "repeat": repeat, "new": new_customers,
        "monthly": [{"label":str(x.month), "value":round(float(x.revenue or 0),2)} for x in monthly_rows],
        "categories": [{"label":x[0], "value":round(float(x[1] or 0),2)} for x in category_rows],
        "products": [{"label":x[0], "revenue":round(float(x[1] or 0),2), "units":int(x[2] or 0)} for x in product_rows],
        "regions": [{"label":x[0], "value":int(x[1])} for x in region_rows],
        "segments": [{"label":k,"value":v} for k,v in segments.items()]
    }

@app.route("/")
def index():
    data = dashboard_data()
    recent = Order.query.order_by(Order.order_date.desc(), Order.id.desc()).limit(8).all()
    return render_template("index.html", data=data, recent=recent)

@app.route("/customers")
def customers():
    rows = db.session.query(Order.customer_id, func.max(Order.customer_name).label("name"),
        func.count(Order.id).label("orders"), func.sum(Order.total).label("spend"),
        func.max(Order.order_date).label("last_order")).group_by(Order.customer_id).order_by(desc("spend")).limit(100).all()
    return render_template("customers.html", rows=rows)

@app.route("/products")
def products():
    rows = db.session.query(Order.product, Order.category, func.sum(Order.quantity).label("units"),
        func.sum(Order.total).label("revenue")).group_by(Order.product,Order.category).order_by(desc("revenue")).all()
    return render_template("products.html", rows=rows)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("dataset")
    if not file or not file.filename.lower().endswith(".csv"):
        flash("Please select a CSV file.", "error")
        return redirect(url_for("index"))
    try:
        df = pd.read_csv(file)
        required = {"order_date","customer_id","customer_name","product","category","quantity","unit_price"}
        missing = required - set(df.columns)
        if missing:
            flash("Missing columns: " + ", ".join(sorted(missing)), "error")
            return redirect(url_for("index"))
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.date
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        df = df.dropna(subset=["order_date","customer_id","product","quantity","unit_price"])
        inserted = 0
        for _, r in df.iterrows():
            qty, price = int(r["quantity"]), float(r["unit_price"])
            if qty < 1 or price < 0: continue
            db.session.add(Order(order_date=r["order_date"], customer_id=str(r["customer_id"]),
                customer_name=str(r.get("customer_name", "Customer")), product=str(r["product"]),
                category=str(r["category"]), quantity=qty, unit_price=price,
                total=qty*price, region=str(r.get("region","India"))))
            inserted += 1
        db.session.commit()
        flash(f"Successfully imported {inserted} records.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not import CSV: {e}", "error")
    return redirect(url_for("index"))

@app.route("/export")
def export():
    rows = Order.query.order_by(Order.order_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["order_date","customer_id","customer_name","product","category","quantity","unit_price","total","region"])
    for r in rows:
        writer.writerow([r.order_date,r.customer_id,r.customer_name,r.product,r.category,r.quantity,r.unit_price,r.total,r.region])
    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="shopscope_analytics_data.csv")

@app.route("/api/analytics")
def api_analytics():
    return jsonify(dashboard_data())

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
