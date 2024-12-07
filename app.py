import sqlite3
import sys
import pandas as pd
import io
import base64
import time
from datetime import datetime
from flask import Flask, redirect, url_for, request, render_template, flash, redirect, make_response
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

app = Flask(__name__)
app.config['SECRET_KEY'] = '92051f34a4e348cd1311488984333c199abe2e57cc1fa4bf'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

class AccountData(object):
    user_id = ""
    cur_listing_id = ""
    quantity = ""
    total_price = ""

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/menu')
def menu():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT name FROM users WHERE user_id = ?", (AccountData.user_id,)).fetchone()

    cur.close()
    con.close()

    return render_template("menu.html", name=result[0], time=(time.time()))


@app.route('/view')
def view():
    # for viewing existing listings
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    listings = cur.execute("SELECT listings.name, users.name, description, price, quantity FROM users JOIN listings ON users.user_id = listings.user_id WHERE available='y';").fetchall()
    l = []
    for listing in listings:
        l.append(listing)

    cur.close()
    con.close()

    return render_template('view.html', listings=l)


@app.route('/add')
def add():
    # for adding a new listing
    return render_template('add.html')


@app.route('/orders')
def orders():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT name FROM users WHERE user_id = ?", (AccountData.user_id,)).fetchone()

    orders = cur.execute("SELECT listings.name, listings.price, orders.total_quantity, users.name,  orders.order_date, orders.total_price FROM listings JOIN users ON listings.user_id = users.user_id JOIN order_listings ON listings.listing_id = order_listings.listing_id JOIN orders ON order_listings.order_id = orders.order_id WHERE orders.user_id = ?", (AccountData.user_id,)).fetchall()
    o = []
    for order in orders:
        o.append(order)

    cur.close()
    con.close()

    return render_template('orders.html', orders=o, name=result[0])


@app.route('/edit', methods=["GET", "POST"])
def edit():
    # for adding email or changing username/password
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE user_id = ?", (AccountData.user_id,))
    user_info = list(cur.fetchone())

    new_username = ""
    new_password = ""
    new_email = ""

    if request.method == "POST":
        new_username = request.form["new_username"]
        new_password = request.form["new_password"]
        new_email = request.form["new_email"]

    if (new_username != ""):
        cur.execute("UPDATE users SET name = ? WHERE user_id = ?", (new_username, AccountData.user_id))
        con.commit()
        return redirect(url_for("edit"))
    if (new_password != ""):
        cur.execute("UPDATE users SET password = ? WHERE user_id = ?", (new_password, AccountData.user_id))
        con.commit()
        return redirect(url_for("edit"))
    if (new_email != ""):
        cur.execute("UPDATE users SET email = ? WHERE user_id = ?", (new_email, AccountData.user_id))
        con.commit()
        return redirect(url_for("edit"))

    cur.close()
    con.close()

    return render_template('edit.html', user_info=user_info)


@app.route('/buy')
def buy():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    query = f"SELECT name, description, price, quantity FROM listings WHERE listing_id = ?;"
    data = cur.execute(query, (AccountData.cur_listing_id,)).fetchall()[0]
    
    print(type(data[2]), type(AccountData.quantity))
    price = float(data[2] * int(AccountData.quantity))
    tax = round(price * 0.06, 2)
    shipping = 2.99
    total = round(price + tax + shipping, 2)

    AccountData.total_price = str(total)

    con.close()

    return render_template("buy.html", name=data[0], description=data[1], quantity=AccountData.quantity, price=price, shipping=shipping, tax=tax, total=total)


@app.post('/confirm_credentials')
def confirm_credentials():
    username = request.form["l_username"]
    password = request.form["l_password"]

    if (username == ""):
        flash("Please enter a username.")
        return redirect(url_for("index"))
    if (password == ""):
        flash("Please enter a password.")
        return redirect(url_for("index"))

    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT user_id FROM users WHERE name = ? AND password = ?", (username, password)).fetchone()

    cur.close()
    con.close()

    if result != None:
        AccountData.user_id = str(result[0])
        return menu()
    else:
        flash("Login invalid.")
        return redirect(url_for("index"))


@app.post('/create_user')
def create_user():
    username = request.form["c_username"]
    password = request.form["c_password"]
    
    if (username == ""):
        flash("Username cannot be empty.")
        return redirect(url_for("index"))
    if (password == ""):
        flash("Password cannot be empty.")
        return redirect(url_for("index"))
    
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    result = cur.execute("SELECT name FROM users WHERE name = ?", (username,)).fetchone()
    if (result is not None):
        flash("Username already exists. Please try another.")
        return redirect(url_for("index"))
    
    cur.execute("INSERT INTO users(name, password) VALUES(?, ?)", (username, password))
    con.commit()

    result = cur.execute("SELECT user_id FROM users WHERE name = ? AND password = ?", (username, password)).fetchone()

    cur.close()
    con.close()

    if result != None:
        AccountData.user_id = str(result[0])
        return menu()
    else:
        flash("Login invalid.")
        return redirect(url_for("index"))


