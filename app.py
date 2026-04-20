from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "secret123"


# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            amount REAL,   -- ✅ supports decimal
            category TEXT,
            date TEXT,
            user_id INTEGER
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# ---------------- START ROUTE ----------------
@app.route('/')
def start():
    return render_template("welcome.html")


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()

            # ✅ Store success message in session
            session['flash_message'] = "Account created successfully 🎉"

            # ✅ Auto login
            session['user_id'] = cursor.lastrowid
            session['username'] = username
            session['just_logged_in'] = True

            conn.close()

            return redirect('/home')
            conn.close()

            return redirect('/login?signup=success')

        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Username already exists")

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    success = request.args.get('signup')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['just_logged_in'] = True
            return redirect('/home')
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error, success=success)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- HOME ----------------
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # -------- ADD EXPENSE --------
    if request.method == 'POST':
        name = request.form.get('name')
        amount = request.form.get('amount')
        category = request.form.get('category')

        # ✅ Validation
        if not name or not amount or not category:
            return redirect('/home')

        try:
            amount = float(amount)
        except:
            return redirect('/home')

        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO expenses (name, amount, category, date, user_id) VALUES (?, ?, ?, ?, ?)",
            (name, amount, category, date, user_id)
        )

        conn.commit()
        conn.close()

        return redirect('/home')

    # -------- FETCH EXPENSES --------
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM expenses WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )

    expenses = cursor.fetchall()
    conn.close()

    # -------- TOTAL --------
    total = round(sum(float(expense[2]) for expense in expenses), 2)

    # -------- CHART DATA --------
    categories = {}

    for expense in expenses:
        cat = expense[3]
        amt = float(expense[2])

        categories[cat] = categories.get(cat, 0) + amt

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        username=session.get('username'),
        play_sound=session.pop('just_logged_in', False),
        chart_data=categories
    )


# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return redirect('/home')


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()