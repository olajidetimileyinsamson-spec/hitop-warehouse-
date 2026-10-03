from flask import Flask, request, redirect, session, make_response, send_from_directory
import sqlite3, os, datetime, uuid, io

app = Flask(__name__)
app.secret_key = "titech-hitop-final-complete-2026"
DB="hitop.db"

MY_NAME = "Timileyin Samson (Titech)"
MY_WHATSAPP = "2349025606097"
MY_AI_LINK = "https://titech-ai.onrender.com"
MY_WHATSAPP_DISPLAY = "+234 902 560 6097"

def init_db():
    con=sqlite3.connect(DB); c=con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, stock INTEGER, category TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS carts (code TEXT PRIMARY KEY, status TEXT, total INTEGER, time TEXT, items_count INTEGER, customer_email TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cart_items (id INTEGER PRIMARY KEY, cart_code TEXT, product TEXT, price INTEGER, qty INTEGER)")
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0]==0:
        c.executemany("INSERT INTO products (name,price,stock,category) VALUES (?,?,?,?)", [("Rice 50kg",28500,50,"Grains"),("Oil 5L",12900,3,"Cooking"),("Soft Drinks Carton",3200,25,"Drinks")])
    con.commit(); con.close()
init_db()

def gen_code():
    return f"HITOP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

@app.route('/logo.png')
def serve_logo():
    return send_from_directory('.', 'logo.png')

BASE_HEAD = f"""
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:Arial;margin:0;padding-bottom:120px;background:#f5f5f5}}
.header{{background:#c40000;color:white;padding:22px 18px;display:flex;align-items:center;gap:15px;position:sticky;top:0;z-index:20}}
.header img{{height:65px;width:65px;object-fit:contain;background:white;border-radius:12px;padding:4px}}
.logo-text{{font-size:36px;font-weight:900;background:white;color:#c40000;padding:6px 14px;border-radius:10px}}
.header b{{font-size:26px;display:block}}.header small{{font-size:15px}}
.search{{width:92%;padding:18px 20px;margin:16px auto;display:block;border-radius:30px;border:2px solid #bbb;font-size:22px;background:white}}
.card{{background:white;border-radius:14px;padding:20px;margin:14px;box-shadow:0 2px 6px rgba(0,0,0,0.05);font-size:19px}}
.prod-name{{font-size:26px;font-weight:900}}.prod-price{{font-size:21px;font-weight:700;margin:8px 0}}
.btn-add{{width:100%;background:#c40000;color:white;border:none;border-radius:8px;padding:11px 0;font-size:18px;font-weight:900;letter-spacing:0.5px;cursor:pointer}}
.qty{{width:65px;padding:10px;font-size:18px;border-radius:6px;border:1px solid #ccc;text-align:center}}
.nav{{position:fixed;bottom:0;width:100%;display:flex;justify-content:space-around;background:white;border-top:2px solid #ddd;padding:16px 0;z-index:30}}
.nav a{{color:#c40000;text-decoration:none;font-weight:900;font-size:16px}}
.titech-badge{{position:fixed;bottom:56px;left:0;right:0;background:#0a0a0a;color:white;text-align:center;padding:12px 8px;font-size:12px;z-index:25;line-height:1.4}}
.titech-badge a{{text-decoration:none;font-weight:bold}}.green{{color:#25D366}}.blue{{color:#00d1ff}}
.low{{color:red;font-weight:900;background:#ffe0e0;padding:6px 10px;border-radius:6px}}.ok{{color:green;font-weight:bold}}
.btn{{padding:12px 16px;border:none;border-radius:8px;color:white;font-weight:900;cursor:pointer}}
</style>
<div class="header">
  <img src="/logo.png" onerror="this.style.display='none'; document.getElementById('fb').style.display='block'">
  <div id="fb" class="logo-text" style="display:none">HITOP</div>
  <div><b>Hitop Warehouse - ACO Branch</b><small> Aco/Amac Estate, Abuja</small></div>
</div>
<div class="titech-badge">Built by <b>{MY_NAME}</b> | <a class="blue" href="{MY_AI_LINK}" target="_blank">🤖 {MY_AI_LINK}</a> | <a class="green" href="https://wa.me/{MY_WHATSAPP}" target="_blank">💬 WhatsApp: {MY_WHATSAPP_DISPLAY}</a></div>
"""

