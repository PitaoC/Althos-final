import customtkinter as ctk
from pymongo import MongoClient
from bson import ObjectId

class AddGroup(ctk.CTkToplevel):
    def __init__(self, parent, AccID, username):
        super().__init__(parent)

        self.parent = parent  
        self.AccID = AccID
        self.username = username

        # Database connection
        try:
            connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
            self.client = MongoClient(connection_string)
            self.db = self.client["ADB"]
            self.groups_collection = self.db["Groups"]  
            print("Connected to Groups MongoDB Atlas in AddGroup!")
        except Exception as e:
            print("Error connecting to MongoDB:", e)

        self.title("Add Group")
        self.geometry("500x200")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)
        self.grab_set()

        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width // 2) - (500 // 2)
        y_position = (screen_height // 2) - (200 // 2)
        self.geometry(f"500x200+{x_position}+{y_position}")

        # UI Elements
        message_lbl = ctk.CTkLabel(self, text="Add Group", font=("Arial", 18))
        message_lbl.pack(pady=15)

        self.gname_txtb = ctk.CTkEntry(self, placeholder_text="Name", width=400, height=35)
        self.gname_txtb.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        add_btn = ctk.CTkButton(btn_frame, text="Add", width=190, command=self.add_data)
        add_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", width=190, fg_color="darkred", hover_color="red", command=self.close_window)
        cancel_btn.pack(side="left", padx=10)

    def add_data(self):
        """Add group data to the database and refresh dashboard."""
        group_name = self.gname_txtb.get().strip()

        if not group_name:
            print("Group Name cannot be empty!")
            return

        group_data = {
            "GroupName": group_name,
            "CreatedBy": ObjectId(self.AccID)  # Store the user's ID
        }

        try:
            result = self.groups_collection.insert_one(group_data)
            print(f"Group added successfully with ID: {result.inserted_id}")

            # Call the refresh method in the parent dashboard
            if self.parent:
                self.parent.fetch_groups()
                self.parent.display_groups()

            self.destroy()  # Close the window after adding
        except Exception as e:
            print(f"Error inserting group data: {e}")

    def close_window(self):
        """Closes the AddGroup window."""
        self.destroy()
