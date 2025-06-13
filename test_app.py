import os
import json
import secrets
import string
import smtplib
import time
import webbrowser
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session
import qrcode
from PIL import Image
import netifaces

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['STATIC_FOLDER'] = 'static'

# Email configuration
SENDER_EMAIL = "alphatechmiit@gmail.com"
EMAIL_PASSWORD = "dvkahcgxtbaocnxc"  # Replace with your Gmail App Password
RECEIVER_EMAIL = "waiyanminmiit@gmail.com"

# Load or initialize users from JSON file
DATA_FILE = 'data/users.json'
if not os.path.exists('data'):
    os.makedirs('data')

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠ Warning: users.json is missing or corrupted. Resetting data...")
        return {"users": {}, "passcodes": {}}  # Reset on failure

data = load_data()
users = data["users"]
passcodes = data["passcodes"]


# Function to save data to JSON
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({"users": users, "passcodes": {}}, f)

# Function to Generate Secure Passcode
def generate_passcode(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))

# Function to Send Passcode via Email using smtplib
def send_passcode_email(email, passcode):
    subject = "Your Delivery Passcode"
    body = f"Your passcode is: {passcode}"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email  # ✅ Send to the logged-in user's email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())  # ✅ Send to the correct user
        print(f"✅ Passcode email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send passcode email: {e}")
    finally:
        server.quit()


# Function to find the hotspot IP
def get_hotspot_ip():
    for interface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    # Look for common hotspot IP ranges (e.g., 192.168.137.x for Windows)
                    if ip.startswith('192.168.137'):
                        return ip
        except:
            continue
    print("Warning: Hotspot IP not found. Using 127.0.0.1 as fallback.")
    return "127.0.0.1"

# Function to generate and display QR code
import tkinter as tk
from PIL import ImageTk

def generate_and_display_qr():
    QR_CODE_PATH = os.path.join("static", "qrcode.png")
    app_url = f"http://{get_hotspot_ip()}:5000"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(app_url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill='black', back_color='white')
    qr_image.save(QR_CODE_PATH)

    root = tk.Tk()
    root.title("Scan QR Code")
    img = Image.open(QR_CODE_PATH)
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo)
    label.pack()
    root.mainloop()
# def generate_and_display_qr():
#     QR_CODE_PATH = os.path.join("static", "qrcode.png")
#     app_url = f"http://{get_hotspot_ip()}:5000"
#     print(f"Generating QR code for URL: {app_url}")
#     qr = qrcode.QRCode(version=1, box_size=10, border=5)
#     qr.add_data(app_url)
#     qr.make(fit=True)
#     qr_image = qr.make_image(fill='black', back_color='white')
#     qr_image.save(QR_CODE_PATH)
#     print(f"QR code generated and saved as {os.path.abspath(QR_CODE_PATH)}")
#     try:
#         img = Image.open(QR_CODE_PATH)
#         img.show()
#         print("QR code displayed in a separate window.")
#     except Exception as e:
#         print(f"Failed to display QR code: {e}")

# Home Page (no QR code on web)
@app.route('/')
def index():
    return render_template("index.html")

# Signup API
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # ✅ Check if both email and password are provided
    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    if email in users:
        return jsonify({"error": "Email already registered"}), 400

    users[email] = password
    save_data()
    return jsonify({"message": "Signup successful!"})


# Login API
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if users.get(email) != password:
        return jsonify({"error": "Invalid credentials"}), 401

    session["email"] = email
    return jsonify({"message": "Login successful!"})

# Start Delivery API
@app.route('/start-delivery', methods=['POST'])
def start_delivery():
    email = session.get("email")
    if not email:
        return jsonify({"error": "User not logged in"}), 401

    passcode = generate_passcode()
    passcodes[email] = passcode
    send_passcode_email(email, passcode)
    return jsonify({"message": "Delivery started! Passcode sent via email.", "passcode": passcode})

# Verify Passcode API
@app.route('/verify-passcode', methods=['POST'])
def verify_passcode():
    data = request.json
    email = session.get("email")
    entered_passcode = data.get("passcode")

    if not email or email not in passcodes:
        return jsonify({"error": "User not logged in or no passcode generated"}), 401

    if passcodes[email] != entered_passcode:
        return jsonify({"error": "Invalid passcode!"}), 401

    # ✅ Delete the passcode after successful verification
    del passcodes[email]
    save_data()  # ✅ Save updated data to JSON

    return jsonify({"message": "Correct passcode! Delivery completed!"})


if __name__ == '__main__':
    print(f"Starting Flask app on host 0.0.0.0 and port 5000...")
    # Open the web interface in the default browser
    webbrowser.open("http://192.168.137.1:5000")
    # Start the Flask server in a separate thread
    server_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False))
    server_thread.daemon = True
    server_thread.start()
    # Wait a few seconds to ensure the server is running before generating QR code
    time.sleep(3)
    generate_and_display_qr()
    # Keep the main thread alive
    server_thread.join()
