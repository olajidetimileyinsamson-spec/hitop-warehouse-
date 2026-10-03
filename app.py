from flask import Flask, request, session, redirect
import sqlite3, os, datetime
app = Flask(__name__)
app.secret_key = "titech-hitop-2026-secure"
DB = "hitop.db"

TITECH_LICENSE_KEY = "TITECH-HITOP-ACO-2026-TIMILEYIN"
TITECH_BADGE_TEXT = "⚡ Built by Titech | Timileyin Samson - titech-ai.onrender.com"
TITECH_LINK = "https://titech-ai.onrender.com"

def init_db():
    con=sqlite3.connect(DB)
    c=con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, role TEXT, pin TEXT, address TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, stock INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, customer TEXT, items TEXT, total INTEGER, status TEXT, payment TEXT, staff TEXT, time TEXT, license TEXT)")
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (name,phone,role,pin,address) VALUES ('MD','08000000000','admin','9999','ACO')")
        c.execute("INSERT INTO users (name,phone,role,pin,address) VALUES ('Musa Staff','08011111111','staff','1234','Warehouse')")
        c.execute("INSERT INTO products (name,price,stock) VALUES ('Rice 50kg',28500,50)")
        c.execute("INSERT INTO products (name,price,stock) VALUES ('Oil 5L',12900,30)")
        c.execute("INSERT INTO products (name,price,stock) VALUES ('Soft Drinks Carton',3200,100)")
    con.commit(); con.close()
init_db()

STYLE = """
<style>
body{font-family:sans-serif;margin:0;padding-bottom:90px;background:#fff;color:#111}
.header{background:#cc0000;color:#fff;padding:18px;border-radius:0 0 22px 22px}
.card{border:1px solid #ffcccc;margin:10px;padding:12px;border-radius:14px;background:#fff;box-shadow:0 2px 6px #ffdddd}
.btn{background:#cc0000;color:#fff;border:none;padding:12px;width:100%;border-radius:10px;font-weight:bold;margin-top:8px}
.titech{position:fixed;bottom:0;left:0;right:0;background:#000;color:#fff;text-align:center;padding:9px;font-size:11px;z-index:9999}
.titech a{color:#ff5555;text-decoration:none;font-weight:bold}
.nav{display:flex;justify-content:space-around;background:#fff;border-top:2px solid #cc0000;padding:10px;position:fixed;bottom:32px;left:0;right:0}
input{width:100%;padding:11px;margin:6px 0;border-radius:8px;border:1px solid #ccc}
</style>
"""

def badge(): return f"<div class=titech><a href='{TITECH_LINK}' target='_blank'>{TITECH_BADGE_TEXT}</a> | LIC: {TITECH_LICENSE_KEY[:20]}..</div>"
def lic_ok(): return os.environ.get("TITECH_LICENSE", TITECH_LICENSE_KEY) == TITECH_LICENSE_KEY

@app.route('/')
def home():
    con=sqlite3.connect(DB); prods=con.execute("SELECT * FROM products").fetchall(); con.close()
    h=STYLE+f"<div class=header><b>🏭 Hitop Warehouse</b><br><small>ACO Branch - Red & White Edition</small></div><div style='padding:10px'>"
    for p in prods: h+=f"<div class=card><b>{p[1]}</b><br>₦{p[2]} | Stock: {p[3]}<br><a href='/buy/{p[0]}'><button class=btn>Add to Cart</button></a></div>"
    h+=f"</div><div class=nav><a href='/'>Shop</a><a href='/staff'>Staff</a><a href='/admin'>MD</a><a href='/profile'>Profile</a></div>{badge()}"; return h

@app.route('/buy/<int:pid>')
def buy(pid):
    if not lic_ok(): return "LICENSE Invalid - Contact Titech for renewal", 403
    con=sqlite3.connect(DB); p=con.execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
    con.execute("INSERT INTO orders (customer,items,total,status,payment,staff,time,license) VALUES (?,?,?,?,?,?,?,?)",(session.get('name','Guest'),p[1],p[2],'NEW','Pending','None',str(datetime.datetime.now())[:19],TITECH_LICENSE_KEY)); con.commit(); con.close()
    return redirect('/')

