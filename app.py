import sqlite3
from flask import Flask, redirect, url_for, request, render_template, flash, redirect, make_response

app = Flask(__name__)
app.config['SECRET_KEY'] = '92051f34a4e348cd1311488984333c199abe2e57cc1fa4bf'

class AccountData(object):
    user_id = ""

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

    cur.execute("SELECT * FROM listings WHERE available = 'y'")
    listing_ids = [column[0] for column in cur.fetchall()]
    listings = []
    for listing_id in listing_ids:
        cur.execute("SELECT name, description, price, quantity FROM listings WHERE listing_id = ?", (listing_id,))
        listings.append(cur.fetchone())

    cur.close()
    con.close()

    return render_template('view.html', listings=listings)


@app.route('/add')
def add():
    # for adding a new listing
    return render_template('add.html')


@app.route('/edit')
def edit():
    # for adding email or changing username/password
    con = sqlite3.connect("XBayDB")
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE user_id = ?", (AccountData.user_id,))
    user_info = list(cur.fetchone())

    new_username = request.form["new_username"]
    new_email = request.form["new_email"]

    if (new_username != ""):
        cur.execute("UPDATE users SET name = ? WHERE user_id = ?", (new_username, AccountData.user_id))
        con.commit()
        return redirect(url_for("edit"))
    if (new_email != ""):
        cur.execute("UPDATE users SET email = ? WHERE user_id = ?", (new_email, AccountData.user_id))
        con.commit()
        return redirect(url_for("edit"))

    cur.close()
    con.close()

    return render_template('edit.html', user_info=user_info)


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


if __name__ == "__main__":
    app.run(debug=True)
