import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class VideoCrawlerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Video Crawler & Trimmer")
        self.geometry("600x650")
        self.resizable(False, False)

        self.title_label = ctk.CTkLabel(self, text="Targeted Video Crawler", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 20))

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(pady=10, padx=20, fill="x")

        self.source_label = ctk.CTkLabel(self.input_frame, text="Select Platform:", anchor="w")
        self.source_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")

        self.source_optionmenu = ctk.CTkOptionMenu(self.input_frame, values=["YouTube", "TikTok", "Instagram"])
        self.source_optionmenu.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="ew")

        self.url_label = ctk.CTkLabel(self.input_frame, text="Starting URL:", anchor="w")
        self.url_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.url_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., https://www.youtube.com/c/SomeChannel")
        self.url_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.keyword_label = ctk.CTkLabel(self.input_frame, text="Target Objects/Actions:", anchor="w")
        self.keyword_label.grid(row=2, column=0, padx=10, pady=(5, 15), sticky="w")

        self.keyword_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., bench press, cutting onion")
        self.keyword_entry.grid(row=2, column=1, padx=10, pady=(5, 15), sticky="ew")

        self.input_frame.grid_columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(self, text="Start Processing", command=self.start_processing)
        self.start_button.pack(pady=20)

        self.log_label = ctk.CTkLabel(self, text="Process Logs:", anchor="w")
        self.log_label.pack(padx=20, fill="x")

        self.log_textbox = ctk.CTkTextbox(self, height=200, state="disabled")
        self.log_textbox.pack(padx=20, pady=(0, 20), fill="both", expand=True)

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def start_processing(self):
        source = self.source_optionmenu.get()
        url = self.url_entry.get()
        keywords = self.keyword_entry.get()

        if not url or not keywords:
            self.log_message("[ERROR] Please provide both a URL and Search Criteria.")
            return

        # Log the inputs
        self.log_message(f"[INFO] Starting job...")
        self.log_message(f"Source: {source}")
        self.log_message(f"URL: {url}")
        self.log_message(f"Keywords: {keywords}")

        # TODO: yt-dlp integration
        self.log_message("[INFO] Ready to begin downloading. (Waiting for Step 2...)")
        self.log_message("-" * 40)


if __name__ == "__main__":
    app = VideoCrawlerApp()
    app.mainloop()
