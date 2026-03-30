import os
import io
from google.cloud import videointelligence

class VideoAnalyzer:
    def __init__(self, json_key_path, logger_callback):
        self.json_key_path = json_key_path
        self.log = logger_callback

    def analyze(self, video_path, target_objects_list):
        if not os.path.exists(self.json_key_path):
            self.log("[ERROR] Google Cloud JSON key not found! Please set it in the Settings tab.")
            return None

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.json_key_path

        self.log(f"[AI] Analyzing video: {os.path.basename(video_path)}...")
        self.log(f"[AI] Targets we are hunting for: {target_objects_list}")
        self.log(f"[AI] This may take a minute or two depending on video length.")

        try:
            client = videointelligence.VideoIntelligenceServiceClient()

            with io.open(video_path, "rb") as movie:
                input_content = movie.read()

            features = [videointelligence.Feature.OBJECT_TRACKING]
            request = videointelligence.AnnotateVideoRequest(
                input_content=input_content,
                features=features,
            )
            self.log("[AI] Request sent to Google Cloud. Waiting for processing...")

            operation = client.annotate_video(request=request)
            result = operation.result(timeout=600)

            self.log("[AI] Analysis complete! Scanning for matches...")

            annotations = result.annotation_results[0].object_annotations

            if not annotations:
                self.log("[AI] Google Cloud returned ZERO objects for this video.")
                return None

            self.log("[RAW DATA] Gathering all unique physical objects detected in the video...")
            detected_entities = set()

            for obj in annotations:
                name = obj.entity.description.lower()
                detected_entities.add(name)

            self.log(f"[RAW DATA] Google's vocabulary for this video: {list(detected_entities)}")
            self.log(f"[AI] --------------------------------------------------")

            valid_timestamps = []
            search_terms = [term.lower() for term in target_objects_list]

            for obj in annotations:
                found_label = obj.entity.description.lower()
                if any(term in found_label for term in search_terms):
                    start = obj.segment.start_time_offset.total_seconds()
                    end = obj.segment.end_time_offset.total_seconds()
                    conf = obj.confidence

                    self.log(f"[AI] Hit: '{found_label}' (Conf: {conf:.2f}) | {start}s to {end}s")
                    valid_timestamps.append((start, end))

            if not valid_timestamps:
                self.log("[AI] No target objects were physically tracked in this video.")
                return None

            merged_timestamps = self._merge_intervals(valid_timestamps)

            self.log(f"[AI] --------------------------------------------------")
            self.log(
                f"[AI] Merged {len(valid_timestamps)} raw tracking blips into {len(merged_timestamps)} solid clips.")

            for i, (start, end) in enumerate(merged_timestamps):
                self.log(f"      -> Final Trim Clip {i + 1}: {start}s to {end}s")

            return merged_timestamps
        except Exception as e:
            self.log(f"[AI ERROR] {str(e)}")
            return None

    def _merge_intervals(self, intervals):
        if not intervals:
            return []

        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]

        for current in intervals[1:]:
            previous = merged[-1]
            if current[0] <= previous[1] + 1.5:
                merged[-1] = (previous[0], max(previous[1], current[1]))
            else:
                merged.append(current)

        return merged
