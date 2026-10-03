from flask import Flask, render_template_string, request, redirect, session, url_for
import sqlite3, os, datetime, uuid

app = Flask(__name__)
app.secret_key = "titech-hitop-2026-ultimate"
LICENSE = os.getenv("TITECH_LICENSE","TITECH-HITOP-ACO-2026-TIMILEYIN")
DB="hitop.db"

def init_db():
    con=sqlite3.connect(DB); c=con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, stock INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS carts (code TEXT PRIMARY KEY, status TEXT, total INTEGER, time TEXT, items_count INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS cart_items (id INTEGER PRIMARY KEY, cart_code TEXT, product TEXT, price INTEGER, qty INTEGER)")
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0]==0:
        c.executemany("INSERT INTO products (name,price,stock) VALUES (?,?,?)", [("Rice 50kg",28500,50),("Oil 5L",12900,30),("Soft Drinks Carton",3200,100)])
    con.commit(); con.close()
init_db()

def gen_unique_code():
    # HITOP-20261003-142201-A3F9 - timestamp + uuid = never repeat even in 10 years
    base = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    rand = uuid.uuid4().hex[:6].upper()
    return f"HITOP-{base}-{rand}"

# CUSTOMER LAYOUT
BASE = """
<style>
body{font-family:Arial;margin:0;padding-bottom:60px;background:#f9f9f9}
.header{background:#c40000;color:white;padding:12px;font-weight:bold;position:sticky;top:0}
.nav{position:fixed;bottom:0;width:100%;display:flex;justify-content:space-around;background:white;border-top:1px solid #ccc;padding:10px}
.nav a{color:#c40000;text-decoration:none;font-weight:bold}
.card{background:white;border:1px solid #eee;border-radius:10px;padding:10px;margin:10px}
.search{width:90%;padding:10px;margin:10px;border-radius:20px;border:1px solid #ccc}
</style>
<div class="header">🏭 Hitop Warehouse - ACO Branch</div>
"""

@app.route("/", methods=["GET"])
def shop():
    q=request.args.get("q","")
    con=sqlite3.connect(DB); c=con.cursor()
    if q: c.execute("SELECT * FROM products WHERE name LIKE?", ('%'+q+'%',))
    else: c.execute("SELECT * FROM products")
    products=c.fetchall(); con.close()
    cart=session.get('cart', {}) # {product_id: qty}
    count=sum(cart.values())
    html=BASE+f"""
    <form><input class="search" name="q" placeholder="🔍 Search goods..." value="{q}"></form>
    """
    for p in products:
        html+=f"""
        <div class="card">
        <b>{p[1]}</b><br>₦{p[2]} | Stock: {p[3]}
        <form method="post" action="/add/{p[0]}" style="display:flex;gap:5px;margin-top:6px">
        <input type="number" name="qty" value="1" min="1" max="{p[3]}" style="width:60px;padding:6px">
        <button style="flex:1;background:#c40000;color:white;border:none;border-radius:6px">Add to Cart</button>
        </form></div>
        """
    html+=f'<div class="nav"><a href="/">Shop</a><a href="/cart">Cart ({count})</a><a href="/profile">Profile</a></div>'
    return html

@app.route("/add/<int:pid>", methods=["POST"])
def add(pid):
    qty=int(request.form.get("qty",1))
    cart=session.get('cart', {})
    cart[str(pid)]=cart.get(str(pid),0)+qty
    session['cart']=cart
    return redirect("/")

@app.route("/cart")
def view_cart():
    cart=session.get('cart', {})
    if not cart: return BASE+"<div class=card>Cart empty</div><div class=nav><a href='/'>Shop</a><a href='/cart'>Cart (0)</a><a href='/profile'>Profile</a></div>"
    con=sqlite3.connect(DB); c=con.cursor()
    total=0; items_html=""
    for pid, qty in cart.items():
        c.execute("SELECT * FROM products WHERE id=?", (pid,)); p=c.fetchone()
        if p:
            sub=p[2]*qty; total+=sub
            items_html+=f"<div class=card>{p[1]} x {qty} = ₦{sub}</div>"
    con.close()
    return BASE+items_html+f"""
    <div class="card"><b>Total: ₦{total}</b>
    <form method="post" action="/checkout"><button style="width:100%;background:#222;color:white;padding:10px;border-radius:6px">Submit Cart - Generate Code</button></form>
    </div>
    <div class="nav"><a href="/">Shop</a><a href="/cart">Cart ({sum(cart.values())})</a><a href="/profile">Profile</a></div>
    """

