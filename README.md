# AI Video Crawler & Trimmer

An automated desktop Python application to find, download, analyze, and  trim video clips based on semantic search queries.
(Right now, I use Gemini LLM for analyzing video, however, I plan to integrate CLIP for zero-shot local frame scoring and understand videos.)

This project automates the entire workflow of:
1. Search platforms like YouTube, TikTok, and Instagram
2. Download relevant videos
3. Use AI to locate exact timestamps of the action
4. Automatically trim and merge highlights into a final video
---

## Features
* **Semantic Video Understanding** 
  * Uses Google Gemini Multimodal API to interpret video content and detect actions contextually.
* **Automated Video Sourcing**
  * YouTube via `yt-dlp`
  * TikTok & Instagram via DuckDuckGo search techniques

* **Smart Video Editing**
  * Automatically trims and merges clips using `ffmpeg`.

* **Responsive Multi-threaded GUI**
  * Built with `customtkinter`, keeping UI smooth during processing.

---

## Prerequisites

### 1. Python
* Python **3.8+**

### 2. FFmpeg
Must be installed and available in your system PATH:

* **Windows**
  ```bash
  winget install ffmpeg
  ```
* **Mac**
  ```bash
  brew install ffmpeg
  ```
* **Linux**
  ```bash
  sudo apt install ffmpeg
  ```

### 3. Google Gemini API Key
Get a free key from: [https://aistudio.google.com/](https://aistudio.google.com/)

---

## Installation

```bash
# Clone repository
git clone https://github.com/nurdosramazan/video_trimmer.git
cd ai-video-crawler

# Install dependencies
pip install customtkinter google-genai yt-dlp static-ffmpeg duckduckgo-search python-dotenv opencv-python
```

### Environment Setup

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_api
```

---

## Usage

Run the application:

```bash
python video_trimmer_app.py
```

### Steps:

1. **Select Platform**
   Choose: YouTube, TikTok, or Instagram

2. **Enter Search Query**
   Example:

   ```
   chopping onions
   ```

3. **Set Target File Count**
   Number of clips to generate

4. **Set Max Duration**
   Total length of final video

5. Click **Start Pipeline**

📁 Output videos are saved in:

```
output_videos/
```