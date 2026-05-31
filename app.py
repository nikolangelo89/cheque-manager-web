from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Προσωρινά αποθηκεύουμε τα δεδομένα σε μνήμη για να δούμε τη ροή.
# Αργότερα θα το κάνουμε με πραγματική βάση Postgres στο cloud.
suppliers = []
cheques = []
supplier_id_counter = 1
cheque_id_counter = 1


@app.route("/")
def index():
    return redirect(url_for("list_cheques"))


@app.route("/suppliers", methods=["GET", "POST"])
def list_suppliers():
    global supplier_id_counter

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

            suppliers.append({
                "id": supplier_id_counter,
                "name": name,
                "balance": balance_val,
                "email": email,
                "phone": phone,
            })
            supplier_id_counter += 1

        return redirect(url_for("list_suppliers"))

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
            <td>{{ "%.2f"|format(s.balance) }}</td>
            <td>{{ s.email }}</td>
            <td>{{ s.phone }}</td>
        </tr>
        {% endfor %}
    </table>
    <p><a href="{{ url_for('list_cheques') }}">Επιταγές</a></p>
    """
    return render_template_string(html, suppliers=suppliers)

@app.route("/cheques", methods=["GET", "POST"])
def list_cheques():
    global cheque_id_counter

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
                amount_val = 0

            cheques.append({
                "id": cheque_id_counter,
                "pharmacy": pharmacy,
                "supplier_id": int(supplier_id),
                "cheque_number": cheque_number,
                "amount": amount_val,
                "issue_date": issue_date,
                "due_date": due_date,
                "employer_name": employer_name,
                "status": "OPEN",
            })
            cheque_id_counter += 1

        return redirect(url_for("list_cheques"))

    supplier_map = {s["id"]: s["name"] for s in suppliers}

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
            <td>{{ supplier_map.get(c.supplier_id, '') }}</td>
            <td>{{ c.cheque_number }}</td>
            <td>{{ c.amount }}</td>
            <td>{{ c.issue_date }}</td>
            <td>{{ c.due_date }}</td>
            <td>{{ c.employer_name }}</td>
            <td>{{ c.status }}</td>
        </tr>
        {% endfor %}
    </table>
    <p><a href="{{ url_for('list_suppliers') }}">Προμηθευτές</a></p>
    """
    return render_template_string(html, suppliers=suppliers, cheques=cheques, supplier_map=supplier_map)


if __name__ == "__main__":
    app.run(debug=True)