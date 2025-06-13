import os
import json
import secrets
import string
import smtplib
import time
import webbrowser
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import qrcode
from PIL import Image, ImageTk
import netifaces
import tkinter as tk

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['STATIC_FOLDER'] = 'static'

# Email configuration
SENDER_EMAIL = "alphatechmiit@gmail.com"
EMAIL_PASSWORD = "dvkahcgxtbaocnxc"

# Load or initialize users from JSON file
DATA_FILE = 'data/users.json'
ORDERS_FILE = 'data/orders.json'

if not os.path.exists('data'):
    os.makedirs('data')

def load_data(file_path, default_data):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if file_path == ORDERS_FILE:
                # Validate each order has required keys
                valid_orders = []
                for order in data.get("orders", []):
                    if isinstance(order, dict) and all(key in order for key in ["email", "timestamp", "passcode", "status"]):
                        valid_orders.append(order)
                    else:
                        print(f"⚠ Invalid order found in {file_path}: {order}")
                data["orders"] = valid_orders
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"⚠ Warning: {file_path} is missing or corrupted. Resetting data...")
        with open(file_path, 'w') as f:
            json.dump(default_data, f)
        return default_data

# Load users
users_data = load_data(DATA_FILE, {"users": {}, "passcodes": {}})
users = users_data["users"]
passcodes = users_data["passcodes"]

# Function to save data to JSON
def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f)

# 🆕 Migrate old user format to new format
for email, user_data in list(users.items()):
    if not isinstance(user_data, dict):
        users[email] = {"password": user_data, "is_admin": False}
save_data(DATA_FILE, {"users": users, "passcodes": passcodes})

# Load orders
orders_data = load_data(ORDERS_FILE, {"orders": []})
orders = orders_data["orders"]


# Function to Generate Secure Passcode
def generate_passcode(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))

# Function to Send Passcode via Email using smtplib
def send_passcode_email(email, passcode):
    subject = "Your Delivery Passcode"
    body = f"Your passcode is: {passcode}"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
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
                    if ip.startswith('192.168.138'):
                        return ip
        except:
            continue
    print("Warning: Hotspot IP not found. Using 127.0.0.1 as fallback.")
    return "127.0.0.1"

# Function to generate and display QR code
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

# Home Page
@app.route('/')
def index():
    return render_template("index.html")

# Signup API
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
    except:
        if request.form:
            data = request.form.to_dict()
        else:
            return jsonify({"error": "Invalid request format"}), 415

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    if email in users:
        return jsonify({"error": "Email already registered"}), 400

    users[email] = {"password": password, "is_admin": False}
    save_data(DATA_FILE, {"users": users, "passcodes": passcodes})
    return jsonify({"message": "Signup successful!"})

# Login API
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
    except:
        if request.form:
            data = request.form.to_dict()
        else:
            return jsonify({"error": "Invalid request format"}), 415

    email = data.get("email")
    password = data.get("password")

    user = users.get(email)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    stored_password = user["password"] if isinstance(user, dict) else user
    if stored_password != password:
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
    send_passcode_email(email, passcode)  # ✅ Already using the logged-in user's email

    order = {
        "email": email,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passcode": passcode,
        "status": "Pending"
    }
    orders.append(order)
    save_data(ORDERS_FILE, {"orders": orders})

    return jsonify({"message": "Delivery started! Passcode sent via email.", "passcode": passcode})

@app.route('/verify-passcode', methods=['POST'])
def verify_passcode():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data or "passcode" not in data:
        return jsonify({"error": "Missing passcode in request"}), 400

    email = session.get("email")
    entered_passcode = data.get("passcode")

    if not email:
        return jsonify({"error": "User not logged in"}), 401

    if email not in passcodes:
        return jsonify({"error": "No passcode generated for this user"}), 401

    if passcodes[email] != entered_passcode:
        return jsonify({"error": "Invalid passcode!"}), 401

    order_found = False
    for order in orders:
        if not isinstance(order, dict) or "email" not in order:
            print(f"⚠ Skipping invalid order: {order}")
            continue
        if order["email"] == email and order["passcode"] == entered_passcode:
            order["status"] = "Completed"
            order_found = True
            break

    if not order_found:
        return jsonify({"error": "No matching order found with this passcode"}), 404

    del passcodes[email]
    save_data(ORDERS_FILE, {"orders": orders})
    save_data(DATA_FILE, {"users": users, "passcodes": passcodes})  # Fixed to save full users_data
    return jsonify({"message": "Correct passcode! Delivery completed!"})

# Admin Login Page
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            data = request.json
        except:
            if request.form:
                data = request.form.to_dict()
            else:
                return jsonify({"error": "Invalid request format"}), 415

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required!"}), 400

        user = users.get(email)
        if not user:
            return jsonify({"error": "Invalid admin credentials"}), 401

        stored_password = user["password"] if isinstance(user, dict) else user
        is_admin = user.get("is_admin", False) if isinstance(user, dict) else False

        if stored_password == password and is_admin:
            session["admin_email"] = email
            return jsonify({"message": "Admin login successful!"})
        return jsonify({"error": "Invalid admin credentials"}), 401

    return render_template("admin_login.html")

# Admin Page (Updated)
@app.route('/admin')
def admin():
    if "admin_email" not in session:
        return redirect(url_for('admin_login'))
    
    return render_template("admin.html", orders=orders)

# Admin Logout (Updated)
@app.route('/admin/logout')
def admin_logout():
    session.pop("admin_email", None)
    return redirect(url_for('index'))  # Redirect to admin login page

# Get Orders for Admin (Dynamic Fetch)
@app.route('/admin/get-orders', methods=['GET'])
def get_orders():
    if "admin_email" not in session:
        return jsonify({"error": "Admin not logged in"}), 401
    valid_orders = [
        order for order in orders
        if isinstance(order, dict) and all(k in order for k in ["email", "timestamp", "passcode", "status"])
    ]
    print(f"DEBUG: Returning orders: {valid_orders}")
    return jsonify(valid_orders)

# Clear Completed Deliveries (Updated)
@app.route('/admin/clear-completed', methods=['POST'])
def clear_completed():
    if "admin_email" not in session:
        return jsonify({"error": "Admin not logged in"}), 401
    global orders
    orders = [order for order in orders if order["status"] != "Completed"]
    save_data(ORDERS_FILE, {"orders": orders})
    return jsonify({"message": "Completed deliveries cleared!"})

if __name__ == '__main__':
    print(f"Starting Flask app on host 0.0.0.0 and port 5000...")
    webbrowser.open("http://192.168.1.5:5000")
    server_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(3)
    generate_and_display_qr()
    server_thread.join()