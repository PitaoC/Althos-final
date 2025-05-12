
#LAST CODE WORKING
import customtkinter as ctk
from pymongo import MongoClient
from bson import ObjectId
import AddMember
import ViewMember
import time
from PIL import Image, ImageTk
import socket
import threading
import io
import os
import tkinter as tk
import rl

# ==========================================================================================
#   DATABASE CONNECTION
# ==========================================================================================
try:
    connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
    client = MongoClient(connection_string)
    db = client["ADB"]
    devices_collection = db["Members"]
    ReportLogs = db["ReportLogs"]
except Exception as e:
    print("Error connecting to Members MongoDB:", e)

class ViewGroup(ctk.CTkFrame):
    def __init__(self, parent, switch_page, group_id="Unknown", group_name="Group Pages"):
        super().__init__(parent)
        self.switch_page = switch_page
        self.group_id = group_id
        self.group_name = group_name
        self.devices = []
        self.kbstatus_dots = {}
        self.mousestatus_dots = {}
        self.panel_padding = 10
        self.panel_width = 200
        self.is_running = True 
        self.device_canvas_map = {}

        # Top Frame
        self.top_frame = ctk.CTkFrame(self, height=50)
        self.top_frame.pack(fill="x", side="top", padx=10, pady=2)

        # Back Button
        self.back_button = ctk.CTkButton(
            self.top_frame, text="← Back", width=80,
            command=self.backtodashboard
        )
        self.back_button.pack(side="left", padx=10, pady=10)

        # Report logs Button
        self.rl_btn = ctk.CTkButton(
            self.top_frame, text="Report Logs", width=80,command=self.open_reportlogs
        )
        self.rl_btn.pack(side="right", padx=(0, 10), pady=10)

        # Refresh Button
        self.refresh_button = ctk.CTkButton(
            self.top_frame, text="⟳ Refresh", width=80,
            command=self.refresh_devices
        )
        self.refresh_button.pack(side="right", padx=(0, 10), pady=10)

        # Page Label
        self.label = ctk.CTkLabel(self.top_frame, text=self.group_name, font=("Arial", 20, "bold"))
        self.label.pack(side="left", padx=10, pady=10)

        # Content Frame
        self.content_frame = ctk.CTkScrollableFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=2)

        self.bind("<Configure>", self.on_resize)
        self.display_devices()

    def backtodashboard(self): # Back to Dashboard and stop all threads
        #self.is_running = False
        #print("stoped receiving data")
        self.switch_page("Dashboard")  
