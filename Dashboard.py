import customtkinter as ctk
from pymongo import MongoClient
from bson import ObjectId
import AddGroup
import ViewGroup
import tkinter as tk

# ============================== DATABASE CONNECTION ==============================
try:
    connection_string = "mongodb+srv://altplusf42024:RuVAh3aZgUbC0YLE@altf4cluster.9p2yp.mongodb.net/?retryWrites=true&w=majority&appName=ALTF4Cluster"
    client = MongoClient(connection_string)
    db = client["ADB"]
    groups_collection = db["Groups"]
except Exception as e:
    print("Error connecting to Groups MongoDB:", e)


class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, switch_page, AccID, username):
        super().__init__(parent)
        self.switch_page = switch_page
        self.accid = AccID
        self.username = username

        self.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.panel_width = 270
        self.panel_padding = 10

        self.groups = []

        self.fetch_groups()
        self.bind("<Configure>", self.on_resize)

    def fetch_groups(self):
        try:
            if ObjectId.is_valid(self.accid):
                acc_id_obj = ObjectId(self.accid)
            else:
                print("Invalid ObjectId format.")
                return

            query = {"CreatedBy": acc_id_obj}
            self.groups = list(groups_collection.find(query))

            if self.groups:
                self.display_groups()
            else:
                print(f"No groups found for CreatedBy {self.accid}")
        except Exception as e:
            print("Error fetching groups:", e)

    def display_groups(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        max_columns = self.calculate_columns()
        if max_columns < 1:
            return

        plus_panel = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        plus_panel.grid(row=0, column=0, padx=self.panel_padding, pady=10, sticky="n")

        button_width = max(200, (self.winfo_width() - 40) // max_columns - (self.panel_padding * 2))

        plus_btn = ctk.CTkButton(plus_panel, text="+", width=button_width, height=150, font=("Arial", 24), command=self.show_addgroup)
        plus_btn.pack(pady=(10, 5), expand=True)

        plus_lbl = ctk.CTkLabel(plus_panel, text="Add Group", font=("Arial", 14))
        plus_lbl.pack(pady=(0, 10))

        for i, group in enumerate(self.groups):
            group_name = group.get("GroupName", "Unnamed Group")

            sub_panel = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            sub_panel.grid(row=(i + 1) // max_columns, column=(i + 1) % max_columns,
                           padx=self.panel_padding, pady=10, sticky="n")

            group_btn = ctk.CTkButton(sub_panel, text=group_name, width=button_width, height=150, command=lambda g=group: self.open_group(g))
            group_btn.pack(pady=(10, 5), expand=True)

            label_frame = ctk.CTkFrame(sub_panel, fg_color="transparent")
            label_frame.pack(pady=(0, 10), fill="x")

            label_frame.grid_columnconfigure(0, weight=1)
            label_frame.grid_columnconfigure(1, weight=0)

            group_lbl = ctk.CTkLabel(label_frame, text=group_name, font=("Arial", 14))
            group_lbl.grid(row=0, column=0, sticky="nsew")

            overflow_btn = ctk.CTkButton(label_frame, text="⋮", width=30, fg_color="transparent", text_color="white", command=lambda dev=group: self.show_overflow_menu(dev))
            #overflow_btn.pack(side="left")
            overflow_btn.grid(row=0, column=1, sticky="e")


        for col in range(max_columns):
            self.scroll_frame.grid_columnconfigure(col, weight=1)

        self.scroll_frame.update_idletasks()

    def show_overflow_menu(self, group):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self.update_group(group))
        menu.add_command(label="Delete", command=lambda: self.delete_group(group))

        x, y = self.winfo_pointerx(), self.winfo_pointery()
        menu.tk_popup(x, y)

    def update_group(self, group):
        group_id = group["_id"]
        latest_group = groups_collection.find_one({"_id": group_id})
        current_name = latest_group.get("GroupName", "")

        update_window = ctk.CTkToplevel(self)
        update_window.title("Update Device Info")
        update_window.resizable(False, False)
        update_window.attributes("-topmost", True)
        update_window.attributes("-toolwindow", True)
        update_window.grab_set()

        width, height = 500, 200
        update_window.geometry(f"{width}x{height}")

        screen_width = update_window.winfo_screenwidth()
        screen_height = update_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        update_window.geometry(f"{width}x{height}+{x}+{y}")


        entry_label = ctk.CTkLabel(update_window, text="New Group Name:")
        entry_label.pack(pady=(20, 5))

        name_entry = ctk.CTkEntry(update_window, width=400, height=35)
        name_entry.insert(0, current_name)
        name_entry.pack(pady=5)

        def save_update():
            new_name = name_entry.get().strip()
            if new_name and new_name != current_name:
                try:
                    groups_collection.update_one(
                        {"_id": group_id},
                        {"$set": {"GroupName": new_name}}
                    )
                    print(f"Group '{current_name}' updated to '{new_name}'")
                    update_window.destroy()
                    self.fetch_groups()
                except Exception as e:
                    print("Error updating group name:", e)

        # Button frame to hold Save and Cancel side by side
        button_frame = ctk.CTkFrame(update_window, fg_color="transparent")
        button_frame.pack(pady=15)

        save_btn = ctk.CTkButton(button_frame, text="Save", fg_color="forestgreen", hover_color="green",width=190, command=save_update)
        save_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", fg_color="darkred", hover_color="red", width=190, command=update_window.destroy)
        cancel_btn.pack(side="left", padx=10)

    def delete_group(self, group):
        group_name = group.get("GroupName", "Unnamed")
        group_id = group.get("_id")

        # Confirmation popup
        confirm_window = ctk.CTkToplevel(self)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("500x140")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        confirm_window.attributes("-topmost", True)
        confirm_window.attributes("-toolwindow", True)

        # Center window on screen
        window_width = 500
        window_height = 140
        screen_width = confirm_window.winfo_screenwidth()
        screen_height = confirm_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        confirm_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        label = ctk.CTkLabel( confirm_window, text=f"Are you sure you want to delete '{group_name}'?", justify="center", font=("Arial", 16))
        label.pack(pady=(20, 10))

        def confirm_delete():
            try:
                groups_collection.delete_one({"_id": group_id})
                print(f"Deleted group '{group_name}'")
                confirm_window.destroy()
                self.fetch_groups()
            except Exception as e:
                print("Error deleting group:", e)

        # Buttons
        btn_frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        yes_btn = ctk.CTkButton(btn_frame, text="Yes", fg_color="red", command=confirm_delete)
        yes_btn.pack(side="left", padx=10)

        no_btn = ctk.CTkButton(btn_frame, text="No", command=confirm_window.destroy)
        no_btn.pack(side="left", padx=10)

    def on_resize(self, event=None):
        self.display_groups()

    def calculate_columns(self):
        available_width = self.winfo_width()
        if available_width <= 1:
            return 3
        return max(1, (available_width - 40) // (self.panel_width + self.panel_padding * 2))

    def show_addgroup(self):
        self.add_group_window = AddGroup.AddGroup(self, self.accid, self.username)
        self.add_group_window.focus()

    def open_group(self, group):
        group_id = str(group.get("_id", "Unknown"))
        group_name = group.get("GroupName", "Unnamed Group")
        self.switch_page("ViewGroup", {"GroupID": group_id, "GroupName": group_name})
