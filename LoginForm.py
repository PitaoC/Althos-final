import customtkinter as ctk
from tkinter import messagebox
from pymongo import MongoClient
from PIL import Image
import subprocess
import random
import smtplib
import threading
import time

# --- MongoDB Connection ---
try:
    connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
    client = MongoClient(connection_string)
    db = client["ADB"]
    accounts_collection = db["Accounts"]
    print("Connected to Accounts MongoDB Atlas!")
except Exception as e:
    print("Error connecting to MongoDB:", e)

# ==========================================================================================
#   OTP Configuration
# ==========================================================================================
SENDER_EMAIL = "alt.plus.f4.2024@gmail.com"
SENDER_APP_PASSWORD = "ffryzvzybqsnswqy"
current_otp = None
otp_timer_running = False

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email):
    global current_otp
    current_otp = generate_otp()
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)

        subject = "Your OTP Code"
        message = f"Your OTP code is: {current_otp}\n\nThis OTP is valid for 2 minutes."
        msg = f"Subject: {subject}\n\n{message}"

        server.sendmail(SENDER_EMAIL, email, msg)
        server.quit()
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")
        return False

def start_otp_timer(button):
    global otp_timer_running, current_otp
    if otp_timer_running:
        return
    otp_timer_running = True

    def countdown():
        nonlocal button
        time_left = 120
        while time_left > 0:
            button.configure(text=f"{time_left}s")
            time.sleep(1)
            time_left -= 1
        button.configure(text="Send", state="normal")
        current_otp = None
        otp_timer_running = False

    button.configure(state="disabled")
    threading.Thread(target=countdown, daemon=True).start()

# ==========================================================================================
app = ctk.CTk()
app.title("Althos")
app.geometry("1000x600")
app.resizable(False, False)

