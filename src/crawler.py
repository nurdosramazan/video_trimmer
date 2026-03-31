import os
import yt_dlp
import static_ffmpeg
from duckduckgo_search import DDGS

static_ffmpeg.add_paths()

class VideoDownloader:
    def __init__(self, output_dir, logger_callback):
        self.output_dir = output_dir
        self.log = logger_callback

    def search_urls(self, search_query, source, limit=20):
        self.log(f"[CRAWLER] Searching for '{search_query}' on {source}...")
        urls = []

        try:
            if source == "YouTube":
                ydl_opts = {'extract_flat': 'in_playlist', 'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch{limit}:{search_query}", download=False)
                    if info and 'entries' in info:
                        urls = [entry['url'] for entry in info['entries'] if entry.get('url')]

            elif source in ["TikTok", "Instagram"]:
                domain = "tiktok.com" if source == "TikTok" else "instagram.com"

                ddg_query = f'site:{domain} {search_query}'

                with DDGS() as ddgs:
                    results = ddgs.text(ddg_query, max_results=limit)
                    urls = [res['href'] for res in results if domain in res['href']]

            self.log(f"[CRAWLER] Successfully found {len(urls)} potential links.")
            return urls

        except Exception as e:
            self.log(f"[CRAWLER ERROR] Failed to search URLs: {str(e)}")
            return []

    def download_single(self, url):
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'match_filter': yt_dlp.utils.match_filter_func("duration < 150"),
            'outtmpl': f'{self.output_dir}/%(id)s.%(ext)s',
            'restrictfilenames': True,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)

                if not info_dict:
                    self.log("[ERROR] No data returned from yt_dlp.")
                    return None

                base_path = ydl.prepare_filename(info_dict)
                file_path = os.path.splitext(base_path)[0] + ".mp4"

                if os.path.exists(file_path):
                    self.log(f"[DOWNLOAD SUCCESS] Saved to {os.path.basename(file_path)}")
                    return file_path
                else:
                    return None
        except Exception as e:
            self.log(f"[SKIPPED] Video unavailable or too long.")
            return None
