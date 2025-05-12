import customtkinter as ctk


class HelpApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Help & Support")
        self.geometry("600x400")
        self.minsize(600, 400)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", True)
        self.grab_set()

        # Center the window on the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width // 2) - (600 // 2)
        y_position = (screen_height // 2) - (400 // 2)
        self.geometry(f"600x400+{x_position}+{y_position}")

        # Main Frame with Scrollbar
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Helper function to add labeled sections
        def add_section(title, content, wraplength=560, icon=None):
            section_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            section_frame.pack(fill="x", padx=5, pady=(10, 5))

            title_text = f"{icon} {title}" if icon else title
            title_label = ctk.CTkLabel(section_frame, text=title_text, font=("Arial", 20, "bold"), anchor="w")
            title_label.pack(fill="x", pady=(5, 2))

            content_label = ctk.CTkLabel(
                section_frame, text=content, font=("Arial", 16), justify="left", wraplength=wraplength
            )
            content_label.pack(fill="x", pady=(0, 5))

        # Content Sections
        add_section(
            "ALTHOS Overview",
            "Welcome to the Help & Support page of the ALTHOS Monitoring System. This system allows you to monitor keyboard and mouse activity, detect user emotions through webcam, and view screen sharing—all in real-time—to support student engagement and productivity in laboratories.",
            icon="📖",
        )

        add_section(
            "Features Guide",
            "Screen Sharing\n\n - View real-time screens of all connected devices.\n\n - Click a screen panel for a larger preview. \n\nKeyboard & Mouse Monitoring \n\nStatus Types:\n\n - Idle (Gray): No input detected for 5+ seconds. \n\n - Normal (Green): Light or steady usage. \n\n - Erratic (Red): Rapid or chaotic input patterns. \n\n Useful for identifying distracted or overwhelmed students. \n\nEmotion Detection (via Webcam) \n\n - Detects facial expressions and classifies them as: \n\n - angry (Red), fear (Violet), happy (Yellow), sad (Blue), surprise (Orange), neutral (Gray) \n\n - Helps instructors gauge student mood.",
            icon="🔍",
        )

        add_section(
            "Troubleshooting",
            "Q1: Devices are not connecting. \n\n - Ensure all devices are on the same network. \n - Check firewall settings—allow access to the app. \n - Double-check IP address input on the Monitoring App. \n\n\n Q2: Webcam feed not showing. \n - Ensure camera access is allowed on client PC. \n - Check if another app is using the webcam. \n\n\n"
            "Q3: No emotion detected. \n - Make sure lighting is sufficient and face is visible. \n - Restart the client app if detection freezes. \n\n\n Q4: Keyboard/mouse activity not updating. \n - Ensure client app is running in the background. \n - Restart the app or reconnect via the Monitoring App.",
            icon="🚨",
        )

        add_section(
            "Contact & Feedback",
            "For feedback or support, please contact us at: \n\nEmail: Alt.plus.f4.2024@gmail.com",
            icon="📩",
        )

        # Add a "Back to Top" button
        back_to_top = ctk.CTkButton(
            self.main_frame,
            text="⬆ Back to Top",
            command=lambda: self.main_frame._parent_canvas.yview_moveto(0),
        )
        back_to_top.pack(pady=(10, 20))


if __name__ == "__main__":
    app = HelpApp()
    app.mainloop()