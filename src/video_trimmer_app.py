import os
import sys
import subprocess
import threading
import customtkinter as ctk
from dotenv import load_dotenv

from llm_agent import LLMAgent
from crawler import VideoDownloader
from video_analyzer import VideoAnalyzer
from video_editor import VideoEditor

load_dotenv()

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class VideoCrawlerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Video Crawler & Trimmer")
        self.geometry("700x650")
        self.resizable(False, False)

        self.cancel_event = threading.Event()

        self.title_label = ctk.CTkLabel(self, text="Targeted Video Crawler", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.tabview = ctk.CTkTabview(self, width=650, height=450)
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

        ctk.CTkLabel(tab, text="Select Platform:").grid(row=0, column=0, padx=20, pady=(15, 10), sticky="w")
        self.source_optionmenu = ctk.CTkOptionMenu(tab, values=["YouTube", "TikTok", "Instagram"])
        self.source_optionmenu.grid(row=0, column=1, padx=20, pady=(15, 10), sticky="ew")

        ctk.CTkLabel(tab, text="Search Criteria:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.keyword_entry = ctk.CTkEntry(tab, placeholder_text="e.g., bench press, cutting onion")
        self.keyword_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(tab, text="Target Clip Count:").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.count_entry = ctk.CTkEntry(tab, placeholder_text="How many videos do you want?")
        self.count_entry.insert(0, "3")
        self.count_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(tab, text="Max Seconds Per Video:").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.length_entry = ctk.CTkEntry(tab, placeholder_text="e.g. 10")
        self.length_entry.insert(0, "15")
        self.length_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")

        self.btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.btn_frame.grid(row=4, column=0, columnspan=2, pady=(30, 10))

        self.start_button = ctk.CTkButton(self.btn_frame, text="Start Pipeline", command=self.start_processing,
                                          height=40)
        self.start_button.pack(side="left", padx=10)

        self.cancel_button = ctk.CTkButton(self.btn_frame, text="Cancel Job", command=self.cancel_processing, height=40,
                                           fg_color="#C62828", hover_color="#b71c1c", state="disabled")
        self.cancel_button.pack(side="left", padx=10)

    def setup_logs_tab(self):
        tab = self.tabview.tab("Active Jobs & Logs")
        self.log_textbox = ctk.CTkTextbox(tab, state="disabled")
        self.log_textbox.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        self.log_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.log_btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.open_folder_button = ctk.CTkButton(self.log_btn_frame, text="Open Output Folder",
                                                command=self.open_output_folder)
        self.open_folder_button.pack(side="right")

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(1, weight=1)
        env_key = os.getenv("GEMINI_API_KEY", "")

        self.gemini_video_label = ctk.CTkLabel(tab, text="Gemini API Key for video:")
        self.gemini_video_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.gemini_video_entry = ctk.CTkEntry(tab, placeholder_text="Paste your Gemini API key here", show="*")
        self.gemini_video_entry.insert(0, env_key)
        self.gemini_video_entry.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="ew")

        self.gemini_intent_label = ctk.CTkLabel(tab, text="Gemini API Key for intent translation:")
        self.gemini_intent_label.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="w")
        self.gemini_intent_entry = ctk.CTkEntry(tab, placeholder_text="Paste your Gemini API key here", show="*")
        self.gemini_intent_entry.insert(0, env_key)
        self.gemini_intent_entry.grid(row=1, column=1, padx=20, pady=(10, 10), sticky="ew")

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

    def cancel_processing(self):
        if not self.cancel_event.is_set():
            self.log_message("\n[WARNING] Cancelling job... (Will stop after current task finishes)")
            self.cancel_event.set()
            self.cancel_button.configure(state="disabled")

    def start_processing(self):
        source = self.source_optionmenu.get()
        raw_input = self.keyword_entry.get()

        try:
            target_count = int(self.count_entry.get())
            max_len = float(self.length_entry.get())
        except ValueError:
            self.log_message("[ERROR] Please enter valid numbers for Count and Length.")
            return

        if not raw_input:
            self.tabview.set("Active Jobs & Logs")
            self.log_message("[ERROR] Please provide Search Criteria.")
            return

        self.tabview.set("Active Jobs & Logs")
        self.log_message("-" * 40)
        self.log_message(f"[INFO] Starting job...")
        self.log_message(f"STARTING NEW JOB: {raw_input} ({source})")

        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.cancel_event.clear()

        threading.Thread(target=self.run_agent_pipeline, args=(raw_input, source, target_count, max_len),
                         daemon=True).start()

    def run_agent_pipeline(self, raw_input, source, target_count, max_len):
        try:
            gemini_key_intent = self.gemini_intent_entry.get()
            gemini_key_video = self.gemini_video_entry.get()

            agent = LLMAgent(api_key=gemini_key_intent, logger_callback=self.log_message)
            crawler = VideoDownloader(output_dir=self.output_dir, logger_callback=self.log_message)
            analyzer = VideoAnalyzer(api_key=gemini_key_video, logger_callback=self.log_message)
            editor = VideoEditor(output_dir=self.output_dir, logger_callback=self.log_message)

            optimized_data = agent.translate_intent(raw_input)
            if not optimized_data:
                return

            self.log_message(f"[INFO] Hunting for {target_count} clips on {source}...")
            url_pool = crawler.search_urls(optimized_data["platform_search_query"], source, limit=20)
            successful_clips = 0
            while successful_clips < target_count and url_pool:
                if self.cancel_event.is_set():
                    self.log_message("[CANCELLED] Pipeline stopped by user.")
                    break
                current_url = url_pool.pop(0)
                self.log_message(f"\n[PIPELINE] Processing next candidate ({successful_clips}/{target_count} done)")

                video_file = crawler.download_single(current_url)
                if not video_file:
                    continue

                if self.cancel_event.is_set():
                    if os.path.exists(video_file): os.remove(video_file)
                    self.log_message("[CANCELLED] Pipeline stopped by user.")
                    break

                timestamps = analyzer.analyze_with_gemini(video_file, raw_input)
                if self.cancel_event.is_set():
                    if os.path.exists(video_file): os.remove(video_file)
                    self.log_message("[CANCELLED] Pipeline stopped by user.")
                    break

                if timestamps:
                    final_video = editor.trim_and_merge(video_file, timestamps, max_length=max_len)
                    if final_video:
                        successful_clips += 1
                else:
                    self.log_message(f"[SKIP] No action matches found in this video.")

                if os.path.exists(video_file):
                    os.remove(video_file)

            if not self.cancel_event.is_set():
                if successful_clips < target_count:
                    self.log_message(f"[INFO] Finished. Found {successful_clips} clips (ran out of search results).")
                else:
                    self.log_message(f"[FINISH] Successfully collected {target_count} clips!")

        except Exception as e:
            self.log_message(f"[PIPELINE ERROR] {str(e)}")
        finally:
            self.after(0, lambda: self.start_button.configure(state="normal"))
            self.after(0, lambda: self.cancel_button.configure(state="disabled"))

        self.log_message("[INFO] End of the session.")


if __name__ == "__main__":
    app = VideoCrawlerApp()
    app.mainloop()