@app.route("/")
def shop():
    if not session.get('email'): return redirect("/login")
    q=request.args.get("q",""); cat=request.args.get("cat","")
    con=sqlite3.connect(DB); c=con.cursor()
    query="SELECT * FROM products"; params=[]
    if q: query+=" WHERE name LIKE?"; params.append('%'+q+'%')
    elif cat: query+=" WHERE category=?"; params.append(cat)
    c.execute(query, params); products=c.fetchall()
    c.execute("SELECT DISTINCT category FROM products"); cats=c.fetchall(); con.close()
    cart=session.get('cart',{})
    html=BASE_HEAD+f'<div style="padding:10px">Hi, {session["email"]}</div><form><input class="search" name="q" placeholder="🔍 Search goods..." value="{q}"></form>'
    html+='<div style="display:flex;gap:8px;overflow:auto;padding:0 14px">'
    html+=f'<a href="/"><button class="btn" style="background:#222">All</button></a>'
    for ct in cats: html+=f'<a href="/?cat={ct[0]}"><button class="btn" style="background:#c40000">{ct[0]}</button></a>'
    html+='</div>'
    for p in products:
        stock_badge = f'<span class="low">LOW STOCK! {p[3]} left</span>' if p[3]<10 else f'<span class="ok">In Stock: {p[3]}</span>'
        html+=f"""<div class="card"><div class="prod-name">{p[1]}</div><small>{p[4]}</small><div class="prod-price">₦{p[2]}<br>{stock_badge}</div>
        <div style="display:flex;gap:10px;align-items:center;margin-top:10px">
        <input class="qty" type="number" value="1" min="1" max="{p[3]}" id="q{p[0]}">
        <form method="post" action="/add/{p[0]}" style="flex:1" onsubmit="this.qty.value=document.getElementById('q{p[0]}').value">
        <input type="hidden" name="qty" value="1"><button class="btn-add">Add to Cart</button></form></div></div>"""
    html+=f'<div class="nav"><a href="/">Shop</a><a href="/cart">Cart ({sum(cart.values()) if cart else 0})</a><a href="/profile">Profile</a></div>'
    return html

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST": session['email']=request.form['email']; session['history']=session.get('history',[]); return redirect("/")
    return BASE_HEAD+'<div class="card"><h3>Customer Login</h3><form method=post><input name=email type=email required placeholder="Enter email" style="width:95%;padding:16px;font-size:20px"><br><br><button class="btn" style="background:#c40000;width:100%">Continue</button></form></div>'

@app.route("/add/<int:pid>", methods=["POST"])
def add(pid):
    qty=int(request.form.get("qty",1)); cart=session.get('cart',{}); cart[str(pid)]=cart.get(str(pid),0)+qty; session['cart']=cart; return redirect("/")

@app.route("/cart")
def view_cart():
    cart=session.get('cart',{})
    if not cart: return BASE_HEAD+"<div class=card>Cart empty</div><div class=nav><a href='/'>Shop</a><a href='/cart'>Cart (0)</a><a href='/profile'>Profile</a></div>"
    con=sqlite3.connect(DB); c=con.cursor(); total=0; items_html=""
    for pid,qty in cart.items():
        c.execute("SELECT * FROM products WHERE id=?",(pid,)); p=c.fetchone()
        if p: total+=p[2]*qty; items_html+=f"<div class=card>{p[1]} x {qty} = ₦{p[2]*qty}</div>"
    con.close()
    return BASE_HEAD+items_html+f'<div class="card"><b style="font-size:22px">Total: ₦{total}</b><form method=post action="/checkout"><button class="btn" style="width:100%;background:#222">Submit - Generate Receipt Code</button></form></div><div class="nav"><a href="/">Shop</a><a href="/cart">Cart ({sum(cart.values())})</a><a href="/profile">Profile</a></div>'