@app.post('/filter_search')
def filter_search():
    filter = request.form["text_search"]
    min_price = request.form["min_price"]
    max_price = request.form["max_price"]

    if min_price == "":
        min_price = 0
    if max_price == "":
        max_price = sys.maxsize

    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    query = "SELECT listings.name, users.name, description, price, quantity FROM users JOIN listings ON users.user_id = listings.user_id WHERE available='y' AND (listings.name LIKE ? OR description LIKE ?) AND price >= ? AND price <= ?;"
    text_filter = f"%{filter}%"
    listings = cur.execute(query, (text_filter, text_filter, min_price, max_price)).fetchall()
    l = []
    for listing in listings:
        l.append(listing)

    cur.close()
    con.close()

    return render_template('view.html', listings=l)


@app.post('/add_listing')
def add_listing():
    item_name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    quantity = request.form["quantity"]

    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    query = f"INSERT INTO listings(user_id, name, description, price, quantity, available) VALUES('{AccountData.user_id}', ?, ?, ?, ?, 'y')"
    cur.execute(query, (item_name, description, price, quantity))

    con.commit()

    cur.close()
    con.close()

    return redirect(url_for("view"))


@app.route('/purchase_listing', methods=["GET", "POST"])
def purchase_listing():
    name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    quantity = request.form["quantity"]

    AccountData.quantity = request.form["selected_quantity"]

    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    query = f"SELECT listing_id FROM listings WHERE name = ? AND description = ? AND price = ? AND quantity = ?;"
    AccountData.cur_listing_id = cur.execute(query, (name, description, price, quantity)).fetchone()[0]

    cur.close()
    con.close()

    return redirect(url_for("buy"))


@app.post('/confirm_purchase')
def confirm_purchase():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    original_quantity = cur.execute(f"SELECT quantity FROM listings WHERE listing_id=?;", (AccountData.cur_listing_id,)).fetchone()[0]
    new_quantity = int(original_quantity) - int(AccountData.quantity)

    query = f"UPDATE listings SET quantity=? WHERE listing_id=?;"
    cur.execute(query, (new_quantity, AccountData.cur_listing_id))

    if(new_quantity == 0):
        query = f"UPDATE listings SET available='n' WHERE listing_id=?;"
        cur.execute(query, (AccountData.cur_listing_id,))


    query = f"INSERT INTO orders(order_id, user_id, order_date, total_price, total_quantity) VALUES(?, ?, ?, ?, ?);"
    cur_time = datetime.now()
    order_date = cur_time.strftime("%m/%d/%y")
    other_order_date = cur_time.strftime("%m%d%y%M%S")

    order_id = other_order_date + AccountData.user_id

    cur.execute(query, (order_id, AccountData.user_id, order_date, AccountData.total_price, AccountData.quantity))

    query = f"INSERT INTO order_listings(order_id, listing_id) VALUES(?, ?);"
    cur.execute(query, (order_id, AccountData.cur_listing_id))

    AccountData.cur_listing_id = ""
    AccountData.quantity = ""
    AccountData.total_price = ""

    con.commit()
    con.close()

    return redirect(url_for("orders"))


@app.route("/graph_image")
def graph_image():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    df = pd.read_sql_query("SELECT users.name, COUNT(orders.user_id) AS order_count FROM users JOIN orders ON users.user_id = orders.user_id GROUP BY orders.user_id ORDER BY order_count DESC", con)
     
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(df["name"], df["order_count"], color="blue")
    ax.set_xlabel("User")
    ax.set_ylabel("Orders")
    ax.set_title("Orders Placed by Users")
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)
    
    con.close()

    return make_response(img.read()), 200, {"Content-Type": "image/png"}


@app.route("/graph_image_also")
def graph_image_also():
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    df = pd.read_sql_query("SELECT order_date, COUNT(order_id) AS count_order FROM orders GROUP BY order_date ORDER BY count_order DESC", con)
    
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(df["order_date"], df["count_order"], color="green")
    ax.set_xlabel("Date")
    ax.set_ylabel("Orders Placed")
    ax.set_title("Orders Placed by Day")
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)

    con.close()

    return make_response(img.read()), 200, {"Content-Type": "image/png"}


if __name__ == "__main__":
    app.run(threaded=False, debug=True)
