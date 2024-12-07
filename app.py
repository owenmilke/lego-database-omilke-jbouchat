import sqlite3
import sys
from flask import Flask, redirect, url_for, request, render_template, flash, redirect, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = '92051f34a4e348cd1311488984333c199abe2e57cc1fa4bf'

class AccountData(object):
    user_id = ""
    cur_listing_id = ""
    quantity = ""

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

    return render_template("menu.html", name=result[0])


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
    data = cur.execute(query, (AccountData.cur_listing_id,)).fetchall()
    
    price = data[2] * AccountData.quantity
    tax = price * 0.06
    shipping = 2.99
    total = price + tax + shipping

    con.close()
    cur.close()

    return render_template("buy.html", name=data[0], description=data[1], quantity=data[3], price=price, shipping=shipping, tax=tax, total=total)


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


@app.post('/purchase_listing')
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


if __name__ == "__main__":
    app.run(debug=True)
