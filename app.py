import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            balance NUMERIC(12,2) DEFAULT 0,
            email TEXT,
            phone TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cheques (
            id SERIAL PRIMARY KEY,
            pharmacy TEXT NOT NULL,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            cheque_number TEXT,
            amount NUMERIC(12,2) NOT NULL,
            issue_date DATE,
            due_date DATE NOT NULL,
            employer_name TEXT,
            status TEXT DEFAULT 'OPEN',
            reminder_sent BOOLEAN DEFAULT FALSE
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()


init_db()


@app.route("/")
def index():
    return redirect(url_for("list_cheques"))


@app.route("/suppliers", methods=["GET", "POST"])
def list_suppliers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        balance = request.form.get("balance", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if name:
            try:
                balance_val = float(balance) if balance else 0.0
            except ValueError:
                balance_val = 0.0

            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO suppliers (name, balance, email, phone)
                VALUES (%s, %s, %s, %s);
                """,
                (name, balance_val, email, phone),
            )
            conn.commit()
            cur.close()
            conn.close()

        return redirect(url_for("list_suppliers"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, balance, email, phone
        FROM suppliers
        ORDER BY id;
        """
    )
    suppliers = cur.fetchall()
    cur.close()
    conn.close()

    html = """
    <h1>Προμηθευτές</h1>
    <form method="post">
        <label>Όνομα: <input type="text" name="name" required></label><br>
        <label>Υπόλοιπο: <input type="number" step="0.01" name="balance"></label><br>
        <label>Email: <input type="email" name="email"></label><br>
        <label>Τηλέφωνο: <input type="text" name="phone"></label><br>
        <button type="submit">Προσθήκη</button>
    </form>
    <hr>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th><th>Όνομα</th><th>Υπόλοιπο</th><th>Email</th><th>Τηλέφωνο</th>
        </tr>
        {% for s in suppliers %}
        <tr>
            <td>{{ s.id }}</td>
            <td>{{ s.name }}</td>
            <td>{{ "%.2f"|format(s.balance or 0) }}</td>
            <td>{{ s.email or "" }}</td>
            <td>{{ s.phone or "" }}</td>
        </tr>
        {% endfor %}
    </table>
    <p><a href="{{ url_for('list_cheques') }}">Επιταγές</a></p>
    """
    return render_template_string(html, suppliers=suppliers)


@app.route("/cheques", methods=["GET", "POST"])
def list_cheques():
    if request.method == "POST":
        pharmacy = request.form.get("pharmacy", "").strip()
        supplier_id = request.form.get("supplier_id", "").strip()
        cheque_number = request.form.get("cheque_number", "").strip()
        amount = request.form.get("amount", "").strip()
        issue_date = request.form.get("issue_date", "").strip()
        due_date = request.form.get("due_date", "").strip()
        employer_name = request.form.get("employer_name", "").strip()

        if pharmacy and supplier_id and amount and due_date:
            try:
                amount_val = float(amount)
            except ValueError:
                amount_val = 0.0

            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO cheques
                    (pharmacy, supplier_id, cheque_number, amount,
                     issue_date, due_date, employer_name, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, 'OPEN');
                """,
                (pharmacy, int(supplier_id), cheque_number, amount_val,
                 issue_date or None, due_date, employer_name),
            )
            conn.commit()
            cur.close()
            conn.close()

        return redirect(url_for("list_cheques"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM suppliers ORDER BY name;")
    suppliers = cur.fetchall()

    cur.execute(
        """
        SELECT
            c.id,
            c.pharmacy,
            c.cheque_number,
            c.amount,
            c.issue_date,
            c.due_date,
            c.employer_name,
            c.status,
            s.name AS supplier_name
        FROM cheques c
        LEFT JOIN suppliers s ON c.supplier_id = s.id
        ORDER BY c.due_date, c.id;
        """
    )
    cheques = cur.fetchall()
    cur.close()
    conn.close()

    html = """
    <h1>Επιταγές</h1>
    <form method="post">
        <label>Φαρμακείο: <input type="text" name="pharmacy" required></label><br>

        <label>Προμηθευτής:
            <select name="supplier_id" required>
                <option value="">--Επιλογή--</option>
                {% for s in suppliers %}
                <option value="{{ s.id }}">{{ s.name }}</option>
                {% endfor %}
            </select>
        </label><br>

        <label>Αρ. Επιταγής: <input type="text" name="cheque_number"></label><br>
        <label>Ποσό: <input type="number" step="0.01" name="amount" required></label><br>
        <label>Ημ/νία Έκδοσης (YYYY-MM-DD):
            <input type="text" name="issue_date">
        </label><br>
        <label>Ημ/νία Λήξης (YYYY-MM-DD):
            <input type="text" name="due_date" required>
        </label><br>
        <label>Εργοδότης (όνομα): <input type="text" name="employer_name"></label><br>

        <button type="submit">Προσθήκη Επιταγής</button>
    </form>

    <hr>
    <table border="1" cellpadding="5">
        <tr>
            <th>ID</th><th>Φαρμακείο</th><th>Προμηθευτής</th>
            <th>Αρ. Επιταγής</th><th>Ποσό</th>
            <th>Έκδοση</th><th>Λήξη</th><th>Εργοδότης</th><th>Κατάσταση</th>
        </tr>
        {% for c in cheques %}
        <tr>
            <td>{{ c.id }}</td>
            <td>{{ c.pharmacy }}</td>
            <td>{{ c.supplier_name or "" }}</td>
            <td>{{ c.cheque_number or "" }}</td>
            <td>{{ "%.2f"|format(c.amount or 0) }}</td>
            <td>{{ c.issue_date or "" }}</td>
            <td>{{ c.due_date }}</td>
            <td>{{ c.employer_name or "" }}</td>
            <td>{{ c.status }}</td>
        </tr>
        {% endfor %}
    </table>
    <p><a href="{{ url_for('list_suppliers') }}">Προμηθευτές</a></p>
    """
    return render_template_string(html, suppliers=suppliers, cheques=cheques)


if __name__ == "__main__":
    # Για τοπικό testing μόνο. Στο Railway τρέχει με gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))