@app.route('/profile', methods=['GET','POST'])
def profile():
    if request.method=='POST':
        session['name']=request.form['name']; con=sqlite3.connect(DB); con.execute("INSERT INTO users (name,phone,role,address) VALUES (?,?,?,?)",(request.form['name'],request.form['phone'],'customer',request.form['address'])); con.commit(); con.close(); return redirect('/')
    return STYLE+f"<div class=header>Customer Profile - Saves Forever (hitop.db)</div><form method=post style='padding:20px'><input name=name placeholder='Full Name' required><input name=phone placeholder='Phone' required><input name=address placeholder='Address' required><button class=btn>Save Profile</button></form>{badge()}"

@app.route('/staff', methods=['GET','POST'])
def staff():
    if not lic_ok(): return STYLE+f"<div class=header style='background:#000'>LICENSE EXPIRED</div><div style='padding:20px'><h3 style='color:red'>Hitop License Expired</h3><p>Contact Titech: {TITECH_BADGE_TEXT}</p></div>{badge()}"
    if request.method=='POST' and request.form['pin']=='1234': session['staff']='Musa'; session['role']='staff'; return redirect('/staff/dash')
    if session.get('role')=='staff': return redirect('/staff/dash')
    return STYLE+"<div class=header>Staff PIN Login</div><form method=post style='padding:20px'><input name=pin type=password placeholder='Staff PIN 1234'><button class=btn>Login</button></form>"+badge()

@app.route('/staff/dash')
def s_dash():
    if session.get('role')!='staff': return redirect('/staff')
    con=sqlite3.connect(DB); orders=con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall(); con.close()
    h=STYLE+f"<div class=header>Staff: {session['staff']} | Order Receive & Payment Sync</div><div style='padding:10px'>"
    for o in orders: h+=f"<div class=card>#{o[0]} {o[2]} ₦{o[3]} | {o[1]} | Pay:{o[5]}<br><a href='/staff/pay/{o[0]}'><button class=btn>💳 Sync Payment -> MD Sees</button></a></div>"
    h+=f"</div>{badge()}"; return h

@app.route('/staff/pay/<int:id>')
def s_pay(id):
    con=sqlite3.connect(DB); con.execute("UPDATE orders SET payment='Received', staff=? WHERE id=?",(session.get('staff'),id)); con.commit(); con.close(); return redirect('/staff/dash')

@app.route('/admin', methods=['GET','POST'])
def admin():
    if not lic_ok(): return "LICENSE Invalid - Contact Titech", 403
    if request.method=='POST' and request.form['pin']=='9999': session['role']='admin'; return redirect('/admin/dash')
    if session.get('role')=='admin': return redirect('/admin/dash')
    return STYLE+"<div class=header>MD Remote Login - From Anywhere</div><form method=post style='padding:20px'><input name=pin type=password placeholder='MD PIN 9999'><button class=btn>Login</button></form>"+badge()

@app.route('/admin/dash')
def a_dash():
    if session.get('role')!='admin': return redirect('/admin')
    con=sqlite3.connect(DB); total=con.execute("SELECT SUM(total) FROM orders WHERE payment='Received'").fetchone()[0] or 0; orders=con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall(); con.close()
    h=STYLE+f"<div class=header>Admin MD - Total Sales ₦{total} | License OK - {TITECH_LICENSE_KEY}</div><div style='padding:10px'><div class=card style='background:#ffeeee'><b>🤖 AI Space Reserved</b><br>For daily sales summary & low stock forecast (Titech AI go enter here later)</div>"
    for o in orders: h+=f"<div class=card><small>#{o[0]} | {o[7]} | {o[1]} bought {o[2]} ₦{o[3]} | Staff:{o[6]} | Pay:{o[5]} | Lic:{o[8][:10]}</small></div>"
    h+=f"</div>{badge()}"; return h

if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
