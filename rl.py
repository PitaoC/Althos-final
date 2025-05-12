#last working code

import customtkinter as ctk
from pymongo import MongoClient
from bson import ObjectId  # Import ObjectId for proper querying
import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkinter import filedialog

# MongoDB Connection (only once!)
try:
    connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
    client = MongoClient(connection_string)
    db = client["ADB"]
    devices_collection = db["Members"]
    reportlogs_collection = db["ReportLogs"]
except Exception as e:
    print("Error connecting to MongoDB:", e)

class rl(ctk.CTkToplevel):
    def __init__(self, parent, group_name, group_id):
        super().__init__(parent)

        self.group_name = group_name  
        self.group_id = group_id  

        self.title(f"Report logs of {self.group_name}")
        self.geometry("800x600")
        self.resizable(False, False) 
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)
        self.grab_set()

        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width // 2) - (800 // 2)
        y_position = (screen_height // 2) - (600 // 2)
        self.geometry(f"800x600+{x_position}+{y_position}")

        self.fullscreen = False 

        # Content frame
        self.container_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container_frame.pack(side="top", anchor="nw", padx=20, pady=(10, 10), fill="both", expand=True)

        self.update_treeview()

    def fetch_members(self):
        """Fetch all members belonging to a group."""
        try:
            group_id_objectid = ObjectId(self.group_id)
            members = list(devices_collection.find({"GroupID": group_id_objectid}))
            return members
        except Exception as e:
            print("Error fetching members:", e)
            return []

    def update_treeview(self):

        members = self.fetch_members()

        # Clear previous widgets
        for widget in self.container_frame.winfo_children():
            widget.destroy()

        if members:
            for record in members:
                device_frame = ctk.CTkFrame(self.container_frame)
                device_frame.pack(fill="x", padx=5, pady=5, anchor="nw")

                device_info = f"{record.get('DeviceName', '')}: ({record.get('DeviceIP', '')}) - ID: {str(record.get('_id', ''))}"
                device_info_label = ctk.CTkLabel(device_frame, text=device_info, anchor="w")
                device_info_label.pack(side="left", padx=10)

                view_button = ctk.CTkButton(device_frame, text="View", command=lambda device=record: self.view_device(device))
                view_button.pack(side="right", padx=10)

        else:
            no_data_label = ctk.CTkLabel(self.container_frame, text="No devices found in this group.", anchor="center")
            no_data_label.pack(pady=20)
        
        # Bottom frame inside container_frame
        self.bottom_frame = ctk.CTkFrame(self.container_frame, fg_color="transparent", height=50)
        self.bottom_frame.pack(side="bottom", fill="x", padx=5, pady=(10, 10))

        self.dl_all_btn = ctk.CTkButton(self.bottom_frame, text="Download All", fg_color="forestgreen", hover_color="green", command=self.download_all_logs)
        self.dl_all_btn.pack(side="right", pady=5 , padx=10)

    def view_device(self, device):
        for widget in self.container_frame.winfo_children():
            widget.destroy()

        # ===== TOP FRAME =====
        top_frame = ctk.CTkFrame(self.container_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        back_btn = ctk.CTkButton(top_frame, text="Back", command=self.update_treeview, width=80)
        back_btn.pack(side="left")

        devicename_lbl = ctk.CTkLabel(top_frame, text=f"{device.get('DeviceName', 'Unknown')}: ({device.get('DeviceIP', 'Unknown')})", font=("Arial", 14))
        devicename_lbl.pack(side="left", padx=20)

        dl_btn = ctk.CTkButton(top_frame, text="Download", fg_color="forestgreen", hover_color="green", command=lambda: self.download_logs(device))
        dl_btn.pack(side="right", padx=5)

        delete_btn = ctk.CTkButton(top_frame, text="Delete", fg_color="red", hover_color="darkred", command=lambda: self.delete_logs(device))
        delete_btn.pack(side="right", padx=5)

        # ===== CONTENT FRAME =====
        content_frame = ctk.CTkFrame(self.container_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ===== TABLE FRAME =====
        table_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(table_frame, show="headings", height=24)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")

        tree.configure(yscrollcommand=scrollbar.set)

        # Configure tree columns dynamically to fit the frame
        selected_columns = ["Timestamp", "Components", "Status", "Duration"]
        tree["columns"] = selected_columns

        for col in selected_columns:
            tree.heading(col, text=col, anchor="center")
            tree.column(col, anchor="center", stretch=True, width=100)  # Set a default width

        tree.tag_configure("even", background="#f2f2f2")
        tree.tag_configure("odd", background="#ffffff")

        def resize_columns(event):
            total_width = tree.winfo_width()
            num_columns = len(selected_columns)
            column_width = total_width // num_columns
            for col in selected_columns:
                tree.column(col, width=column_width)

        tree.bind("<Configure>", resize_columns)

        # Fetch and display all logs by default
        def fetch_all_logs():
            try:
                # Query to fetch all logs for the current device
                query = {"DeviceID": ObjectId(device.get("_id"))}
                report_logs_data = list(reportlogs_collection.find(query).sort("Timestamp", -1))

                # Clear table and insert all data
                for row in tree.get_children():
                    tree.delete(row)

                for index, record in enumerate(report_logs_data):
                    row_data = [
                        record.get("Timestamp", ""),
                        record.get("Components", ""),
                        record.get("Status", ""),
                        f"{record.get('DurationSeconds', 0)} seconds"
                    ]
                    if index % 2 == 0:
                        tree.insert("", "end", values=row_data, tags=("even",))
                    else:
                        tree.insert("", "end", values=row_data, tags=("odd",))

            except Exception as e:
                print("Error fetching all logs:", e)

        # Load all logs by default
        fetch_all_logs()

        # ===== STATUS FRAME =====
        status_frame = tk.Frame(self.container_frame, height=100, bg="white")
        status_frame.pack(fill="x", padx=10, pady=(5, 10))

        status_label = tk.Label(
            status_frame,
            text="Mapped State: \nReasoning: ",
            font=("Arial", 10),
            anchor="w",
            justify="left",
            bg="white"
        )
        status_label.pack(fill="both", expand=True, padx=10, pady=10)

        def calculate_status():
            """Calculate the mapped state and reasoning based on the most frequent emotion and activity with the longest duration."""
            try:
                # Query to fetch all logs for the current device
                query = {"DeviceID": ObjectId(device.get("_id"))}
                report_logs_data = list(reportlogs_collection.find(query))

                if not report_logs_data:
                    status_label.config(
                        text="Mapped State: No Data\nReasoning: No logs available for this device."
                    )
                    return

                # Calculate the most frequent emotion and activity with the longest duration
                emotion_counts = {}
                emotion_durations = {}
                activity_counts = {}
                activity_durations = {}

                for log in report_logs_data:
                    # Get emotion, component, and duration
                    emotion = log.get("Status", "Unknown").strip().title()
                    component = log.get("Components", "Unknown").strip().title()
                    duration = log.get("DurationSeconds", 0)

                    # Count occurrences and sum durations for emotions
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                    emotion_durations[emotion] = emotion_durations.get(emotion, 0) + duration

                    # Handle activity based on component
                    if component in ["Mouse", "Keyboard"]:
                        activity = log.get("Status", "Unknown").strip().title()  # Use Status for activity
                    else:
                        activity = component  # For other components, use the component name as activity

                    # Count occurrences and sum durations for activities
                    activity_counts[activity] = activity_counts.get(activity, 0) + 1
                    activity_durations[activity] = activity_durations.get(activity, 0) + duration

                # Find the most frequent and longest duration emotion
                most_frequent_emotion = max(emotion_counts, key=emotion_counts.get, default="Unknown")
                longest_duration_emotion = max(emotion_durations, key=emotion_durations.get, default="Unknown")

                # Find the most frequent and longest duration activity
                most_frequent_activity = max(activity_counts, key=activity_counts.get, default="Unknown")
                longest_duration_activity = max(activity_durations, key=activity_durations.get, default="Unknown")

                # Use the most frequent emotion and the longest duration activity
                selected_emotion = most_frequent_emotion
                selected_activity = longest_duration_activity

               

                # Logic mapping based on the provided table
                logic_mapping = {
                    ("Happy", "Erratic"): ("Distracted", "Positive valence + high arousal, but lack of focus."),
                    ("Happy", "Normal"): ("Engaged", "Positive emotion + steady activity leads to active involvement and focus."),
                    ("Happy", "Idle"): ("Passive / Relaxed", "Positive but low arousal; possibly disengaged but not negatively so."),
                    ("Sad", "Erratic"): ("Confused / Emotionally Distressed", "Negative valence + conflicting high arousal."),
                    ("Sad", "Normal"): ("Withdrawn", "Negative valence + neutral arousal; may appear present but emotionally withdrawn."),
                    ("Sad", "Idle"): ("Bored", "Negative emotion + inactivity leads to disengagement and lack of stimulation."),
                    ("Angry", "Erratic"): ("Frustrated", "High-arousal emotion + uncontrolled behavior results in frustration."),
                    ("Angry", "Normal"): ("Tense / Irritated", "Negative valence + controlled arousal; may be suppressing frustration."),
                    ("Angry", "Idle"): ("Resigned / Shut Down", "Negative valence + low activity; possibly gave up, emotionally overwhelmed."),
                    ("Fearful", "Erratic"): ("Panic / Overwhelmed", "High negative arousal; signals overload or distress."),
                    ("Fearful", "Normal"): ("Anxious / Vigilant", "Fearful but still functioning; indicates stress or high monitoring."),
                    ("Fearful", "Idle"): ("Anxious", "Negative emotion + inactivity increases anxiety and unease."),
                    ("Surprised", "Erratic"): ("Distracted", "High-arousal emotion + scattered behavior causes distraction."),
                    ("Surprised", "Normal"): ("Curious / Alert", "Surprise with controlled activity = curiosity, increased focus."),
                    ("Surprised", "Idle"): ("Distracted / Startled", "Surprise + inactivity may reflect a temporary freeze."),
                    ("Neutral", "Erratic"): ("Restless / Unsettled", "No emotion but erratic behavior = discomfort or cognitive overload."),
                    ("Neutral", "Normal"): ("Calm / Stable / Focused", "Balanced affect + stable behavior suggests content engagement."),
                    ("Neutral", "Idle"): ("Disengaged", "No emotional cues, low activity; likely mentally elsewhere."),
                }

                # Check if the pair exists in the mapping
                if (selected_emotion, selected_activity) not in logic_mapping:
                    print(f"Unmapped pair: ({selected_emotion}, {selected_activity})")

                mapped_state, reasoning = logic_mapping.get(
                    (selected_emotion, selected_activity),
                    ("Unknown", "No mapping available.")
                )

                # Update the status label
                status_label.config(
                    text=f"Mapped State: {mapped_state}\nReasoning: {reasoning}"
                )

            except Exception as e:
                print("Error calculating status:", e)
                status_label.config(
                    text="Mapped State: Error\nReasoning: Unable to calculate status."
                )

            # Schedule the next update
            self.after(1000, calculate_status)  # Update every 1 second

        # Start live status updates
        calculate_status()

    def download_logs(self, device):

        try:
            device_id = device.get("_id")
            device_name = device.get("DeviceName", "UnknownDevice")
            device_ip = device.get("DeviceIP", "UnknownIP")
            
            if not isinstance(device_id, ObjectId):
                device_id = ObjectId(device_id)

            report_logs_data = list(reportlogs_collection.find({"DeviceID": device_id}))
            
            if not report_logs_data:

                noreportlogs = ctk.CTkToplevel(self)
                noreportlogs.title("Confirm Delete")
                noreportlogs.geometry("500x140")
                noreportlogs.resizable(False, False)
                noreportlogs.grab_set()
                noreportlogs.attributes("-topmost", True)
                noreportlogs.attributes("-toolwindow", True)

                # Center window on screen
                window_width = 500
                window_height = 140
                screen_width = noreportlogs.winfo_screenwidth()
                screen_height = noreportlogs.winfo_screenheight()
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                noreportlogs.geometry(f"{window_width}x{window_height}+{x}+{y}")

                label = ctk.CTkLabel(noreportlogs, text=f"No report logs found for this device:'{device_name} ({device_ip})'", font=("Arial", 16))
                label.pack(pady=20)

                ok_button = ctk.CTkButton(noreportlogs, text="OK", command=noreportlogs.destroy)
                ok_button.pack(pady=10)

                return
            
       
            relevant_columns = ["Timestamp", "DeviceName", "DeviceIP", "Components", "Status", "DurationSeconds"]
            filtered_data = []

            for record in report_logs_data:
                filtered_record = {key: record.get(key, "") for key in relevant_columns}
                filtered_data.append(filtered_record)
    
            df = pd.DataFrame(filtered_data)
            
            default_file_name = f"{device_name}_reportlogs.xlsx"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=default_file_name 
            )
            
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                print(f"Report logs saved to {file_path}")
        
        except Exception as e:
            print(f"Error during download: {e}")

    def delete_logs(self, device):
        """Delete all logs for the specified device."""
        try:
            device_id = device.get("_id")
            device_name = device.get("DeviceName", "UnknownDevice")
            device_ip = device.get("DeviceIP", "UnknownIP")

            if not isinstance(device_id, ObjectId):
                device_id = ObjectId(device_id)

            # Confirm deletion with the user
            confirm_delete = ctk.CTkToplevel(self)
            confirm_delete.title("Confirm Delete")
            confirm_delete.geometry("500x140")
            confirm_delete.resizable(False, False)
            confirm_delete.grab_set()
            confirm_delete.attributes("-topmost", True)
            confirm_delete.attributes("-toolwindow", True)

            # Center window on screen
            window_width = 500
            window_height = 140
            screen_width = confirm_delete.winfo_screenwidth()
            screen_height = confirm_delete.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            confirm_delete.geometry(f"{window_width}x{window_height}+{x}+{y}")

            label = ctk.CTkLabel(confirm_delete, text=f"Are you sure you want to delete all logs for '{device_name} ({device_ip})'?", font=("Arial", 16))
            label.pack(pady=20)

            def confirm_action():
                # Delete logs from the database
                reportlogs_collection.delete_many({"DeviceID": device_id})
                print(f"All logs for device '{device_name} ({device_ip})' have been deleted.")
                confirm_delete.destroy()

            confirm_button = ctk.CTkButton(confirm_delete, text="Yes", fg_color="red", hover_color="darkred", command=confirm_action)
            confirm_button.pack(side="left", padx=20, pady=10)

            cancel_button = ctk.CTkButton(confirm_delete, text="No", command=confirm_delete.destroy)
            cancel_button.pack(side="right", padx=20, pady=10)

        except Exception as e:
            print(f"Error during deletion: {e}")

    def download_all_logs(self):
        try:
            # Fetch all report logs for the specified groupID
            group_id_objectid = ObjectId(self.group_id)
            report_logs_data = list(reportlogs_collection.find({"GroupID": group_id_objectid}))

            if not report_logs_data:
                # Create a pop-up window to notify the user that no logs were found
                noreportlogs = ctk.CTkToplevel(self)
                noreportlogs.title("No Logs Found")
                noreportlogs.geometry("500x140")
                noreportlogs.resizable(False, False)
                noreportlogs.grab_set()
                noreportlogs.attributes("-topmost", True)
                noreportlogs.attributes("-toolwindow", True)

                # Center window on screen
                window_width = 500
                window_height = 140
                screen_width = noreportlogs.winfo_screenwidth()
                screen_height = noreportlogs.winfo_screenheight()
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                noreportlogs.geometry(f"{window_width}x{window_height}+{x}+{y}")

                label = ctk.CTkLabel(noreportlogs, text=f"No report logs found for the group '{self.group_name}'", font=("Arial", 16))
                label.pack(pady=20)

                ok_button = ctk.CTkButton(noreportlogs, text="OK", command=noreportlogs.destroy)
                ok_button.pack(pady=10)

                return

            # Filter relevant columns and prepare data for saving
            relevant_columns = ["Timestamp", "DeviceName", "DeviceIP", "Components", "Status", "DurationSeconds"]
            filtered_data = []

            for record in report_logs_data:
                filtered_record = {key: record.get(key, "") for key in relevant_columns}
                filtered_data.append(filtered_record)

            # Create a DataFrame from the filtered data
            df = pd.DataFrame(filtered_data)

            # Prompt the user to select a file location for saving the logs
            default_file_name = f"{self.group_name}_reportlogs.xlsx"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=default_file_name
            )

            if file_path:
                df.to_excel(file_path, index=False, engine="openpyxl")
                print(f"Group report logs saved to {file_path}")

        except Exception as e:
            print(f"Error during download: {e}")