import customtkinter as ctk
from pymongo import MongoClient
from bson import ObjectId

class AddMember(ctk.CTkToplevel):
    def __init__(self, parent, group_id, group_name):
        super().__init__(parent)

        self.parent = parent  
        self.group_id = group_id
        self.group_name = group_name  

        # Database connection
        try:
            connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
            self.client = MongoClient(connection_string)
            self.db = self.client["ADB"]
            self.members_collection = self.db["Members"]  
            print("Connected to Members MongoDB Atlas in AddGroup!")
        except Exception as e:
            print("Error connecting to MongoDB:", e)

        self.title("Add Member")
        self.geometry("500x250")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)
        self.grab_set()

        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width // 2) - (500 // 2)
        y_position = (screen_height // 2) - (250 // 2)
        self.geometry(f"500x250+{x_position}+{y_position}")

        # UI Elements
        message_lbl = ctk.CTkLabel(self, text="Add Member", font=("Arial", 18))
        message_lbl.pack(pady=15)

        self.dname_txtb = ctk.CTkEntry(self, placeholder_text="Device Name", width=400, height=35)
        self.dname_txtb.pack(pady=5)

        self.ip_txtb = ctk.CTkEntry(self, placeholder_text="Device IP Address", width=400, height=35)
        self.ip_txtb.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        add_btn = ctk.CTkButton(btn_frame, text="Add", width=190, command=self.add_data)
        add_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", width=190, fg_color="darkred", hover_color="red", command=self.close_window)
        cancel_btn.pack(side="left", padx=10)

    def add_data(self):
        """Add member data to the database and refresh dashboard."""
        devicename = self.dname_txtb.get().strip()
        deviceip = self.ip_txtb.get().strip()

        if not devicename:
            print("Device Name cannot be empty!")
            return
        
        if not deviceip:
            print("Device IP cannot be empty!")
            return

        member_data = {
            "DeviceName": devicename,
            "DeviceIP": deviceip,
            "GroupID": ObjectId(self.group_id)
        }

        try:
            result = self.members_collection.insert_one(member_data)
            print(f"Member added successfully with ID: {result.inserted_id}")

            self.destroy()  # Close the window after adding

            # Call the refresh method in the parent dashboard
            if self.parent:
                self.parent.set_group_data(self.group_id, self.group_name)
                self.parent.display_devices()

            
        except Exception as e:
            print(f"Error inserting group data: {e}")

    def close_window(self):
        """Closes the AddGroup window."""
        self.destroy()