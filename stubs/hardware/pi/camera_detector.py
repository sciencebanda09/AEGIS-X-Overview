"""
camera_detector.py — AEGIS-X Camera Detection Pipeline
========================================================
Public interface stub. Core implementation is proprietary.

Detection backends (selected at init):
  • YOLOv8n  — fine-tuned drone detector (requires ultralytics + .pt)
  • BlobDetector — background subtraction + HSV LED detection (fallback)
  • MockCamera — synthetic detections for PC testing (no OpenCV)

Pixel-to-angle conversion:
  • bbox centre → azimuth / elevation via FOV geometry
  • Default FOV: H=62.2°, V=48.8° (Pi Camera v2)

Author : SentrixLab
Version: 17.0
License: Proprietary — contact for licensing
"""

import threading
import queue
import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

log = logging.getLogger("Camera")


@dataclass
class Detection:
    """Single drone detection from one camera frame."""
    confidence:    float   # 0.0–1.0
    azimuth_deg:   float   # + = right of camera centre
    elevation_deg: float   # + = above camera centre
    bbox_area:     float   # pixels² — proxy for distance
    label:         str = "drone"
    frame_x:       float = 0.0   # pixel centre X
    frame_y:       float = 0.0   # pixel centre Y


def bbox_to_angles(
    x1: float, y1: float, x2: float, y2: float,
    frame_w: int, frame_h: int,
    hfov_deg: float = 62.2,
    vfov_deg: float = 48.8,
) -> tuple[float, float, float]:
    """
    Convert bounding box pixel coordinates to azimuth/elevation angles.

    Args:
        x1, y1, x2, y2 : bounding box corners in pixels
        frame_w, frame_h: frame dimensions
        hfov_deg        : horizontal FOV in degrees
        vfov_deg        : vertical FOV in degrees

    Returns:
        (azimuth_deg, elevation_deg, bbox_area_px²)
        azimuth  > 0 = right, elevation > 0 = up
    """
    raise NotImplementedError("Proprietary — contact SentrixLab for licensing")


class CameraDetector:
    """
    Background camera thread.

    Reads frames, runs detection (YOLO or blob), converts pixel
    coordinates to angular measurements, pushes Detection objects
    to output queue.

    Usage
    -----
    detector = CameraDetector(
        camera_index = 0,
        use_yolo     = True,
        yolo_path    = 'models/drone_yolov8n.pt',
    )
    q = queue.Queue(maxsize=5)
    detector.start(q)

    # In main loop:
    dets = q.get()   # list of Detection objects
    detector.stop()
    """

    def __init__(
        self,
        camera_index: int   = 0,
        width:        int   = 640,
        height:       int   = 480,
        fps:          int   = 30,
        use_yolo:     bool  = False,
        yolo_path:    str   = "yolov8n.pt",
        hfov_deg:     float = 62.2,
        vfov_deg:     float = 48.8,
    ):
        """
        Args:
            camera_index: OpenCV camera index (0 = first camera)
            width, height: capture resolution
            fps          : target frame rate
            use_yolo     : use YOLOv8n if True, blob detector if False
            yolo_path    : path to .pt model file
            hfov_deg     : horizontal FOV for angle conversion
            vfov_deg     : vertical FOV for angle conversion
        """
        raise NotImplementedError("Proprietary — contact SentrixLab for licensing")

    def start(self, out_queue: queue.Queue) -> None:
        """
        Start background camera thread.

        Args:
            out_queue: Queue to push List[Detection] into (~30 Hz).
                       Uses put_nowait — drops frames if queue full.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Stop thread and release camera resource."""
        raise NotImplementedError