@app.route("/checkout", methods=["POST"])
def checkout():
    cart=session.get('cart',{});
    if not cart: return redirect("/")
    code=gen_code(); con=sqlite3.connect(DB); c=con.cursor(); total=0
    for pid,qty in cart.items():
        c.execute("SELECT * FROM products WHERE id=?",(pid,)); p=c.fetchone()
        if p: total+=p[2]*qty; c.execute("INSERT INTO cart_items VALUES (NULL,?,?,?,?)",(code,p[1],p[2],qty)); c.execute("UPDATE products SET stock=stock-? WHERE id=?",(qty,pid))
    c.execute("INSERT INTO carts VALUES (?,?,?,?,?,?)",(code,"Submitted",total,datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),len(cart),session.get('email','')))
    con.commit(); con.close(); session['history']=session.get('history',[])+[code]; session['cart']={}; return redirect(f"/receipt/{code}")

@app.route("/receipt/<code>")
def receipt(code):
    con=sqlite3.connect(DB); c=con.cursor()
    c.execute("SELECT * FROM carts WHERE id=?", (code,))
    cart=c.fetchone()
    if not cart:
        con.close()
        return "Not found <a href='/'>Shop</a>"
    c.execute("SELECT * FROM cart_items WHERE cart_id=?", (code,))
    items=c.fetchall()
    con.close()

    status = cart[4] if len(cart) > 4 else "Submitted"
    is_paid = "PAID" in str(status).upper()
    rows="".join([f"<tr><td>{i[1]}</td><td>{i[2]}</td><td>₦{i[3]}</td><td>₦{i[4]}</td></tr>" for i in items])

    return f"""<html><head><meta name="viewport" content="width=device-width">
    <style>.btn{{padding:10px;border:0;border-radius:8px;color:#fff}}</style></head>
    <body><div style="display:flex;align-items:center;gap:10px"><img src="/logo.png" style="height:45px">
    <h2>HITOP Warehouse</h2></div>
    <p><b>Code:</b> {cart[0]}<br><b>Email:</b> {cart[1]}<br>
    <b>Status:</b> <span style="color:{'green' if is_paid else 'orange'};font-weight:bold">{'PAID ✅' if is_paid else 'PENDING ⏳ - Await Staff'}</span></p>
    {'<div style="background:#fff3cd;padding:10px;border-radius:8px;border:1px solid orange">Awaiting staff confirmation. Print/PDF go show after staff confirm payment.</div>' if not is_paid else ''}
    <table border=1 cellpadding=8 style="width:100%;border-collapse:collapse;margin-top:10px"><tr><th>Product</th><th>Qty</th><th>Price</th><th>Sub</th></tr>{rows}</table>
    <h3>Total: ₦{cart[2]}</h3>
    {'<div class="no-print"><button class="btn" onclick="window.print()" style="background:#111">🖨️ Print</button> <a href="/receipt/{code}/pdf"><button class="btn" style="background:#c40000">📄 PDF</button></a> <a href="https://wa.me/?text=My HITOP Receipt '+code+'"><button class="btn" style="background:#25D366">Share</button></a></div>' if is_paid else '<small>Print/PDF locked until PAID</small>'}
    <br><br>
    <a href="/">Shop</a> | <a href="/profile">Profile</a>
    </div></body></html>
    """

@app.route("/receipt/<code>/pdf")
def receipt_pdf(code):
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("SELECT * FROM carts WHERE code=?",(code,)); cart=c.fetchone(); c.execute("SELECT * FROM cart_items WHERE cart_code=?",(code,)); items=c.fetchall(); con.close()
    try:
        from reportlab.pdfgen import canvas; from reportlab.lib.pagesizes import A4
        buf=io.BytesIO(); p=canvas.Canvas(buf, pagesize=A4); p.setFont("Helvetica-Bold",16); p.drawString(50,800,"Hitop Warehouse Receipt"); p.setFont("Helvetica",11)
        p.drawString(50,780,f"Code: {cart[0]}"); p.drawString(50,765,f"Customer: {cart[5]}"); p.drawString(50,750,f"Time: {cart[3]}")
        y=720
        for it in items: p.drawString(50,y,f"{it[2]} x{it[4]} ₦{it[3]} = ₦{it[3]*it[4]}"); y-=18
        p.setFont("Helvetica-Bold",13); p.drawString(50,y-20,f"TOTAL: ₦{cart[2]}"); p.showPage(); p.save(); buf.seek(0)
        r=make_response(buf.getvalue()); r.headers['Content-Type']='application/pdf'; r.headers['Content-Disposition']=f'attachment; filename={code}.pdf'; return r
    except: return redirect(f"/receipt/{code}")