# ==========================================================================================
#   DISPLAY THE DATA FROM THE DATABASE
# ==========================================================================================
    def display_devices(self):
        self.device_canvas_map = {}

        for widget in self.content_frame.winfo_children():
            widget.destroy()

        max_columns = self.calculate_columns()
        if max_columns < 1:
            return

        plus_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        plus_panel.grid(row=0, column=0, padx=self.panel_padding, pady=10, sticky="n")

        button_width = max(200, (self.winfo_width() - 40) // max_columns - (self.panel_padding * 2))

        plus_btn = ctk.CTkButton(plus_panel, text="+", width=button_width, height=150,font=("Arial", 24), command=self.show_addmem)
        plus_btn.pack(pady=(10, 5), expand=True)

        plus_lbl = ctk.CTkLabel(plus_panel, text="Add Device", font=("Arial", 14))
        plus_lbl.pack(pady=(0, 10))

        for i, device in enumerate(self.devices):
            device_id = device.get("_id", "Unknown ID")
            device_ip = device.get("DeviceIP", "Unnamed Device IP")
            device_name = device.get("DeviceName", "Unnamed Device")

            sub_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            sub_panel.grid(row=(i + 1) // max_columns, column=(i + 1) % max_columns, padx=self.panel_padding, pady=10, sticky="n")

            canvas = tk.Canvas(sub_panel, width=button_width + 4, height=154, highlightthickness=0,bg="gray")
            canvas.pack_propagate(False)
            canvas.pack(pady=10)

            # Add the canvas to the map
            self.device_canvas_map[device_ip] = canvas

            screenframe = ctk.CTkFrame(canvas, width=button_width, height=150, corner_radius=10)
            screenframe.pack_propagate(False)
            canvas.create_window(2, 2, anchor="nw", window=screenframe)

            screen_label = ctk.CTkLabel(screenframe, text=" ", font=("Arial", 14, "bold"), width=button_width - 4, height=150 - 4, fg_color="lightgray")
            screen_label.pack(fill="both", expand=True)
            screen_label.bind("<Button-1>", lambda event, dev=device: self.open_member(dev))

            #Start receiving the screen
            threading.Thread(target=self.receive_screen, args=(device, screen_label), daemon=True).start()
            #Start receiving the emotion data
            threading.Thread(target=self.receive_emotion_data, args=(device_ip, device_id, device_name), daemon=True).start()
            
            # Bottom Label Frame (device label + overflow menu)
            label_frame = ctk.CTkFrame(sub_panel, fg_color="transparent")
            label_frame.pack(pady=(0, 10), fill="x")

            # Configure columns with appropriate weights
            label_frame.grid_columnconfigure(0, weight=0)
            label_frame.grid_columnconfigure(1, weight=1)
            label_frame.grid_columnconfigure(2, weight=0) 

            # Keyboard status dot
            kbstatus_dot = ctk.CTkLabel(label_frame, text="●", font=("Arial", 14), text_color="black")
            kbstatus_dot.grid(row=0, column=0, sticky="w", padx=(0, 5))
            self.kbstatus_dots[device_id] = kbstatus_dot
            threading.Thread(target=self.receive_keyboard_status, args=(device_id, device_ip, kbstatus_dot, device_name), daemon=True).start()

            # Mouse status dot
            mousestatus_dot = ctk.CTkLabel(label_frame, text="●", font=("Arial", 14), text_color="black")
            mousestatus_dot.grid(row=0, column=0, sticky="e", padx=(20, 5), columnspan=1)
            self.mousestatus_dots[device_id] = mousestatus_dot
            threading.Thread(target=self.receive_mouse_status, args=(device_id, device_ip, mousestatus_dot, device_name), daemon=True).start()

            # Device name label (centered)
            device_lbl = ctk.CTkLabel(label_frame, text=device_name, font=("Arial", 14))
            device_lbl.grid(row=0, column=1, sticky="nsew")

            # Overflow button (right-aligned)
            overflow_btn = ctk.CTkButton(label_frame, text="⋮", width=30, fg_color="transparent", text_color="white", command=lambda dev=device: self.show_overflow_menu(dev))
            overflow_btn.grid(row=0, column=2, sticky="e")

        for col in range(max_columns):
            self.content_frame.grid_columnconfigure(col, weight=1)

        self.content_frame.update_idletasks()

    def show_overflow_menu(self, device):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit", command=lambda: self.update_device(device))
        menu.add_command(label="Delete", command=lambda: self.delete_device(device))

        x, y = self.winfo_pointerx(), self.winfo_pointery()
        menu.tk_popup(x, y)

# ==========================================================================================
#   UPDATE DEVICE
# ==========================================================================================

    def update_device(self, device):
        # Fetch the current device details from the database
        device_id = device["_id"]
        current_device_ip = device.get("DeviceIP", "")
        current_device_name = device.get("DeviceName", "")

        # Create a new top-level window for updating device details
        update_window = ctk.CTkToplevel(self)
        update_window.title("Update Device Info")
        update_window.resizable(False, False)
        update_window.attributes("-topmost", True)
        update_window.attributes("-toolwindow", True)
        update_window.grab_set()

        width, height = 500, 250
        update_window.geometry(f"{width}x{height}")

        # Center the window on the screen
        screen_width = update_window.winfo_screenwidth()
        screen_height = update_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        update_window.geometry(f"{width}x{height}+{x}+{y}")

        # Labels for the fields
        deviceip_lbl = ctk.CTkLabel(update_window, text="Device IP:", anchor="w")
        deviceip_lbl.pack(fill="x", padx=55, pady=(6, 2))

        device_ip_entry = ctk.CTkEntry(update_window,  width=400, height=35)
        device_ip_entry.insert(0, current_device_ip)
        device_ip_entry.pack(pady=5)

        devicename_lbl = ctk.CTkLabel(update_window, text="Device Name:", anchor="w")
        devicename_lbl.pack(fill="x", padx=55, pady=(2, 2))

        device_name_entry = ctk.CTkEntry(update_window,  width=400, height=35)
        device_name_entry.insert(0, current_device_name)
        device_name_entry.pack(pady=5)

        def save_update():
            new_device_ip = device_ip_entry.get().strip()
            new_device_name = device_name_entry.get().strip()

            # Validate and update the device details if necessary
            if new_device_ip and new_device_name:
                try:
                    # Update the device document in MongoDB
                    devices_collection.update_one(
                        {"_id": device_id},
                        {"$set": {"DeviceIP": new_device_ip, "DeviceName": new_device_name}}
                    )
                    print(f"Device updated: IP '{current_device_ip}' to '{new_device_ip}', Name '{current_device_name}' to '{new_device_name}'")
                    update_window.destroy()
                    self.refresh_devices()  # Refresh the devices list after update
                except Exception as e:
                    print("Error updating device details:", e)

        # Button frame to hold Save and Cancel side by side
        button_frame = ctk.CTkFrame(update_window, fg_color="transparent")
        button_frame.pack(pady=15)

        save_btn = ctk.CTkButton(button_frame, text="Save", fg_color="forestgreen", hover_color="green",width=190, command=save_update)
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", fg_color="darkred", hover_color="red", width=190, command=update_window.destroy)
        cancel_btn.pack(side="left", padx=10)

# ==========================================================================================
#   DELETE DEVICE
# ==========================================================================================
    def delete_device(self, device):
        device_ip = device.get("DeviceIP", "Unnamed Device IP")
        device_name = device.get("DeviceName", "Unnamed Device")

        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Delete")
        confirm.geometry("500x140")
        confirm.resizable(False, False)
        confirm.grab_set()
        confirm.attributes("-topmost", True)
        confirm.attributes("-toolwindow", True)

        # Center window on screen
        window_width = 500
        window_height = 140
        screen_width = confirm.winfo_screenwidth()
        screen_height = confirm.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        confirm.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Confirmation message
        label = ctk.CTkLabel(confirm, text=f"Are you sure you want to delete '{device_name} ({device_ip})'", font=("Arial", 16))
        label.pack(pady=20)

        def confirm_delete():
            try:
                devices_collection.delete_one({"_id": device["_id"]})
                print("Deleted device:", device["_id"])
                confirm.destroy()
                self.refresh_devices()
            except Exception as e:
                print("Error deleting device:", e)
                confirm.destroy()

        # Buttons side-by-side
        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack(pady=10)

        yes_btn = ctk.CTkButton(btn_frame, text="Yes", fg_color="darkred", hover_color="red", command=confirm_delete)
        yes_btn.pack(side="left", padx=10)

        no_btn = ctk.CTkButton(btn_frame, text="No", command=confirm.destroy)
        no_btn.pack(side="left", padx=10)

# ==========================================================================================
#   RESIZE HANDLER
# ==========================================================================================
    def on_resize(self, event=None):
        self.display_devices()

    def calculate_columns(self):
        available_width = self.winfo_width()
        if available_width <= 1:
            return 3
        return max(1, (available_width - 40) // (self.panel_width + self.panel_padding * 2))

# ==========================================================================================
#   SET GROUP DATA
# ==========================================================================================
    def set_group_data(self, group_id, group_name):
        self.group_id = group_id
        self.group_name = group_name
        self.label.configure(text=self.group_name)

        try:
            query_filter = {"GroupID": ObjectId(self.group_id)} if ObjectId.is_valid(self.group_id) else {"GroupID": self.group_id}
            self.devices = list(devices_collection.find(query_filter))
            if not self.devices:
                print("No devices found for GroupID:", self.group_id)
        except Exception as e:
            print("Error fetching devices:", e)

        self.display_devices()

# ==========================================================================================
#   SCREEN RECEIVER
# ==========================================================================================
    def receive_screen(self, device, screen_label):
        device_ip = device.get("DeviceIP", "Unnamed Device IP")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                try:
                    client_socket.connect((device_ip, 5001))

                    while self.is_running:
                        try:
                            length = client_socket.recv(4)
                            if len(length) < 4:
                                print(f"Connection closed by server ({device_ip}).")
                                break
                            data_length = int.from_bytes(length, 'big')

                            data = b""
                            while len(data) < data_length:
                                packet = client_socket.recv(data_length - len(data))
                                if not packet:
                                    print(f"Connection lost ({device_ip}).")
                                    break
                                data += packet

                            if data:
                                image = Image.open(io.BytesIO(data))
                                frame_width = screen_label.winfo_width()
                                frame_height = screen_label.winfo_height()
                                image = image.resize((frame_width, frame_height), Image.LANCZOS)
                                photo = ImageTk.PhotoImage(image)

                                screen_label.configure(image=photo, text="")
                                screen_label.image = photo

                        except Exception as e:
                            print(f"Error receiving screen from {device_ip}: {e}")
                            break
                except socket.timeout:
                    print(f"Connection to {device_ip} timed out.")
                    self.set_offline_state(screen_label)
                except ConnectionRefusedError:
                    print(f"Connection to {device_ip} was refused.")
                    self.set_offline_state(screen_label)
        except Exception as e:
            print(f"Error connecting to {device_ip}: {e}")
            self.set_offline_state(screen_label)

    def set_offline_state(self, screen_label):
        screen_label.configure(text="Screen Offline", image=None, fg_color="gray", font=("Arial", 16, "bold"))

# ==========================================================================================
#   KEYBOARD RECEIVER
# ==========================================================================================
    def receive_keyboard_status(self, device_id, device_ip, kbstatus_dot, device_name):
        last_status = None
        last_status_time = time.time()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                client_socket.connect((device_ip, 6002))
                print(f"[Keyboard] Connected to {device_ip}")

                while self.is_running:
                    try:
                        data = client_socket.recv(1024).decode("utf-8").strip().lower()
                        if not data:
                            print(f"[Keyboard] Connection closed by client: {device_ip}")
                            break

                        # Print and save the data logs
                        if data != last_status and last_status is not None:
                            current_time = time.time()
                            duration = current_time - last_status_time
                            self.print_status_log(
                                self.group_id, device_id, "keyboard", last_status, duration, device_name, device_ip
                            )

                            # Update the last status and time
                            last_status_time = current_time

                        # Update the current status
                        last_status = data

                        # Decide color based on status
                        if data == "erratic":
                            color = "red"
                        elif data == "normal":
                            color = "green"
                        elif data == "idle":
                            color = "gray"
                        else:
                            color = "orange"  # Unknown status

                        # Update the kbstatus_dot color
                        kbstatus_dot.configure(text_color=color)

                    except Exception as e:
                        print(f"[Keyboard] Error receiving data from {device_ip}: {e}")
                        kbstatus_dot.configure(text_color="red") 
                        break

        except (ConnectionRefusedError, socket.timeout) as e:
            print(f"[Keyboard] Cannot connect to {device_ip}: {e}")
            kbstatus_dot.configure(text_color="black") 

# ==========================================================================================
#   MOUSE RECEIVER
# ==========================================================================================
    def receive_mouse_status(self, device_id, device_ip, mousestatus_dot, device_name):
        last_status = None
        last_status_time = time.time()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                client_socket.connect((device_ip, 6003))
                print(f"[Mouse] Connected to {device_ip}")

                while self.is_running:
                    try:
                        data = client_socket.recv(1024).decode("utf-8").strip().lower()
                        if not data:
                            print(f"[Mouse] Connection closed by client: {device_ip}")
                            break

                        # Print and save the data logs
                        if data != last_status and last_status is not None:
                            current_time = time.time()
                            duration = current_time - last_status_time
                            self.print_status_log(
                                self.group_id, device_id, "mouse", last_status, duration, device_name, device_ip
                            )

                            # Update the last status and time
                            last_status_time = current_time

                        # Update the current status
                        last_status = data

                        # Change dot color based on status
                        if data == "erratic":
                            color = "red"
                        elif data == "normal":
                            color = "green"
                        elif data == "idle":
                            color = "gray"
                        else:
                            color = "orange"  # Unknown status

                        mousestatus_dot.configure(text_color=color)

                    except Exception as e:
                        print(f"[Mouse] Error receiving data: {e}")
                        mousestatus_dot.configure(text_color="red")
                        break

        except (ConnectionRefusedError, socket.timeout) as e:
            print(f"[Mouse] Cannot connect to {device_ip}: {e}")
            mousestatus_dot.configure(text_color="black")

# ==========================================================================================
#   FUNCTION TO CHANGE THE COLOR OF THE BORDER BASED ON THE USER EMOTION
# ==========================================================================================
    def update_border_color(self, canvas, color):
        canvas.configure(bg=color)

    def receive_emotion_data(self, device_ip, device_id,device_name):
        last_emotion = None
        last_emotion_time = time.time()

        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.settimeout(15)
                    try:
                        client_socket.connect((device_ip, 5005))
                        print(f"[Emotion] Connected to {device_ip}")

                        while self.is_running:
                            try:
                                header = client_socket.recv(4)
                                if len(header) < 4:
                                    break
                                data_size = int.from_bytes(header, "big")

                                data = b""
                                while len(data) < data_size:
                                    packet = client_socket.recv(data_size - len(data))
                                    if not packet:
                                        break
                                    data += packet

                                if data:
                                    emotion_data = data.decode("utf-8").strip()
                                    emotion_state, color = emotion_data.split(":")
                                    #print(f"[Emotion] Received from {self.group_id, device_id}, {device_ip, device_name} {emotion_data}")

                                    # Save emotion log to the database
                                    if emotion_state != last_emotion and last_emotion is not None:
                                        current_time = time.time()
                                        duration = current_time - last_emotion_time
                                        self.print_status_log(
                                            self.group_id, device_id, "camera", last_emotion, duration, device_name, device_ip
                                        )
                                        last_emotion_time = current_time

                                    # Update the last emotion state
                                    last_emotion = emotion_state

                                    # Update the border color for the corresponding canvas
                                    if device_ip in self.device_canvas_map:
                                        canvas = self.device_canvas_map[device_ip]
                                        self.update_border_color(canvas, color)

                            except socket.timeout:
                                break
                    except (socket.timeout, ConnectionRefusedError):
                        time.sleep(5)
            except Exception:
                time.sleep(5)

# ==========================================================================================
#   PRINT STATUS LOG AND SAVE TO DATABASE
# ==========================================================================================
    def print_status_log(self, group_id, device_id, device_type, status, duration, device_name, device_ip):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            group_id = ObjectId(group_id)
        except Exception as e:
            print(f"Error converting group_id to ObjectId: {e}")
            return

        # Log entry to print
        log_entry = {
            "GroupID": group_id,
            "DeviceID": device_id,
            "Timestamp": timestamp,
            "DeviceName": device_name,
            "DeviceIP": device_ip,
            "Components": device_type.capitalize(),
            "Status": status.capitalize(),
            "DurationSeconds": round(duration, 2)
        }
        
        # Save the log entry to the MongoDB database
        try:
            ReportLogs.insert_one(log_entry)
            
        except Exception as e:
            print(f"Error saving log entry to database: {e}")

# ==========================================================================================
#   REFRESH DISPLAY DATA
# ==========================================================================================
    def refresh_devices(self):
        try:
            query_filter = {"GroupID": ObjectId(self.group_id)} if ObjectId.is_valid(self.group_id) else {"GroupID": self.group_id}
            self.devices = list(devices_collection.find(query_filter))
            print("Devices refreshed:", self.devices)
        except Exception as e:
            print("Error refreshing devices:", e)
        self.display_devices()

# ==========================================================================================
#   SHOW ADD MEMBER FORM
# ==========================================================================================
    def show_addmem(self):
        self.ShowAddMem = AddMember.AddMember(self, self.group_id, self.group_name)
        self.ShowAddMem.focus()

# ==========================================================================================
#   OPEN THE MEMBER FORM
# ==========================================================================================
    def open_member(self, device):
        device_ip = device.get("DeviceIP", "Unknown IP")
        device_name = device.get("DeviceName", "Unnamed Device")
        self.openmem = ViewMember.ViewMember(self, device, device_ip,self.group_id, self.group_name)
        self.openmem.focus()

# ==========================================================================================
#   OPEN THE REPOR LOGS FORM
# ==========================================================================================
    def open_reportlogs(self):
        self.openmem = rl.rl(self,self.group_name,self.group_id)
        self.openmem.focus()



