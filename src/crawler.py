import os
import yt_dlp
import static_ffmpeg

static_ffmpeg.add_paths()

class VideoDownloader:
    def __init__(self, output_dir, logger_callback):
        self.output_dir = output_dir
        self.log = logger_callback

    def download(self, search_query, source):
        self.log(f"[INFO] Initiating global crawler on: {source}")
        max_results = 3

        if source == "YouTube":
            platform_search = f"ytsearch{max_results}:{search_query}"
        elif source == "TikTok" or source == "Instagram":
            self.log(f"[WARNING] {source} global search is limited for now.")
            platform_search = f"ytsearch{max_results}:{search_query}"
        else:
            self.log(f"[ERROR] {source} search not supported yet.")
            return []

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'match_filter': yt_dlp.utils.match_filter_func("duration < 300"),
            'outtmpl': f'{self.output_dir}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        downloaded_files = []

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.log(f"[INFO] Traversing relevant links...")
                info_dict = ydl.extract_info(platform_search, download=True)

                if not info_dict:
                    self.log("[ERROR] No data returned from yt_dlp.")
                    return []

                # Preserved your exact logging loops
                if 'entries' in info_dict:
                    for entry in info_dict['entries']:
                        if entry:
                            self.log(f"[SUCCESS] Downloaded: {entry.get('title')}")
                else:
                    self.log(f"[SUCCESS] Downloaded: {info_dict.get('title')}")

                self.log("-" * 40)

                if 'entries' in info_dict:
                    for entry in info_dict['entries']:
                        if entry:
                            base_path = ydl.prepare_filename(entry)
                            file_path = os.path.splitext(base_path)[0] + ".mp4"

                            if os.path.exists(file_path):
                                self.log(f"[INFO] Successfully Saved: {file_path}")
                                downloaded_files.append((entry.get('title'), file_path))
                            else:
                                self.log(f"[WARNING] Skipped or failed to merge: {entry.get('title')}")

                self.log("-" * 40)
                return downloaded_files

        except Exception as e:
            self.log(f"[ERROR] Failed to download: {str(e)}")
            self.log("-" * 40)
            return []
