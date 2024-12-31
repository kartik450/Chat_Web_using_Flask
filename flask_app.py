from flask import Flask, request, render_template, Response, jsonify, session
from firebase import firebase
import time
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required to use sessions
# https://cell-83b7b-default-rtdb.firebaseio.com/
# Firebase setup
firebase_url = "https://chat45544-default-rtdb.firebaseio.com/"  # Your Firebase URL
firebase_app = firebase.FirebaseApplication(firebase_url, None)

# Global variable to store chat key
chat_key = ""

# Home route to render login page
@app.route("/")
def home():
    return render_template("login.html", message2="")

# User login details
@app.route("/user_details", methods=["GET", "POST"])
def user_details():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Load user data from err.json
        def load_err(file_path: str) -> dict:
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {"questions": []}
                save_err(file_path, data)
            return data

        def save_err(file_path: str, data: dict):
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)

        def find_best_match(user_question: str, questions: list[str]) -> str | None:
            from difflib import get_close_matches
            matches = get_close_matches(user_question, questions, n=1, cutoff=1.0)
            return matches[0] if matches else None

        def get_answer_for_question(question: str, err: dict) -> str | None:
            for q in err["questions"]:
                if q["question"] == question:
                    return q["answer"]

        def chat_bot():
            err = load_err('err.json')
            user_input = username
            question_list = [q["question"] for q in err["questions"]]
            best_match = find_best_match(user_input, question_list)

            if best_match:
                answer = get_answer_for_question(best_match, err)
                return answer
            else:
                return "Incorrect username"

        ans = chat_bot()
        if ans == "Incorrect username":
            return render_template("login.html", message2="Incorrect username")
        elif password != ans:
            return render_template("login.html", message2="Incorrect password")

        # Store username in session
        session['username'] = username
        return render_template('sender.html')


@app.route('/forget')
def forget():
    return render_template('forget.html')

@app.route('/new_pass',methods=["GET","POST"])
def new_pass():
    if request.method=="POST":
        user_name=request.form['forget_u']
        new_passw=request.form['new_password']
        new_passw_con=request.form['new_password_con']
        if new_passw!=new_passw_con:
            return render_template('forget.html',error_m="Password not matched")
        #import json

        def load_err(file_path: str) -> dict:
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {"questions": []}
                save_err(file_path, data)
            return data

        def save_err(file_path: str, data: dict):
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)

        def find_best_match(user_question: str, questions: list[str]) -> str | None:
            from difflib import get_close_matches
            matches = get_close_matches(user_question, questions, n=1, cutoff=1.0)
            return matches[0] if matches else None

        def get_answer_for_question(question: str, err: dict) -> str | None:
            for q in err["questions"]:
                if q["question"] == question:
                    return q["answer"]

        def update_answer(file_path: str, question: str, new_answer: str):
            err = load_err(file_path)
            for q in err["questions"]:
                if q["question"] == question:
                    q["answer"] = new_answer
                    save_err(file_path, err)


    # If question not found, add it
            #err["questions"].append({"question": question, "answer": new_answer})
            #save_err(file_path, err)
            #return "New question and answer added."

        def chat_bot():
            err = load_err('err.json')
            user_input = user_name # Assuming you want to check the username
            question_list = [q["question"] for q in err["questions"]]
            best_match = find_best_match(user_input, question_list)

            if best_match:
                answer = get_answer_for_question(best_match, err)
                #print(f"Current answer: {answer}")

                #update = input("Do you want to update the answer? (yes/no): ").lower()
                #if update == "yes":
                new_answer = new_passw
                result = update_answer('err.json', best_match, new_answer)
                print(result)
                return "1.1"

            else:
                return "-1.0"

        ss=chat_bot()
        if ss=="1.1":
           return render_template("login.html",message2="Password changed successfully..")
        else:
            return render_template("forget.html",error_m="Incorrect username.")


# User registration
@app.route("/register")
def register():
    return render_template('register.html')

@app.route('/registration', methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        username1 = request.form['username']
        password1 = request.form['password']

        def load_err(file_path: str) -> dict:
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                data = {"questions": []}
                save_err(file_path, data)
            return data

        def save_err(file_path: str, data: dict):
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)

        def find_best_match(user_question: str, questions: list[str]) -> str | None:
            from difflib import get_close_matches
            matches = get_close_matches(user_question, questions, n=1, cutoff=1.0)
            return matches[0] if matches else None

        def chat_bot():
            err = load_err('err.json')
            user_input = username1
            question_list = [q["question"] for q in err["questions"]]
            best_match = find_best_match(user_input, question_list)

            if best_match:
                return "incorrect"
            else:
                new_answer = password1
                err["questions"].append({"question": user_input, "answer": new_answer})
                save_err('err.json', err)
                return "correct"

        ans = chat_bot()
        if ans == "incorrect":
            return render_template('register.html', messa="Username already exists...")
        return render_template('login.html', message2="Registered")

# Messages storage (real-time streaming) using a key
messages1 = {}  # To store messages with their keys

@app.route('/test1')
def index():
    return render_template('test1.html')

# Save the key that the user enters
@app.route("/data", methods=["GET", "POST"])
def data():
    global chat_key
    if request.method == "POST":
        chat_key = request.form['key']  # User inputs the chat key
        return render_template('test1.html')

# Stream messages based on the chat key
@app.route('/stream')
def stream():
    last_sent_key = None  # Keep track of the last message key sent to the client

    def event_stream():
        nonlocal last_sent_key  # To access and update the outer variable

        while True:
            # Fetch messages only for the specific chat key
            if chat_key:
                messages = firebase_app.get(f'/messages/{chat_key}', '')  # Get all messages under the specific chat key
            else:
                messages = {}

            new_messages = {}

            if messages:
                # Sort messages by their Firebase keys (timestamps) to ensure correct order
                sorted_messages = sorted(messages.items(), key=lambda x: x[0])

                for message_id, message_data in sorted_messages:
                    message = message_data['message']

                    # Check if the message is new and hasn't been sent yet
                    if last_sent_key is None or message_id > last_sent_key:
                        new_messages[message_id] = message
                        last_sent_key = message_id  # Update the last sent message key

            if new_messages:
                for message_key, message in new_messages.items():
                    yield f'data: {message}\n\n'  # Send new messages to the client

            time.sleep(0.0001)  # Reduce polling interval for faster updates

    return Response(event_stream(), mimetype="text/event-stream")

# Send messages with the chat key
@app.route('/send', methods=['POST'])
def send():
    global chat_key
    message = request.form.get('message')
    if message and chat_key:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = session.get('username', 'Anonymous')  # Get the username from session
        firebase_app.post(f'/messages/{chat_key}', {'message': f"{username} : {message}"})  # Store message under chat key
    return ('', 204)

# Fetch messages for polling
@app.route('/messages', methods=['GET'])
def get_messages():
    global chat_key
    if chat_key:
        messages = firebase_app.get(f'/messages/{chat_key}', '')  # Get all messages under the specific chat key
    else:
        messages = {}

    response_messages = []
    if messages:
        # Sort messages by their Firebase keys (timestamps) to ensure correct order
        sorted_messages = sorted(messages.items(), key=lambda x: x[0])
        for message_id, message_data in sorted_messages:
            response_messages.append({'id': message_id, 'message': message_data['message']})

    return jsonify({"messages": response_messages})

if __name__ == "__main__":
    app.run(debug=True, port=5200)
