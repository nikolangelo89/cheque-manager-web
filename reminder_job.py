import os
from urllib.parse import urlparse
from datetime import date, timedelta
import pg8000
import smtplib
from email.message import EmailMessage


DATABASE_URL = os.environ.get("DATABASE_URL")
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
RECIPIENTS = os.environ.get("REMINDER_RECIPIENTS", "")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    parsed = urlparse(DATABASE_URL)
    user = parsed.username
    password = parsed.password
    database = parsed.path.lstrip("/")
    host = parsed.hostname
    port = parsed.port or 5432

    return pg8000.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def get_open_cheques_due_within(days=3):
    today = date.today()
    limit_date = today + timedelta(days=days)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            pharmacy,
            cheque_number,
            amount,
            due_date,
            employer_name
        FROM cheques
        WHERE status = 'OPEN'
          AND (reminder_sent IS FALSE OR reminder_sent IS NULL)
          AND due_date BETWEEN %s AND %s
        ORDER BY due_date, id;
        """,
        (today, limit_date),
    )

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cheques = [{cols[i]: row[i] for i in range(len(cols))} for row in rows]

    cur.close()
    conn.close()
    return cheques


def mark_cheques_reminded(cheque_ids):
    if not cheque_ids:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cheques SET reminder_sent = TRUE WHERE id = ANY(%s);",
        (cheque_ids,),
    )
    conn.commit()
    cur.close()
    conn.close()


def send_email(cheque, recipients):
    if not recipients:
        return

    due_date = cheque["due_date"]
    today = date.today()
    days_left = (due_date - today).days

    subject = f"Υπενθύμιση επιταγής – λήξη σε {days_left} ημέρες"
    body = f"""
Καλησπέρα σας,

Η επιταγή με τα παρακάτω στοιχεία λήγει σε {days_left} ημέρες:

Φαρμακείο: {cheque['pharmacy']}
Αρ. Επιταγής: {cheque.get('cheque_number') or '-'}
Ποσό: {cheque['amount']} €
Ημ/νία Λήξης: {cheque['due_date']}
Εργοδότης (όνομα): {cheque.get('employer_name') or '-'}

Παρακαλώ φροντίστε, αν χρειάζεται, για την ύπαρξη των απαραίτητων χρημάτων ώστε να καλυφθεί η επιταγή.

Με εκτίμηση,
Σύστημα υπενθύμισης επιταγών
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def main():
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD):
        raise RuntimeError("SMTP configuration is missing")

    recipients = [r.strip() for r in RECIPIENTS.split(",") if r.strip()]
    if not recipients:
        raise RuntimeError("REMINDER_RECIPIENTS is empty")

    cheques = get_open_cheques_due_within(days=3)

    if not cheques:
        print("No cheques due within 3 days.")
        return

    sent_ids = []
    for ch in cheques:
        try:
            send_email(ch, recipients)
            sent_ids.append(ch["id"])
            print(f"Sent reminder for cheque id={ch['id']}")
        except Exception as e:
            print(f"Failed to send email for cheque id={ch['id']}: {e}")

    if sent_ids:
        mark_cheques_reminded(sent_ids)
        print(f"Marked {len(sent_ids)} cheques as reminded.")


if __name__ == "__main__":
    main()