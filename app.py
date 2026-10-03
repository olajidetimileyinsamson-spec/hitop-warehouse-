from flask import Flask, render_template_string, request, redirect, session, jsonify
import sqlite3, os, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "titech-hitop-2026"
LICENSE = os.getenv("TITECH_LICENSE", "TITECH-HITOP-ACO-2026-TIMILEYIN")

DB = "hitop.db"

def init_db():
    con = sqlite3.connect(DB)
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, stock INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, product TEXT, price INTEGER, status TEXT, staff_id TEXT, time TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, amount INTEGER, profit INTEGER, time TEXT, staff_id TEXT)")
    # seed if empty
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0]==0:
        c.executemany("INSERT INTO products (name,price,stock) VALUES (?,?,?)", [
            ("Rice 50kg",28500,50),
            ("Oil 5L",12900,30),
            ("Soft Drinks Carton",3200,100)
        ])
    con.commit(); con.close()

init_db()

# --- HTML TEMPLATES ---
CUSTOMER_HTML = """
<div style="background:#c40000;color:white;padding:12px;font-weight:bold">🏭 Hitop Warehouse<br><small>ACO Branch - Red & White Edition</small></div>
<div style="padding:10px">
{% for p in products %}
<div style="border:1px solid #eee;border-radius:10px;padding:10px;margin-bottom:10px;background:white">
<b>{{p[1]}}</b><br>₦{{p[2]}} | Stock: {{p[3]}}
<form method="post" action="/add-to-cart"><input type="hidden" name="id" value="{{p[0]}}"><button style="width:100%;background:#c40000;color:white;border:none;padding:8px;border-radius:6px;margin-top:6px">Add to Cart</button></form>
</div>
{% endfor %}
</div>
<div style="position:fixed;bottom:0;width:100%;display:flex;justify-content:space-around;background:white;border-top:1px solid #ccc;padding:8px"><span>Shop</span><span>Cart ({{cart_count}})</span><span>Profile</span></div>
<div style="text-align:center;font-size:10px;background:black;color:#aaa;padding:4px">⚡ Built by Titech | Timileyin Samson | LIC: {{lic}}</div>
"""

STAFF_LOGIN = """<h2 style="color:#c40000">Staff Login</h2><form method="post"><input name="pin" placeholder="Enter PIN" type="password"><button>Login</button></form>"""
STAFF_DASH = """
<h2>Staff Panel - ID: {{sid}}</h2>
<a href="/staff/orders"><button style="width:100%;padding:15px;margin:5px;background:#c40000;color:white">Receive Orders (Live)</button></a>
<a href="/staff/sync"><button style="width:100%;padding:15px;margin:5px;background:#222;color:white">Sync Payment</button></a>
<a href="/staff/addsale"><button style="width:100%;padding:15px;margin:5px;background:green;color:white">Add Sale (Walk-in)</button></a>
<p>Staff ID dey bottom so MD sabi who do wetin.</p>
"""

MD_DASH = """
<h2 style="color:#c40000">MD Remote Control</h2>
<p>Sales Today: ₦{{sales}} | Profit: ₦{{profit}}</p>
<h3>Audit Log</h3><pre>{{logs}}</pre>
<h3>Notifications</h3><p>{{notif}}</p>
<div style="border:1px dashed red;padding:10px">AI Forecasting Space (ACO + EOQ) - Coming</div>
"""

@app.route("/")
def home():
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("SELECT * FROM products"); prods=c.fetchall(); con.close()
    return render_template_string(CUSTOMER_HTML, products=prods, cart_count=len(session.get('cart',[])), lic=LICENSE[:27]+"...")

@app.route("/add-to-cart", methods=["POST"])
def addcart():
    cart=session.get('cart',[]); cart.append(request.form['id']); session['cart']=cart; return redirect("/")

# SECRET STAFF
@app.route("/staff/", methods=["GET","POST"])
def staff_login():
    if request.method=="POST":
        if request.form['pin']=="1234":
            session['staff']="STAFF-001"; return redirect("/staff/dash")
    return STAFF_LOGIN

@app.route("/staff/dash")
def staff_dash():
    if 'staff' not in session: return redirect("/staff/")
    return render_template_string(STAFF_DASH, sid=session['staff'])

# SECRET MD
@app.route("/md/", methods=["GET","POST"])
def md_login():
    if request.method=="POST":
        if request.form['pin']=="9999":
            session['md']=True; return redirect("/md/dash")
    return """<h2>MD Login</h2><form method="post"><input name="pin" type="password" placeholder="MD PIN"><button>Login</button></form>"""

@app.route("/md/dash")
def md_dash():
    if 'md' not in session: return redirect("/md/")
    con=sqlite3.connect(DB); c=con.cursor()
    c.execute("SELECT SUM(amount), SUM(profit) FROM sales"); row=c.fetchone(); sales=row[0] or 0; profit=row[1] or 0
    c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 10"); logs=str(c.fetchall())
    con.close()
    return render_template_string(MD_DASH, sales=sales, profit=profit, logs=logs, notif="No new notification")

if __name__=="__main__":
    if "TITECH" not in LICENSE: print("LICENSE Invalid");
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