@app.route("/checkout", methods=["POST"])
def checkout():
    cart=session.get('cart', {})
    if not cart: return redirect("/")
    code=gen_unique_code()
    con=sqlite3.connect(DB); c=con.cursor()
    total=0
    for pid, qty in cart.items():
        c.execute("SELECT * FROM products WHERE id=?", (pid,))
        p=c.fetchone()
        if p:
            total+=p[2]*qty
            c.execute("INSERT INTO cart_items (cart_code, product, price, qty) VALUES (?,?,?,?)", (code,p[1],p[2],qty))
            c.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, pid)) # 6. STOCK REDUCE HERE
    c.execute("INSERT INTO carts (code,status,total,time,items_count) VALUES (?,?,?,?,?)", (code,"Submitted",total,datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), len(cart)))
    con.commit(); con.close()
    # save to profile history
    hist=session.get('history', []); hist.append(code); session['history']=hist
    session['cart']={}
    return BASE+f"<div class=card><h3>Receipt Generated</h3><p>Code: <b>{code}</b></p><p>Total: ₦{total}</p><p>Give this code to staff for payment sync.</p><a href='/'>Continue Shopping</a></div>"

@app.route("/profile")
def profile():
    hist=session.get('history', [])
    con=sqlite3.connect(DB); c=con.cursor()
    html=BASE+"<h3 style='padding:10px'>Purchase History</h3>"
    for code in reversed(hist):
        c.execute("SELECT * FROM carts WHERE code=?", (code,)); cart=c.fetchone()
        if cart: html+=f"<div class=card>{cart[0]}<br>Status: {cart[1]} | ₦{cart[2]}<br>{cart[3]}</div>"
    if not hist: html+="<div class=card>No history yet</div>"
    con.close()
    html+=f"<div class=nav><a href='/'>Shop</a><a href='/cart'>Cart (0)</a><a href='/profile'>Profile</a></div>"
    return html

# SECRET - STAFF
@app.route("/staff/", methods=["GET","POST"])
def staff_login():
    if request.method=="POST" and request.form['pin']=="1234":
        session['staff']="STAFF-001"; return redirect("/staff/dash")
    return BASE+"<div class=card><h3>Staff Login</h3><form method=post><input name=pin type=password placeholder=PIN><button>Login</button></form></div>"

@app.route("/staff/dash")
def staff_dash():
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("SELECT * FROM carts WHERE status='Submitted' ORDER BY time DESC"); orders=c.fetchall(); con.close()
    html=BASE+"<h3>Receive Orders</h3>"
    for o in orders:
        html+=f"<div class=card>{o[0]} - ₦{o[2]} - {o[3]}<br><a href='/staff/sync/{o[0]}'><button style=background:green;color:white;padding:6px>Sync Payment</button></a></div>"
    return html

@app.route("/staff/sync/<code>")
def sync(code):
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("UPDATE carts SET status='Paid - Receipt' WHERE code=?", (code,)); con.commit(); con.close()
    return redirect("/staff/dash")

# SECRET - MD
@app.route("/md/", methods=["GET","POST"])
def md_login():
    if request.method=="POST" and request.form['pin']=="9999":
        session['md']=True; return redirect("/md/dash")
    return BASE+"<div class=card><h3>MD Login</h3><form method=post><input name=pin type=password><button>Login</button></form></div>"

@app.route("/md/dash")
def md_dash():
    con=sqlite3.connect(DB); c=con.cursor()
    c.execute("SELECT * FROM products"); prods=c.fetchall()
    c.execute("SELECT * FROM carts ORDER BY time DESC LIMIT 20"); carts=c.fetchall()
    con.close()
    html=BASE+f"<h3>MD - Stock Control</h3>"
    for p in prods: html+=f"<div class=card>{p[1]} - Stock: {p[3]} <form method=post action='/md/update/{p[0]}'><input type=number name=stock value={p[3]}><button>Update</button></form></div>"
    html+="<h3>All Receipts</h3>"
    for ca in carts: html+=f"<div class=card>{ca[0]} - {ca[1]} - ₦{ca[2]}</div>"
    return html

@app.route("/md/update/<int:pid>", methods=["POST"])
def md_update(pid):
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("UPDATE products SET stock=? WHERE id=?", (request.form['stock'], pid)); con.commit(); con.close()
    return redirect("/md/dash")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
