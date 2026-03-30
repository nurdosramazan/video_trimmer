import os
import sys
import subprocess
import threading

import customtkinter as ctk
from llm_agent import LLMAgent
from crawler import VideoDownloader
from video_analyzer import VideoAnalyzer

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class VideoCrawlerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.source_label = None
        self.source_optionmenu = None
        self.url_label = None
        self.url_entry = None
        self.keyword_label = None
        self.keyword_entry = None
        self.start_button = None
        self.log_textbox = None
        self.log_btn_frame = None
        self.cancel_button = None
        self.open_folder_button = None
        self.api_label = None
        self.api_entry = None
        self.browse_api_btn = None
        self.gemini_label = None
        self.gemini_entry = None

        self.title("AI Video Crawler & Trimmer")
        self.geometry("700x550")
        self.resizable(False, False)

        self.title_label = ctk.CTkLabel(self, text="Targeted Video Crawler", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.tabview = ctk.CTkTabview(self, width=650, height=400)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)

        self.tabview.add("Task Setup")
        self.tabview.add("Active Jobs & Logs")
        self.tabview.add("Settings")

        self.setup_task_tab()
        self.setup_logs_tab()
        self.setup_settings_tab()

        self.output_dir = "output_videos"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def setup_task_tab(self):
        tab = self.tabview.tab("Task Setup")
        tab.grid_columnconfigure(1, weight=1)

        self.source_label = ctk.CTkLabel(tab, text="Select Platform:")
        self.source_label.grid(row=0, column=0, padx=20, pady=(30, 10), sticky="w")
        self.source_optionmenu = ctk.CTkOptionMenu(tab, values=["YouTube", "TikTok", "Instagram"])
        self.source_optionmenu.grid(row=0, column=1, padx=20, pady=(30, 10), sticky="ew")

        self.keyword_label = ctk.CTkLabel(tab, text="Target Objects/Actions:")
        self.keyword_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.keyword_entry = ctk.CTkEntry(tab, placeholder_text="e.g., bench press, cutting onion")
        self.keyword_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        self.start_button = ctk.CTkButton(tab, text="Start Crawling & Trimming", command=self.start_processing,
                                          height=40)
        self.start_button.grid(row=3, column=0, columnspan=2, padx=20, pady=(40, 10))

    def setup_logs_tab(self):
        tab = self.tabview.tab("Active Jobs & Logs")
        self.log_textbox = ctk.CTkTextbox(tab, state="disabled")
        self.log_textbox.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        self.log_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.log_btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.cancel_button = ctk.CTkButton(self.log_btn_frame, text="Cancel Job", fg_color="#b23b3b",
                                           hover_color="#8f2f2f")
        self.cancel_button.pack(side="left", padx=(0, 10))

        self.open_folder_button = ctk.CTkButton(self.log_btn_frame, text="Open Output Folder",
                                                command=self.open_output_folder)
        self.open_folder_button.pack(side="right")

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(1, weight=1)

        self.api_label = ctk.CTkLabel(tab, text="Google Cloud JSON Path:")
        self.api_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.api_entry = ctk.CTkEntry(tab, placeholder_text="Path to credentials.json")
        self.api_entry.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="ew")

        self.browse_api_btn = ctk.CTkButton(tab, text="Browse", width=80, command=self.browse_api_key)
        self.browse_api_btn.grid(row=0, column=2, padx=(0, 20), pady=(20, 10))

        self.gemini_label = ctk.CTkLabel(tab, text="Gemini API Key:")
        self.gemini_label.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="w")
        self.gemini_entry = ctk.CTkEntry(tab, placeholder_text="Paste your free Gemini API key here")
        self.gemini_entry.grid(row=1, column=1, columnspan=2, padx=20, pady=(10, 10), sticky="ew")

    def browse_api_key(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Select Google Cloud JSON Key",
            filetypes=[("JSON Files", "*.json")]
        )
        if file_path:
            self.api_entry.delete(0, "end")
            self.api_entry.insert(0, file_path)

    def log_message(self, message):
        self.after(0, self._insert_log, message)

    def _insert_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def open_output_folder(self):
        if sys.platform.startswith("win"):
            os.startfile(self.output_dir)
        elif sys.platform == "darwin":
            subprocess.call(["open", self.output_dir])
        else:
            subprocess.call(["xdg-open", self.output_dir])

    def start_processing(self):
        source = self.source_optionmenu.get()
        raw_input = self.keyword_entry.get()

        if not raw_input:
            self.tabview.set("Active Jobs & Logs")
            self.log_message("[ERROR] Please provide Search Criteria.")
            return

        self.tabview.set("Active Jobs & Logs")
        self.log_message(f"[INFO] Starting job...")
        self.log_message(f"Source: {source}")
        self.log_message(f"Keywords: {raw_input}")

        self.start_button.configure(state="disabled")

        agent_thread = threading.Thread(target=self.run_agent_pipeline, args=(raw_input, source), daemon=True)
        agent_thread.start()

    def run_agent_pipeline(self, raw_input, source):
        try:
            gemini_key = self.gemini_entry.get()
            google_json = self.api_entry.get()

            agent = LLMAgent(api_key=gemini_key, logger_callback=self.log_message)
            crawler = VideoDownloader(output_dir=self.output_dir, logger_callback=self.log_message)
            vision_ai = VideoAnalyzer(json_key_path=google_json, logger_callback=self.log_message)

            optimized_data = agent.translate_intent(raw_input)
            if not optimized_data:
                return

            search_query = optimized_data["platform_search_query"]
            vision_objects = optimized_data["vision_target_objects"]

            self.log_message(f"[INFO] Searching for: '{vision_objects}'")

            downloaded_files = crawler.download(search_query, source)

            for title, file_path in downloaded_files:
                self.log_message(f"[INFO] Successfully Saved: {file_path}")

                timestamps = vision_ai.analyze(file_path, optimized_data)

                if timestamps:
                    self.log_message("-" * 40)
                    self.log_message("[INFO] Ready for Step 4 (Trimming).")
                    # TODO: Step 4 - Send timestamps to FFmpeg to cut the video
                else:
                    self.log_message(f"[WARNING] No visual matches found, skipping trim for: {title}")

                self.log_message("-" * 40)

        except Exception as e:
            self.log_message(f"[PIPELINE ERROR] {str(e)}")
        finally:
            self.after(0, lambda: self.start_button.configure(state="normal"))

        self.log_message("[INFO] End of the session.")


if __name__ == "__main__":
    app = VideoCrawlerApp()
    app.mainloop()
