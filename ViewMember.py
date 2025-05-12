import customtkinter as ctk
from pymongo import MongoClient
from bson import ObjectId
from PIL import Image, ImageTk
import socket
import threading
import io
import tkinter as tk
import cv2
import numpy as np

class ViewMember(ctk.CTkToplevel):
    def __init__(self, parent, device, device_ip, group_id, group_name):
        super().__init__(parent)

        self.device_id = device.get("_id", "Unknown ID")
        device_name = device.get("DeviceName", "Unnamed Device")
        self.ip = device.get("DeviceIP", "Unknown Device IP")
        self.group_id = group_id  
        self.group_name = group_name
        self.is_running = True

        self.title("View Device")
        self.geometry("1450x650")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)
        self.grab_set()
        self.title(f"{self.ip}")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width // 2) - (1450 // 2)
        y_position = (screen_height // 2) - (650 // 2)
        self.geometry(f"1450x650+{x_position}+{y_position}")

        self.fullscreen = False 
        
        # Main container
        container_frame = ctk.CTkFrame(self, fg_color="transparent")
        container_frame.pack(side="left", anchor="nw", padx=20, pady=20)

        #keyboard & mouse label (KML) frame
        kml_frame = ctk.CTkFrame(container_frame,fg_color="transparent")
        kml_frame.pack(side="top", pady=10)

        #keyboard & mouse (KM) frame
        km_frame = ctk.CTkFrame(container_frame,fg_color="transparent")
        km_frame.pack(side="top", pady=2)

        # keyboard label
        kb_lbl = ctk.CTkLabel(kml_frame, text="Keyboard Status:", font=("Arial", 14, "bold"), width=700, height=30, fg_color="transparent", corner_radius=10)
        kb_lbl.pack(side="left", expand=True,pady=2)

        # keyboard label
        mouse_lbl = ctk.CTkLabel(kml_frame, text="Mouse Status:", font=("Arial", 14, "bold"), width=700, height=30, fg_color="transparent", corner_radius=10)
        mouse_lbl.pack(side="left", expand=True,pady=2)

        # keyboard Status
        self.kbstatus_lbl = ctk.CTkLabel(km_frame, text=" ", font=("Arial", 14, "bold"), width=680, height=30, fg_color="green", corner_radius=10)
        self.kbstatus_lbl.pack(side="left", padx=10)

        # Mouse Status
        self.mousestatus_lbl = ctk.CTkLabel(km_frame, text=" ", font=("Arial", 14, "bold"), width=680, height=30, fg_color="green", corner_radius=10)
        self.mousestatus_lbl.pack(side="left", padx=10)

        #Screen & Camera (SC) frame
        sc_frame = ctk.CTkFrame(container_frame,fg_color="transparent")
        sc_frame.pack(side="top", pady=6)

        #Screen Frame (Fixed Size)
        self.screenframe = ctk.CTkFrame(sc_frame, width=700, height=400, corner_radius=10)
        self.screenframe.pack_propagate(False)  # Prevent resizing
        self.screenframe.pack(side="left", pady=10)

        #Label for Displaying Screen (Fixed Size)
        self.screen_label = ctk.CTkLabel(self.screenframe, text=" ", font=("Arial", 14, "bold"), width=700, height=400, fg_color="gray")
        self.screen_label.pack(fill="both", expand=True)

        self.cameraframe = ctk.CTkFrame(sc_frame, width=700, height=400, corner_radius=10)
        self.cameraframe.pack_propagate(False)
        self.cameraframe.pack(side="left", padx=10)

        self.camera_label = ctk.CTkLabel(self.cameraframe, text=" ", font=("Arial", 14, "bold"), width=700, height=400, fg_color="gray")
        self.camera_label.pack(fill="both", expand=True)

        # Start receiving screen data in a separate thread
        threading.Thread(target=self.receive_screen, daemon=True).start()
        threading.Thread(target=self.receive_keyboard_status, daemon=True).start()
        threading.Thread(target=self.receive_mouse_status, daemon=True).start()
        threading.Thread(target=self.receive_camera, daemon=True).start()

        self.prev_kb_status = None
        self.prev_mouse_status = None

# ==========================================================================================
#   SCREEN RECEIVER
# ==========================================================================================
    def receive_screen(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                try:
                    client_socket.connect((self.ip, 5000))
                 
                    while True:
                        try:
                            length = client_socket.recv(4)
                            if len(length) < 4:
                                print("Connection closed by server.")
                                break
                            data_length = int.from_bytes(length, 'big')

                            data = b""
                            while len(data) < data_length:
                                packet = client_socket.recv(data_length - len(data))
                                if not packet:
                                    print("Connection lost.")
                                    break
                                data += packet

                            if data:
                                image = Image.open(io.BytesIO(data))
                                image = image.resize((700, 400), Image.LANCZOS)
                                photo = ImageTk.PhotoImage(image)
                                self.screen_label.configure(image=photo)
                                self.screen_label.image = photo
                        except Exception as e:
                            print(f"Error receiving screen: {e}")
                            break

                except socket.timeout:
                    print(f"Connection to {self.ip} timed out. Device may be offline.")
                    self.Screen_offline_state()

                except ConnectionRefusedError:
                    print(f"Connection to {self.ip} was refused. Device is offline.")
                    self.Screen_offline_state()

        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.Screen_offline_state()

    def Screen_offline_state(self):
        self.screen_label.configure(text="Screen is offline", image=None, fg_color="black")


# ==========================================================================================
#   KEYBOARD STATUS RECEIVER
# ==========================================================================================
    def receive_keyboard_status(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(30)
                client_socket.connect((self.ip, 5002))

                while self.is_running:
                    try:
                        data = client_socket.recv(1024).decode("utf-8").strip().lower()
                        if not data:
                            print("[Keyboard] Connection closed by client.")
                            break

                        if not self.kbstatus_lbl.winfo_exists():
                            break

                        if data == "erratic":
                            color = "red"
                        elif data == "normal":
                            color = "green"
                        elif data == "idle":
                            color = "gray"
                        else:
                            color = "orange"

                        self.kbstatus_lbl.configure(text=f"{data.upper()}", fg_color=color)

                    except Exception as e:
                        print(f"[Keyboard] Error receiving data: {e}")
                        if self.kbstatus_lbl.winfo_exists():
                            self.kbstatus_lbl.configure(text="ERROR", fg_color="red")
                        break

        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            print(f"[Keyboard] Cannot connect to {self.ip}: {e}")
            if self.kbstatus_lbl.winfo_exists():
                self.kbstatus_lbl.configure(text="OFFLINE", fg_color="black")

# ==========================================================================================
#   MOUSE STATUS RECEIVER
# ==========================================================================================
    def receive_mouse_status(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(30)
                client_socket.connect((self.ip, 5003))

                while True:
                    try:
                        data = client_socket.recv(1024).decode("utf-8").strip().lower()
                        if not data:
                            print("[Mouse] Connection closed by client.")
                            break

                        if data == "erratic":
                            color = "red"
                        elif data == "normal":
                            color = "green"
                        elif data == "idle":
                            color = "gray"
                        else:
                            color = "orange"  # Unknown status

                        try:
                            self.mousestatus_lbl.configure(text=f"{data.upper()}", fg_color=color)
                        except tk.TclError:
                            break  # Exit the loop and end the thread

                    except Exception as e:
                        print(f"[Mouse] Error receiving data: {e}")
                        try:
                            self.mousestatus_lbl.configure(text="ERROR", fg_color="red")
                        except tk.TclError:
                            break
                        break

        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            print(f"[Mouse] Cannot connect to {self.ip}: {e}")
            try:
                self.mousestatus_lbl.configure(text="OFFLINE", fg_color="black")
            except tk.TclError:
                print("[Mouse] Widget no longer exists.")

# ==========================================================================================
#   CAMERA RECEIVER
# ==========================================================================================
    def receive_camera(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                try:
                    client_socket.connect((self.ip, 5004)) 
                    print(f"[Camera] Connected to {self.ip}")

                    while True:
                        try:                
                            length = client_socket.recv(4)
                            if len(length) < 4:
                                print("[Camera] Connection closed by client.")
                                break
                            data_length = int.from_bytes(length, 'big')

                            # Receive the frame data
                            data = b""
                            while len(data) < data_length:
                                packet = client_socket.recv(data_length - len(data))
                                if not packet:
                                    print("[Camera] Connection lost.")
                                    break
                                data += packet

                            if data:
                                # Decode the frame and display it
                                np_data = np.frombuffer(data, np.uint8)
                                frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

                                if frame is not None:
                                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    img = Image.fromarray(frame)
                                    img = img.resize((700, 400), Image.LANCZOS)
                                    photo = ImageTk.PhotoImage(img)

                                    self.camera_label.configure(image=photo)
                                    self.camera_label.image = photo
                        except Exception as e:
                            print(f"[Camera] Error receiving data: {e}")
                            break

                except socket.timeout:
                    print(f"[Camera] Connection to {self.ip} timed out. Device may be offline.")
                    self.Camera_offline_state()

                except ConnectionRefusedError:
                    print(f"[Camera] Connection to {self.ip} was refused. Device is offline.")
                    self.Camera_offline_state()

        except Exception as e:
            print(f"[Camera] Error connecting to server: {e}")
            self.Camera_offline_state()

    def Camera_offline_state(self):
        self.camera_label.configure(text="Camera is offline", image=None, fg_color="black")