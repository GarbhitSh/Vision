"""
Tracking algorithm wrapper - ByteTrack
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from config.settings import settings
from utils.logger import logger


class ByteTracker:
    """ByteTrack tracker implementation"""
    
    def __init__(self):
        """Initialize ByteTrack tracker"""
        self.tracked_objects = {}  # track_id -> track info
        self.next_track_id = 1
        self.max_age = settings.TRACK_MAX_AGE
        self.min_hits = settings.TRACK_MIN_HITS
        self.iou_threshold = settings.TRACK_IOU_THRESHOLD
        self.frame_count = 0
    
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """
        Calculate Intersection over Union (IoU) between two boxes
        
        Args:
            box1: [x, y, w, h]
            box2: [x, y, w, h]
        
        Returns:
            IoU value
        """
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Calculate union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _match_detections_to_tracks(
        self,
        detections: List[Dict],
        tracks: Dict[int, Dict]
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Match detections to existing tracks using IoU
        
        Returns:
            matches: List of (detection_idx, track_id) tuples
            unmatched_dets: List of unmatched detection indices
            unmatched_trks: List of unmatched track IDs
        """
        if len(detections) == 0:
            return [], [], list(tracks.keys())
        
        if len(tracks) == 0:
            return [], list(range(len(detections))), []
        
        # Calculate IoU matrix
        iou_matrix = np.zeros((len(detections), len(tracks)))
        track_ids = list(tracks.keys())
        
        for i, det in enumerate(detections):
            for j, track_id in enumerate(track_ids):
                track = tracks[track_id]
                iou = self._calculate_iou(det["bbox"], track["bbox"])
                iou_matrix[i, j] = iou
        
        # Greedy matching
        matches = []
        unmatched_dets = list(range(len(detections)))
        unmatched_trks = list(track_ids)
        
        # Sort by IoU (highest first)
        iou_pairs = []
        for i in range(len(detections)):
            for j in range(len(track_ids)):
                if iou_matrix[i, j] > self.iou_threshold:
                    iou_pairs.append((iou_matrix[i, j], i, track_ids[j]))
        
        iou_pairs.sort(reverse=True, key=lambda x: x[0])
        
        matched_dets = set()
        matched_trks = set()
        
        for iou, det_idx, track_id in iou_pairs:
            if det_idx not in matched_dets and track_id not in matched_trks:
                matches.append((det_idx, track_id))
                matched_dets.add(det_idx)
                matched_trks.add(track_id)
        
        unmatched_dets = [i for i in range(len(detections)) if i not in matched_dets]
        unmatched_trks = [tid for tid in track_ids if tid not in matched_trks]
        
        return matches, unmatched_dets, unmatched_trks
    
    def update(self, detections: List[Dict]) -> List[Dict]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of detections from current frame
        
        Returns:
            List of tracked objects with track_id
        """
        self.frame_count += 1
        
        # Separate confirmed and tentative tracks
        confirmed_tracks = {}
        tentative_tracks = {}
        
        for track_id, track in self.tracked_objects.items():
            if track["hits"] >= self.min_hits:
                confirmed_tracks[track_id] = track
            else:
                tentative_tracks[track_id] = track
        
        # Match detections to confirmed tracks
        matches, unmatched_dets, unmatched_trks = self._match_detections_to_tracks(
            detections, confirmed_tracks
        )
        
        # Update matched tracks
        for det_idx, track_id in matches:
            det = detections[det_idx]
            self.tracked_objects[track_id].update({
                "bbox": det["bbox"],
                "confidence": det["confidence"],
                "hits": self.tracked_objects[track_id]["hits"] + 1,
                "age": 0,
                "last_seen": self.frame_count
            })
        
        # Match unmatched detections to tentative tracks
        unmatched_detections = [detections[i] for i in unmatched_dets]
        if len(unmatched_detections) > 0 and len(tentative_tracks) > 0:
            tentative_matches, unmatched_dets_new, unmatched_trks_tent = self._match_detections_to_tracks(
                unmatched_detections, tentative_tracks
            )
            
            # Update tentative matches
            for det_idx_new, track_id in tentative_matches:
                det = unmatched_detections[det_idx_new]
                self.tracked_objects[track_id].update({
                    "bbox": det["bbox"],
                    "confidence": det["confidence"],
                    "hits": self.tracked_objects[track_id]["hits"] + 1,
                    "age": 0,
                    "last_seen": self.frame_count
                })
            
            unmatched_dets = [unmatched_dets[i] for i in unmatched_dets_new]
            unmatched_trks.extend(unmatched_trks_tent)
        
        # Create new tracks for unmatched detections
        for det_idx in unmatched_dets:
            det = detections[det_idx]
            track_id = self.next_track_id
            self.next_track_id += 1
            
            self.tracked_objects[track_id] = {
                "track_id": track_id,
                "bbox": det["bbox"],
                "confidence": det["confidence"],
                "hits": 1,
                "age": 0,
                "last_seen": self.frame_count,
                "first_seen": self.frame_count
            }
        
        # Update age and remove old tracks
        tracks_to_remove = []
        for track_id, track in self.tracked_objects.items():
            if track_id in unmatched_trks:
                track["age"] += 1
                if track["age"] > self.max_age:
                    tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracked_objects[track_id]
        
        # Return confirmed tracks
        tracked_objects = []
        for track_id, track in self.tracked_objects.items():
            if track["hits"] >= self.min_hits:
                tracked_objects.append({
                    "track_id": track_id,
                    "bbox": track["bbox"],
                    "confidence": track["confidence"],
                    "age": track["age"],
                    "state": "confirmed"
                })
        
        return tracked_objects
    
    def get_track(self, track_id: int) -> Optional[Dict]:
        """Get track information by track_id"""
        return self.tracked_objects.get(track_id)
    
    def reset(self):
        """Reset tracker state"""
        self.tracked_objects = {}
        self.next_track_id = 1
        self.frame_count = 0

