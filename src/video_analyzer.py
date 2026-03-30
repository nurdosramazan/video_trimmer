import os
import io
import math
from google.cloud import videointelligence
from difflib import SequenceMatcher

class VideoAnalyzer:
    def __init__(self, json_key_path, logger_callback):
        self.json_key_path = json_key_path
        self.log = logger_callback

    def is_similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() > 0.7

    def analyze(self, video_path, intent_data):
        if not os.path.exists(self.json_key_path):
            self.log("[ERROR] Google Cloud JSON key not found! Please set it in the Settings tab.")
            return None

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.json_key_path

        self.log(f"[AI] Analyzing video: {os.path.basename(video_path)}...")
        positive_targets = [t.lower() for t in intent_data["vision_target_objects"] + intent_data["broad_synonyms"]]
        negative_targets = [t.lower() for t in intent_data["negative_concepts"]]

        self.log(f"[AI] Targets we are hunting for: {intent_data}")
        self.log(f"[AI] Negatives we penalize: {negative_targets}")
        self.log(f"[AI] This may take a minute or two depending on video length.")

        try:
            client = videointelligence.VideoIntelligenceServiceClient()

            with io.open(video_path, "rb") as movie:
                input_content = movie.read()

            features = [
                videointelligence.Feature.OBJECT_TRACKING,
                videointelligence.Feature.LABEL_DETECTION
            ]
            request = videointelligence.AnnotateVideoRequest(
                input_content=input_content,
                features=features,
            )
            self.log("[AI] Request sent to Google Cloud. Waiting for processing...")

            operation = client.annotate_video(request=request)
            result = operation.result(timeout=600)

            self.log("[AI] Analysis complete! Scanning for matches...")

            max_time = 0.0

            def get_end_time(segment):
                return segment.end_time_offset.total_seconds()

            raw_positives = []
            raw_negatives = []
            detected_vocab = set()

            for obj in result.annotation_results[0].object_annotations:
                label = obj.entity.description.lower()
                detected_vocab.add(label)
                start = obj.segment.start_time_offset.total_seconds()
                end = get_end_time(obj.segment)
                if end > max_time: max_time = end

                if any(self.is_similar(term, label) or term in label for term in positive_targets):
                    raw_positives.append((label, start, end))
                elif any(self.is_similar(term, label) or term in label for term in negative_targets):
                    raw_negatives.append((label, start, end))

            for label_annotation in result.annotation_results[0].segment_label_annotations:
                label = label_annotation.entity.description.lower()
                detected_vocab.add(label)
                for segment in label_annotation.segments:
                    start = segment.segment.start_time_offset.total_seconds()
                    end = get_end_time(segment.segment)
                    if end > max_time: max_time = end

                    if any(self.is_similar(term, label) or term in label for term in positive_targets):
                        raw_positives.append((label, start, end))
                    elif any(self.is_similar(term, label) or term in label for term in negative_targets):
                        raw_negatives.append((label, start, end))

            self.log(f"[RAW DATA] Google's vocabulary for this video included: {list(detected_vocab)[:15]}...")
            if not raw_positives:
                self.log("[WARNING] No target objects or synonyms were found in this video.")
                return None

            num_buckets = math.ceil(max_time) + 1
            time_buckets = [{"pos": set(), "neg": set()} for _ in range(num_buckets)]

            for label, start, end in raw_positives:
                for sec in range(math.floor(start), math.ceil(end)):
                    if sec < num_buckets: time_buckets[sec]["pos"].add(label)

            for label, start, end in raw_negatives:
                for sec in range(math.floor(start), math.ceil(end)):
                    if sec < num_buckets: time_buckets[sec]["neg"].add(label)

            action_seconds = []
            for sec, bucket in enumerate(time_buckets):
                score = len(bucket["pos"]) - (len(bucket["neg"]) * 3)  # Negatives carry a heavy penalty

                if score >= 2:
                    action_seconds.append(sec)

            if not action_seconds:
                self.log(
                    "[WARNING] Objects were found, but were heavily filtered by negative 'Talking Head' constraints.")
                return None

            intervals = []
            current_start = action_seconds[0]
            current_end = action_seconds[0]

            for sec in action_seconds[1:]:
                if sec <= current_end + 3:
                    current_end = sec
                else:
                    intervals.append((current_start, current_end))
                    current_start = sec
                    current_end = sec
            intervals.append((current_start, current_end))

            final_clips = []
            for start, end in intervals:
                if (end - start) >= 2:
                    pad_start = max(0.0, float(start) - 2.0)
                    pad_end = float(end) + 2.0
                    final_clips.append((pad_start, pad_end))

            self.log(f"[AI SUCCESS] Extracted {len(final_clips)} action-dense clips!")
            for i, (s, e) in enumerate(final_clips):
                self.log(f"      -> Final Trim Clip {i + 1}: {s}s to {e}s")

            return final_clips
        except Exception as e:
            self.log(f"[AI ERROR] {str(e)}")
            return None