# Center the window
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
x_position = (screen_width // 2) - (1000 // 2)
y_position = (screen_height // 2) - (600 // 2)
app.geometry(f"1000x600+{x_position}+{y_position}")

main_frame = ctk.CTkFrame(app)
main_frame.pack(fill="both", expand=True)

right_frame = ctk.CTkFrame(main_frame, width=500)
right_frame.pack(side="right", fill="both", expand=True)

left_frame = ctk.CTkFrame(main_frame, width=500, fg_color="#132330")
left_frame.pack(side="left", fill="both", expand=True)

logo_path = "Logo/LOGO1.png"
logo_image = Image.open(logo_path).resize((400, 400))
logo_ctkimage = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(400, 400))

logo_lbl = ctk.CTkLabel(left_frame, image=logo_ctkimage, text="")
logo_lbl.place(relx=0.5, rely=0.5, anchor="center")


def clear_frame():
    for widget in right_frame.winfo_children():
        widget.destroy()

def showpass(entry):
    entry.configure(show="" if entry.cget("show") == "*" else "*")

# ==========================================================================================
#   Login & Sign-Up Functions
# ==========================================================================================
def login():
    email = username_txtb.get()
    password = password_txtb.get()
    user = accounts_collection.find_one({"email": email, "password": password})
    if user:
        message_lbl.configure(text="Login Successful", text_color="green")
        app.withdraw()
        AccID = str(user.get("_id", "Unknown"))
        username = user.get("username", "Unknown")
        subprocess.Popen(["python", "Main.py", AccID, username]).wait()
        app.quit()
    else:
        message_lbl.configure(text="Invalid email or password!", text_color="white")

# ==========================================================================================
#   LOGIN GUI
# ==========================================================================================
def create_login_view():
    clear_frame()
    global username_txtb, password_txtb, message_lbl

    inner_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
    inner_frame.pack(expand=True)

    ctk.CTkLabel(inner_frame, text="Login to Althos", font=("Arial", 28, "bold")).pack(pady=(5, 20))

    username_txtb = ctk.CTkEntry(inner_frame, placeholder_text="Email", width=350, height=35)
    username_txtb.pack(pady=5)

    password_txtb = ctk.CTkEntry(inner_frame, placeholder_text="Password", show="*", width=350, height=35)
    password_txtb.pack(pady=5)

    showpass_cb = ctk.CTkCheckBox(inner_frame, text="Show Password", command=lambda: showpass(password_txtb))
    showpass_cb.pack(pady=5, anchor="w")

    login_btn = ctk.CTkButton(inner_frame, text="Login", width=350, height=35, command=login)
    login_btn.pack(pady=5)

    signup_btn = ctk.CTkButton(inner_frame, text="SignUp", width=350, height=35, command=create_signup_view)
    signup_btn.pack(pady=5)

    message_lbl = ctk.CTkLabel(inner_frame, text="", font=("Arial", 14))
    message_lbl.pack(pady=5)

# ==========================================================================================
#   SIGNUP GUI
# ==========================================================================================
def create_signup_view():
    clear_frame()
    global username_txtb, password_txtb, message_lbl

    inner_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
    inner_frame.pack(expand=True)

    ctk.CTkLabel(inner_frame, text="Sign up to Althos", font=("Arial", 28, "bold")).pack(pady=(5, 20))

    username_txtb = ctk.CTkEntry(inner_frame, placeholder_text="Username", width=350, height=35)
    username_txtb.pack(pady=5)

    email_txtb = ctk.CTkEntry(inner_frame, placeholder_text="Email", width=350, height=35)
    email_txtb.pack(pady=5)

    password_txtb = ctk.CTkEntry(inner_frame, placeholder_text="Password", show="*", width=350, height=35)
    password_txtb.pack(pady=5)

    showpass_cb = ctk.CTkCheckBox(inner_frame, text="Show Password", command=lambda: showpass(password_txtb))
    showpass_cb.pack(pady=5, anchor="w")

    otp_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
    otp_frame.pack(pady=5)

    otp_txtb = ctk.CTkEntry(otp_frame, placeholder_text="OTP", width=245, height=35)
    otp_txtb.pack(side="left", padx=(0, 5))

    def send_otp_handler():
        email = email_txtb.get()
        if email:
            if send_otp(email):
                start_otp_timer(send_btn)
                message_lbl.configure(text=f"OTP sent to {email}", text_color="green")
        else:
            #messagebox.showwarning("Missing Info", "Please enter email.")
            message_lbl.configure(text="Please enter email.", text_color="white")

    send_btn = ctk.CTkButton(otp_frame, text="Send", width=100, height=35, command=send_otp_handler)
    send_btn.pack(side="left")

    def signup_with_otp():
        email = email_txtb.get()
        username = username_txtb.get()
        password = password_txtb.get()
        entered_otp = otp_txtb.get()

        if not all([email, username, password, entered_otp]):
            message_lbl.configure(text="All fields are required!", text_color="white")
            return

        if current_otp is None:
            message_lbl.configure(text="OTP expired. Request new one.", text_color="white")
        elif entered_otp == current_otp:
            existing = accounts_collection.find_one({"email": email})
            if existing:
                message_lbl.configure(text="Account already exists!", text_color="orange")
            else:
                accounts_collection.insert_one({
                    "username": username,
                    "email": email,
                    "password": password
                })
                message_lbl.configure(text="Account created!", text_color="green")
                create_login_view()
        else:
            message_lbl.configure(text="Invalid OTP!", text_color="white")

    signup_btn = ctk.CTkButton(inner_frame, text="Sign Up", width=350, height=35, command=signup_with_otp)
    signup_btn.pack(pady=5)

    cancel_btn = ctk.CTkButton(inner_frame, text="Cancel", fg_color="darkred", hover_color="red", width=350, height=35, command=create_login_view)
    cancel_btn.pack(pady=5)

    message_lbl = ctk.CTkLabel(inner_frame, text="", font=("Arial", 14))
    message_lbl.pack(pady=5)

# Run the application
create_login_view()
app.mainloop()
