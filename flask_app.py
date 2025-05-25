from flask import Flask, request, render_template, Response, jsonify, session
import time
import json
from datetime import datetime
import random
import smtplib
from email.mime.text import MIMEText
import logging  # For fallback logging
from firebase import firebase

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for sessions

# Firebase setup
firebase_url = "https://chat45544-default-rtdb.firebaseio.com/"
firebase_app = firebase.FirebaseApplication(firebase_url, None)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "virtualbot45@gmail.com"  # Replace with your email
SMTP_PASSWORD = "trmm rzml afgy khsd"  # Replace with your app-specific password

# Configure logging as a fallback
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        # Fallback to logging if SMTP fails (e.g., on PythonAnywhere free tier)
        logger.error(f"SMTP failed: {str(e)}. Logging OTP instead.")
        logger.info(f"Email to {to_email} - Subject: {subject} - Body: {body}")
        raise  # Re-raise the exception to handle it in the route

def generate_otp():
    return str(random.randint(100000, 999999))

# JSON file handling (unchanged)
def load_err(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"questions": []}
        save_err(file_path, data)
    return data

def save_err(file_path: str, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: list[str]) -> str | None:
    from difflib import get_close_matches
    matches = get_close_matches(user_question, questions, n=1, cutoff=1.0)
    return matches[0] if matches else None

# Routes
@app.route("/")
def home():
    return render_template("login.html", message2="")

@app.route("/user_details", methods=["POST"])
def user_details():
    username = request.form['username']
    password = request.form['password']
    err = load_err('err.json')
    questions = [q["question"] for q in err["questions"]]
    best_match = find_best_match(username, questions)

    if not best_match:
        return render_template("login.html", message2="Incorrect username")
    
    for q in err["questions"]:
        if q["question"] == best_match:
            if q["answer"] == password:
                session['username'] = username
                return render_template('sender.html')
            else:
                return render_template("login.html", message2="Incorrect password")

@app.route("/register")
def register():
    return render_template('register.html', messa="")

@app.route('/registration', methods=["POST"])
def registration():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    err = load_err('err.json')
    questions = [q["question"] for q in err["questions"]]
    if find_best_match(username, questions):
        return render_template('register.html', messa="Username already exists...")
    
    otp = generate_otp()
    session['registration_data'] = {'username': username, 'email': email, 'password': password, 'otp': otp}
    try:
        send_email(email, "Your Registration OTP", f"Your OTP is: {otp}")
        return render_template('verify_otp.html', messa="OTP sent to your email.")
    except Exception as e:
        # Fallback message for free tier
        return render_template('verify_otp.html', messa=f"Failed to send OTP via email (SMTP blocked). Check server logs for OTP: {otp}")

@app.route('/verify_otp', methods=["POST"])
def verify_otp():
    user_otp = request.form['otp']
    reg_data = session.get('registration_data', {})
    
    if user_otp == reg_data.get('otp'):
        err = load_err('err.json')
        err["questions"].append({"question": reg_data['username'], "answer": reg_data['password'], "email": reg_data['email']})
        save_err('err.json', err)
        session.pop('registration_data', None)
        return render_template('login.html', message2="Registered successfully!")
    return render_template('verify_otp.html', messa="Invalid OTP. Try again.")

@app.route('/forget')
def forget():
    return render_template('forget.html', error_m="")

@app.route('/send_forget_otp', methods=["POST"])
def send_forget_otp():
    username = request.form['forget_u']
    err = load_err('err.json')
    questions = [q["question"] for q in err["questions"]]
    best_match = find_best_match(username, questions)
    
    if not best_match:
        return render_template('forget.html', error_m="Incorrect username.")
    
    for q in err["questions"]:
        if q["question"] == best_match:
            email = q.get("email")
            if not email:
                return render_template('forget.html', error_m="No email associated with this account.")
            
            otp = generate_otp()
            session['forget_data'] = {'username': username, 'otp': otp}
            try:
                send_email(email, "Your Password Reset OTP", f"Your OTP is: {otp}")
                return render_template('verify_forget_otp.html', username=username, error_m="OTP sent to your email.")
            except Exception as e:
                return render_template('verify_forget_otp.html', username=username, error_m=f"Failed to send OTP via email (SMTP blocked). Check server logs for OTP: {otp}")
    
    return render_template('forget.html', error_m="Something went wrong.")

@app.route('/new_pass', methods=["POST"])
def new_pass():
    username = request.form['forget_u']
    user_otp = request.form['otp']
    new_passw = request.form['new_password']
    new_passw_con = request.form['new_password_con']
    forget_data = session.get('forget_data', {})
    
    if user_otp != forget_data.get('otp'):
        return render_template('verify_forget_otp.html', username=username, error_m="Invalid OTP.")
    
    if new_passw != new_passw_con:
        return render_template('verify_forget_otp.html', username=username, error_m="Passwords do not match.")
    
    err = load_err('err.json')
    for q in err["questions"]:
        if q["question"] == username:
            q["answer"] = new_passw
            save_err('err.json', err)
            session.pop('forget_data', None)
            return render_template("login.html", message2="Password changed successfully.")
    
    return render_template('forget.html', error_m="Something went wrong.")

# Remaining routes (unchanged)
chat_key = ""

@app.route('/test1')
def index():
    return render_template('test1.html')

@app.route("/data", methods=["POST"])
def data():
    global chat_key
    chat_key = request.form['key']
    return render_template('test1.html')

@app.route('/stream')
def stream():
    last_sent_key = None
    def event_stream():
        nonlocal last_sent_key
        while True:
            if chat_key:
                messages = firebase_app.get(f'/messages/{chat_key}', '')
            else:
                messages = {}
            new_messages = {}
            if messages:
                sorted_messages = sorted(messages.items(), key=lambda x: x[0])
                for message_id, message_data in sorted_messages:
                    message = message_data['message']
                    if last_sent_key is None or message_id > last_sent_key:
                        new_messages[message_id] = message
                        last_sent_key = message_id
            if new_messages:
                for message_key, message in new_messages.items():
                    yield f'data: {message}\n\n'
            time.sleep(0.0001)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/send', methods=['POST'])
def send():
    global chat_key
    message = request.form.get('message')
    if message and chat_key:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = session.get('username', 'Anonymous')
        firebase_app.post(f'/messages/{chat_key}', {'message': f"{username} : {message}"})
    return ('', 204)

@app.route('/messages', methods=['GET'])
def get_messages():
    global chat_key
    if chat_key:
        messages = firebase_app.get(f'/messages/{chat_key}', '')
    else:
        messages = {}
    response_messages = []
    if messages:
        sorted_messages = sorted(messages.items(), key=lambda x: x[0])
        for message_id, message_data in sorted_messages:
            response_messages.append({'id': message_id, 'message': message_data['message']})
    return jsonify({"messages": response_messages})

if __name__ == "__main__":
    app.run(debug=True, port=5200)