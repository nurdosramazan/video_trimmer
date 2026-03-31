import os
import subprocess

class VideoEditor:
    def __init__(self, output_dir, logger_callback):
        self.output_dir = output_dir
        self.log = logger_callback

    def trim_and_merge(self, input_video, timestamps, max_length):
        abs_output_dir = os.path.abspath(self.output_dir)
        abs_input_video = os.path.abspath(input_video)

        base_name = os.path.splitext(os.path.basename(input_video))[0]
        final_output = os.path.join(abs_output_dir, f"{base_name}_trimmed.mp4")

        temp_clips = []
        list_file_path = os.path.join(abs_output_dir, f"{base_name}_concat.txt")
        total_duration = 0.0

        try:
            for i, (start, end) in enumerate(timestamps):
                duration = end - start

                if total_duration + duration > max_length:
                    duration = max_length - total_duration

                if duration <= 0:
                    break

                clip_name = os.path.join(abs_output_dir, f"{base_name}_part{i}.mp4")
                temp_clips.append(clip_name)

                cmd = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", str(start), "-i", abs_input_video, "-t", str(duration),
                    "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
                    clip_name
                ]
                subprocess.run(cmd, check=True)
                total_duration += duration
                if total_duration >= max_length:
                    self.log(f"[EDITOR] Max length ({max_length}s) reached.")
                    break

            with open(list_file_path, "w", encoding="utf-8") as f:
                for clip in temp_clips:
                    safe_path = clip.replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            self.log("[EDITOR] Merging clips into final video...")
            concat_cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", list_file_path,
                "-c", "copy", final_output
            ]
            subprocess.run(concat_cmd, check=True)

            self.log(f"[EDITOR SUCCESS] Saved final video: {os.path.basename(final_output)}")

        except subprocess.CalledProcessError as e:
            self.log(f"[EDITOR ERROR] FFmpeg failed: {e}")
            return None
        finally:
            for clip in temp_clips:
                if os.path.exists(clip):
                    os.remove(clip)
            if os.path.exists(list_file_path):
                os.remove(list_file_path)

        return final_output if os.path.exists(final_output) else None
