"""
Kalman Filter for 2D Bounding Box Trajectory and Velocity Estimation
"""
from typing import Tuple
import numpy as np


class KalmanBoxTracker:
    """
    Kalman filter tracking bounding box state:
    [cx, cy, aspect_ratio, height, vx, vy, va, vh]
    """

    def __init__(self, bbox_xyxy: list):
        # State vector: [x, y, a, h, vx, vy, va, vh]
        self.state = np.zeros((8, 1), dtype=np.float32)
        # Covariance matrix
        self.covariance = np.eye(8, dtype=np.float32) * 10.0
        self.covariance[4:, 4:] *= 100.0  # High uncertainty on initial velocities

        # State transition matrix F
        self.F = np.eye(8, dtype=np.float32)
        for i in range(4):
            self.F[i, i + 4] = 1.0  # dt = 1.0 frame

        # Measurement matrix H
        self.H = np.zeros((4, 8), dtype=np.float32)
        for i in range(4):
            self.H[i, i] = 1.0

        # Motion noise Q and measurement noise R
        self.Q = np.eye(8, dtype=np.float32) * 1.0
        self.Q[4:, 4:] *= 0.1
        self.R = np.eye(4, dtype=np.float32) * 1.0

        # Initialize state with measurement
        self._init_state(bbox_xyxy)

    def _init_state(self, bbox_xyxy: list):
        x1, y1, x2, y2 = bbox_xyxy
        w = max(1.0, x2 - x1)
        h = max(1.0, y2 - y1)
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        aspect_ratio = w / h

        self.state[0, 0] = cx
        self.state[1, 0] = cy
        self.state[2, 0] = aspect_ratio
        self.state[3, 0] = h

    def predict(self) -> list:
        """
        Advance state vector by 1 time step and return predicted bounding box [x1, y1, x2, y2]
        """
        if self.state[3, 0] + self.state[7, 0] <= 0:
            self.state[7, 0] = 0.0

        self.state = np.dot(self.F, self.state)
        self.covariance = np.dot(np.dot(self.F, self.covariance), self.F.T) + self.Q
        return self.get_bbox()

    def update(self, bbox_xyxy: list):
        """
        Update state vector with new observed detection bounding box
        """
        x1, y1, x2, y2 = bbox_xyxy
        w = max(1.0, x2 - x1)
        h = max(1.0, y2 - y1)
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        aspect_ratio = w / h

        measurement = np.array([[cx], [cy], [aspect_ratio], [h]], dtype=np.float32)
        y = measurement - np.dot(self.H, self.state)
        S = np.dot(np.dot(self.H, self.covariance), self.H.T) + self.R
        K = np.dot(np.dot(self.covariance, self.H.T), np.linalg.inv(S))

        self.state = self.state + np.dot(K, y)
        self.covariance = self.covariance - np.dot(np.dot(K, self.H), self.covariance)

    def get_bbox(self) -> list:
        """Convert state [cx, cy, a, h] back to bounding box [x1, y1, x2, y2]"""
        cx = float(self.state[0, 0])
        cy = float(self.state[1, 0])
        aspect_ratio = max(0.01, float(self.state[2, 0]))
        h = max(1.0, float(self.state[3, 0]))
        w = aspect_ratio * h

        x1 = cx - w / 2.0
        y1 = cy - h / 2.0
        x2 = cx + w / 2.0
        y2 = cy + h / 2.0
        return [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]

    def get_velocity(self) -> Tuple[float, float]:
        """Return estimated velocities (vx, vy) in pixels/frame"""
        vx = float(self.state[4, 0])
        vy = float(self.state[5, 0])
        return (round(vx, 2), round(vy, 2))
