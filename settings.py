import customtkinter as ctk
import sys
from pymongo import MongoClient
from bson import ObjectId
from tkinter import messagebox  # For confirmation dialog
import subprocess

class Settings(ctk.CTk):
    def __init__(self, acc_id, username):
        super().__init__()

        self.acc_id = acc_id  # Store AccID
        self.username = username  # Store username
        
        # MongoDB Connection
        self.accounts_collection = None
        self.account_data = None
        try:
            connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
            client = MongoClient(connection_string)
            db = client["ADB"]
            self.accounts_collection = db["Accounts"]
            print("Connected to Accounts MongoDB Atlas!")

            # Convert acc_id to ObjectId and query the database
            self.account_data = self.accounts_collection.find_one({"_id": ObjectId(self.acc_id)})
            if self.account_data:
                print(f"Account data found: {self.account_data}")
            else:
                print(f"No account found with acc_id: {self.acc_id}")

        except Exception as e:
            print("Error connecting to MongoDB:", e)

        self.title("Account Settings")
        self.geometry("400x400")
        self.minsize(500, 400)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)
        self.grab_set()

        # Center the window on the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width // 2) - (500 // 2)
        y_position = (screen_height // 2) - (400 // 2)
        self.geometry(f"500x400+{x_position}+{y_position}")

        print(f"AccID: {self.acc_id}, Username: {self.username}")  # Debugging info

        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Label for email
        email_text = self.account_data["email"] if self.account_data and "email" in self.account_data else "Email not found"
        self.email_label = ctk.CTkLabel(self.main_frame, text=f"Email: {email_text}", anchor="w")
        self.email_label.pack(fill="x", pady=(0, 10))

        # Username textbox
        username_text = self.account_data["username"] if self.account_data and "username" in self.account_data else self.username
        self.username_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Username", state="normal")
        self.username_entry.insert(0, username_text)
        self.username_entry.configure(state="disabled")
        self.username_entry.pack(fill="x", pady=5)

        # Password textbox
        self.password_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Password", show="*", state="disabled")
        self.password_entry.pack(fill="x", pady=5)

        # Confirm password textbox
        self.confirm_password_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Confirm Password", show="*", state="disabled")
        self.confirm_password_entry.pack(fill="x", pady=5)

        # Checkbox for showing password
        self.show_password_var = ctk.BooleanVar()
        self.show_password_checkbox = ctk.CTkCheckBox(self.main_frame, text="Show Password", variable=self.show_password_var, command=self.toggle_password_visibility)
        self.show_password_checkbox.pack(anchor="w", pady=10)

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=10)

        self.edit_button = ctk.CTkButton(self.button_frame, text="Edit", command=self.edit_action)
        self.edit_button.pack(side="left", expand=True, fill="x", padx=5)

        # Apply Changes button (initially hidden)
        self.apply_button = ctk.CTkButton(self.button_frame, text="Apply Changes", command=self.apply_changes_action)
        self.apply_button.pack(side="left", expand=True, fill="x", padx=5)
        self.apply_button.pack_forget()  # Hide the Apply Changes button initially

        self.cancel_button = ctk.CTkButton(self.button_frame, text="Cancel", command=self.cancel_action)
        self.cancel_button.pack(side="right", expand=True, fill="x", padx=5)

        self.delete_button = ctk.CTkButton(self.main_frame, text="Delete Account", fg_color="red", hover_color="#ff6666", command=self.delete_account_action)
        self.delete_button.pack(fill="x", pady=10)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.configure(show="")
            self.confirm_password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")
            self.confirm_password_entry.configure(show="*")

    def edit_action(self):
        # Enable textboxes
        self.username_entry.configure(state="normal")
        self.password_entry.configure(state="normal")
        self.confirm_password_entry.configure(state="normal")

        # Hide the Edit button and show the Apply Changes button
        self.edit_button.pack_forget()
        self.apply_button.pack(side="left", expand=True, fill="x", padx=5)

    def apply_changes_action(self):
        # Get updated username and password
        new_username = self.username_entry.get()
        new_password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Validate inputs
        if new_password != confirm_password:
            print("Error", "Passwords do not match!")
            return
        
        if not new_username or not new_password:
            print("Error", "Username and Password cannot be empty!")
            return

        try:
            # Update the account in the database
            self.accounts_collection.update_one(
                {"_id": ObjectId(self.acc_id)},
                {"$set": {"username": new_username, "password": new_password}}
            )

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply changes: {e}")

        # Disable textboxes and reset UI state
        self.cancel_action()

    def cancel_action(self):
        print("Cancel button pressed")
        # Reset the UI state
        self.username_entry.configure(state="disabled")
        self.password_entry.configure(state="disabled")
        self.confirm_password_entry.configure(state="disabled")

        # Hide the Apply Changes button and show the Edit button
        self.apply_button.pack_forget()
        self.edit_button.pack(side="left", expand=True, fill="x", padx=5)

        self.destroy()

    def delete_account_action(self):
        # Confirm deletion
        confirm = messagebox.askyesno("Delete Account", "Are you sure you want to delete this account?")
        if not confirm:
            return

        try:
            # Delete the account from the database
            self.accounts_collection.delete_one({"_id": ObjectId(self.acc_id)})
            messagebox.showinfo("Success", "Account deleted successfully!")
            self.destroy()  # Close the settings window
            subprocess.Popen(["python", "LoginForm.py"])  # Launch login.py
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {e}")


if __name__ == "__main__":
    # Retrieve acc_id and username from command-line arguments
    acc_id = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    username = sys.argv[2] if len(sys.argv) > 2 else "Guest"

    app = Settings(acc_id, username)
    app.mainloop()