# PROFILE WITH ABOUT - THIS WAS MISSING BEFORE
@app.route("/profile")
def profile():
    if not session.get('email'): return redirect("/login")
    con=sqlite3.connect(DB); c=con.cursor()
    ABOUT = """
    <div class="card" style="border-left:6px solid #c40000">
        <h3 style="margin-top:0">📍 About Hitop Stores</h3>
        <div style="line-height:1.9">
            <div><b>Aco / Amac shopping complex, Aco Estate, off Airport road, Abuja., Abuja, Nigeria</b><br><small style="color:gray">Address</small></div><hr>
            <div><a href="tel:08102685222" style="font-size:22px;font-weight:900;color:#111;text-decoration:none">08102685222</a><br><small style="color:gray">Mobile</small></div><hr>
            <div><a href="mailto:hitopstores@gmail.com" style="font-weight:900;color:#111">hitopstores@gmail.com</a><br><small style="color:gray">Email</small></div><hr>
            <div><a href="https://wa.me/2348102685222" target="_blank" style="font-size:22px;font-weight:900;color:#25D366;text-decoration:none">08102685222</a><br><small style="color:gray">WhatsApp (Store)</small></div><hr>
            <div><a href="https://instagram.com/hitopstores" target="_blank" style="font-weight:900;color:#111">instagram.com/hitopstores</a></div><hr>
            <div><a href="http://www.hitopstores.nig.com/" target="_blank" style="font-weight:900;color:#111">www.hitopstores.nig.com</a></div>
        </div>
    </div>
    """
    html = BASE_HEAD + f"<div class=card><b>Logged in:</b> {session.get('email')}<br><a href='/logout' style='color:#c40000;font-weight:bold'>Logout</a></div>" + ABOUT
    html+='<div class="card"><h3>🧾 My Purchase History</h3></div>'
    total=0
    for code in reversed(session.get('history',[])):
        c.execute("SELECT * FROM carts WHERE code=?",(code,)); ct=c.fetchone()
        if ct: total+=ct[2]; html+=f"<div class=card><a href='/receipt/{ct[0]}' style='font-weight:900;color:#c40000'>{ct[0]}</a><br>₦{ct[2]} - {ct[1]}<br><small>{ct[3]}</small><br><a href='/receipt/{ct[0]}/pdf' style='color:green;font-weight:bold'>📄 PDF</a></div>"
    html+=f"<div class=card><b>Total Spent: ₦{total}</b></div>"
    con.close()
    html+=f"<div class=nav><a href='/'>Shop</a><a href='/cart'>Cart</a><a href='/profile'>Profile</a></div>"
    return html

@app.route("/about")
def about(): return redirect("/profile")

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

@app.route("/staff/", methods=["GET","POST"])
def staff_login():
    if request.method=="POST" and request.form['pin']=="1234": session['staff']="STAFF-001"; return redirect("/staff/dash")
    return BASE_HEAD+"<div class=card><h3>Staff Login</h3><form method=post><input name=pin type=password placeholder='PIN 1234' style='padding:12px'><button class=btn style=background:#222>Login</button></form></div>"
    
