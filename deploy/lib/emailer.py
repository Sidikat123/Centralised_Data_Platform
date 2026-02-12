import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import streamlit as st


def send_inquiry_email(*, name: str, email: str, phone: str, message: str):
    host = st.secrets["SMTP_HOST"]
    port = int(st.secrets["SMTP_PORT"])
    user = st.secrets["SMTP_USER"]
    pwd = st.secrets["SMTP_PASS"]
    to_email = st.secrets["ALERT_TO_EMAIL"]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = f"New Inquiry | AlloyTower | {stamp}"

    body = f"""New inquiry submitted

Name: {name}
Email: {email}
Phone: {phone or "—"}

Message:
{message}
"""

    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to_email
    msg["Subject"] = subject

    # ✅ This makes "Reply" go to the user's email in most email clients
    msg["Reply-To"] = email

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.sendmail(user, [to_email], msg.as_string())