@app.route("/staff/dash", methods=["GET","POST"]) # <- Add methods
def staff_dash():
    if not session.get('is_staff'):
        return redirect('/staff/')
    con=sqlite3.connect(DB); c=con.cursor()

    # === 1. WALK-IN CODE - PASTE HERE ===
    if request.method=="POST" and 'walkin_product' in request.form:
        prod_id = request.form['walkin_product']
        qty = int(request.form['walkin_qty'])
        cust_email = request.form.get('walkin_email') or "walkin@hitop.com"
        c.execute("SELECT * FROM products WHERE id=?", (prod_id,))
        p = c.fetchone()
        if p and p[3] >= qty:
            import datetime
            cart_id = f"HITOP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-WALKIN"
            total = p[2] * qty
            c.execute("INSERT INTO carts VALUES (?,?,?,?,?)",
                      (cart_id, cust_email, total, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "PAID"))
            c.execute("INSERT INTO cart_items (cart_id,product,qty,price,subtotal) VALUES (?,?,?,?,?)",
                      (cart_id, p[1], qty, p[2], total))
            c.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, prod_id))
            con.commit()

    if request.method=="POST" and 'sync_id' in request.form:
        c.execute("UPDATE carts SET status='PAID' WHERE id=?", (request.form['sync_id'],))
        con.commit()

    c.execute("SELECT * FROM products"); prods=c.fetchall()
    c.execute("SELECT * FROM carts ORDER BY time DESC"); orders=c.fetchall()
    # === END ===

    html=BASE_HEAD+"<h3 style=padding:12px>Staff Dashboard</h3>"

    # === WALK-IN FORM ===
    html+=f"""
    <div class="card" style="border:3px solid #111;padding:15px;margin:15px 0;background:#fff">
    <h3>➕ Add Walk-In Sale</h3>
    <form method=post>
    <select name=walkin_product required style="width:100%;padding:12px;margin:5px 0">
    <option value="">-- Select Product --</option>
    """
    for p in prods:
        html+=f'<option value="{p[0]}">{p[1]} - ₦{p[2]} (Stock:{p[3]})</option>'
    html+="""
    </select>
    <div style="display:flex;gap:5px">
    <input name=walkin_qty type=number min=1 placeholder="Qty" required style="width:48%;padding:12px">
    <input name=walkin_email placeholder="Phone (optional)" style="width:48%;padding:12px">
    </div>
    <button style="background:#111;color:#fff;width:100%;padding:12px;margin-top:5px;border-radius:8px">💰 Add Sale</button>
    </form></div>
    <h3>Recent Orders</h3>
    """

    for o in orders:
        html+=f"<div class=card><b>{o[0]}</b><br>{o[5]} - ₦{o[2]} - {o[1]}<br><br><a href='/receipt/{o[0]}'><button class=btn style=background:#222>🖨️ View/Print</button></a> <a href='/receipt/{o[0]}/pdf'><button class=btn style=background:#c40000>📄 PDF Share</button></a> <a href='/staff/sync/{o[0]}'><button class=btn style=background:green>Sync Paid</button></a></div>"
    html+=f"<div style=padding:12px><a href='/md/'><button class=btn style=background:#111>MD Page - Low Stock Alert</button></a></div>"
    return html

@app.route("/md/", methods=["GET","POST"])
def md_page():
    con=sqlite3.connect(DB); c=con.cursor()
    if request.method=="POST" and 'add' in request.form:
        try: c.execute("UPDATE products SET stock=stock+? WHERE id=?",(int(request.form['add']), request.form['id'])); con.commit()
        except: pass
    if request.method=="POST" and 'new_name' in request.form:
        c.execute("INSERT INTO products (name,price,stock,category) VALUES (?,?,?,?)",(request.form['new_name'], int(request.form['new_price']), int(request.form['new_stock']), request.form['new_cat'])); con.commit()
    c.execute("SELECT * FROM products"); prods=c.fetchall()
    total_stock_value = sum([p[2]*p[3] for p in prods])
    low_count = len([p for p in prods if p[3] < 10])
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    date_filter = request.args.get("date", today_str)
    c.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM carts WHERE date(time)=?",(date_filter,))
    daily_count, daily_total = c.fetchone()
    c.execute("SELECT * FROM carts WHERE date(time)=? ORDER BY time DESC",(date_filter,)); daily_orders=c.fetchall()
    c.execute("SELECT product, SUM(qty) as sq FROM cart_items GROUP BY product ORDER BY sq DESC LIMIT 1"); best=c.fetchone()
    best_text = f"{best[0]} ({best[1]} sold)" if best else "No sales yet"
    c.execute("SELECT * FROM carts ORDER BY time DESC LIMIT 50"); all_orders=c.fetchall(); con.close()
    tab=request.args.get("tab","low")
    html=BASE_HEAD+f"""
    <div style="padding:14px"><h2>MD Dashboard</h2><small>Today: {today_str} | Viewing: {date_filter}</small>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0">
    <div class="card" style="margin:0;border-left:5px solid green"><small>Today Sales</small><br><b style="font-size:24px">₦{daily_total}</b><br><small>{daily_count} receipts</small></div>
    <div class="card" style="margin:0;border-left:5px solid #c40000"><small>Stock Value</small><br><b style="font-size:24px">₦{total_stock_value}</b></div>
    <div class="card" style="margin:0;border-left:5px solid orange"><small>Low Stock</small><br><b style="font-size:24px">{low_count}</b></div>
    <div class="card" style="margin:0;border-left:5px solid blue"><small>Best</small><br><b style="font-size:13px">{best_text}</b></div></div>
    <div style="display:flex;gap:8px;overflow:auto">
    <a href="/md/?tab=low"><button class="btn" style="background:#111">Low Stock</button></a>
    <a href="/md/?tab=daily&date={date_filter}"><button class="btn" style="background:#111">Daily Sales 📄</button></a>
    <a href="/md/?tab=all"><button class="btn" style="background:#111">All Products</button></a>
    <a href="/md/?tab=manage"><button class="btn" style="background:#111">Add Product</button></a></div>"""
    if tab=='daily':
        html+=f"""<div class="card"><form method=get style="display:flex;gap:8px"><input type=hidden name=tab value=daily>
        <input type=date name=date value="{date_filter}" style="padding:12px;flex:1"><button class="btn" style="background:#111">View</button></form>
        <h3>Sales {date_filter}</h3><b>Total: ₦{daily_total} - {daily_count} orders</b><br><br>
        <a href="/md/daily/pdf?date={date_filter}"><button class="btn" style="background:#c40000;width:100%">📄 Download Daily PDF</button></a></div>"""
        for o in daily_orders: html+=f"<div class=card><b>{o[0]}</b><br>{o[5]} - ₦{o[2]} - {o[1]}<br><small>{o[3]}</small></div>"
    elif tab=='manage':
        html+="""<div class="card"><h3>Add New Product</h3><form method=post><input name=new_name placeholder="Product Name" required style="width:100%;padding:12px;margin:5px 0">
        <input name=new_price type=number placeholder="Price" required style="width:48%;padding:12px"><input name=new_stock type=number placeholder="Stock" required style="width:48%;padding:12px">
        <input name=new_cat placeholder="Category" required style="width:100%;padding:12px;margin:5px 0"><button class="btn" style="background:#c40000;width:100%">Add</button></form></div>"""
    else:
        for p in ([x for x in prods if x[3]<10] if tab=='low' else prods):
            alert = f'<div class="low">⚠️ LOW STOCK! Only {p[3]} left</div>' if p[3]<10 else f'<div class="ok">Stock OK: {p[3]}</div>'
            html+=f"<div class=card><b style='font-size:24px'>{p[1]}</b> ({p[4]})<br>₦{p[2]}<br>{alert}<form method=post style=margin-top:10px><input type=hidden name=id value={p[0]}><input type=number name=add placeholder='Add qty' style=padding:10px;width:110px><button class=btn style=background:#c40000>Add Stock</button></form></div>"
    html+="</div><div class=nav><a href='/'>Shop</a><a href='/staff/dash'>Staff</a><a href='/md/?tab=daily'>Daily</a></div>"; return html

@app.route("/md/daily/pdf")
def md_daily_pdf():
    date_filter=request.args.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("SELECT * FROM carts WHERE date(time)=? ORDER BY time DESC",(date_filter,)); orders=c.fetchall(); con.close()
    total=sum([o[2] for o in orders])
    try:
        from reportlab.pdfgen import canvas; from reportlab.lib.pagesizes import A4; buf=io.BytesIO(); p=canvas.Canvas(buf, pagesize=A4)
        p.setFont("Helvetica-Bold",18); p.drawString(50,800,f"Hitop Daily Sales - {date_filter}"); p.setFont("Helvetica",12)
        p.drawString(50,780,f"Total: N{total} - Orders: {len(orders)} - Built by Titech {MY_AI_LINK}")
        y=750
        for o in orders: p.drawString(50,y,f"{o[3]} | {o[0]} | {o[5]} | N{o[2]}"); y-=18;
        p.drawString(50,y-20,f"GRAND TOTAL: N{total}"); p.showPage(); p.save(); buf.seek(0)
        r=make_response(buf.getvalue()); r.headers['Content-Type']='application/pdf'; r.headers['Content-Disposition']=f'attachment; filename=Daily-{date_filter}.pdf'; return r
    except Exception as e: return f"Need reportlab - pip install reportlab<br>{e}"

@app.route("/staff/sync/<code>")
def sync(code):
    con=sqlite3.connect(DB); c=con.cursor(); c.execute("UPDATE carts SET status='Paid - Receipt' WHERE code=?",(code,)); con.commit(); con.close(); return redirect(f"/receipt/{code}")

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
