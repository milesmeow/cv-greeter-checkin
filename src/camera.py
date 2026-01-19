"""
Camera module for webcam capture.

Handles webcam initialization, frame capture, and cleanup.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from enum import Enum, auto


class CameraState(Enum):
    """Camera connection states."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    WARMING_UP = auto()
    READY = auto()
    ERROR = auto()


class Camera:
    """Manages webcam capture for the check-in system."""
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize the camera.

        Args:
            camera_index: Which camera to use (0 = default/first camera)
        """
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_running = False
        self._state = CameraState.DISCONNECTED
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
    
    def start(self) -> bool:
        """
        Start the camera capture.

        Returns:
            True if camera started successfully, False otherwise
        """
        if self._is_running:
            return True

        self._state = CameraState.CONNECTING
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_index}")
            self._state = CameraState.ERROR
            return False

        # Set camera properties for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self._is_running = True
        self._state = CameraState.WARMING_UP
        self._consecutive_failures = 0
        return True
    
    def stop(self):
        """Release the camera."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self._is_running = False
        self._state = CameraState.DISCONNECTED

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.

        Returns:
            BGR image as numpy array, or None if capture failed
        """
        if not self._is_running or self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret or frame is None:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_consecutive_failures:
                self._state = CameraState.ERROR
            return None

        # Reset failure count on successful frame
        self._consecutive_failures = 0
        return frame

    def set_ready(self):
        """Mark camera as ready (valid frames being received)."""
        self._state = CameraState.READY
        self._consecutive_failures = 0
    
    def get_frame_rgb(self) -> Optional[np.ndarray]:
        """
        Capture a frame and convert to RGB.
        
        The face_recognition library expects RGB format.
        
        Returns:
            RGB image as numpy array, or None if capture failed
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def get_frame_for_display(self) -> Optional[np.ndarray]:
        """
        Capture a frame ready for Tkinter display.
        
        Flips horizontally (mirror effect) for more natural interaction.
        
        Returns:
            RGB image as numpy array, or None if capture failed
        """
        frame = self.get_frame()
        if frame is None:
            return None
        
        # Mirror the image for more natural feel
        frame = cv2.flip(frame, 1)
        
        # Convert BGR to RGB for display
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def capture_for_recognition(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Capture a frame for face recognition.
        
        Returns:
            Tuple of (display_frame, recognition_frame)
            - display_frame: Mirrored RGB for UI display
            - recognition_frame: Non-mirrored RGB for face_recognition
            
            Returns (None, None) if capture failed
        """
        frame = self.get_frame()
        if frame is None:
            return None, None
        
        # Display frame (mirrored)
        display_frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        
        # Recognition frame (not mirrored - face_recognition needs consistent orientation)
        recognition_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return display_frame, recognition_frame
    
    @property
    def is_running(self) -> bool:
        """Check if camera is currently capturing."""
        return self._is_running

    @property
    def state(self) -> CameraState:
        """Get current camera state."""
        return self._state

    def is_frame_valid(self, frame: np.ndarray) -> bool:
        """
        Check if a frame is valid for display.

        Args:
            frame: The frame to validate

        Returns:
            True if frame is valid, False otherwise
        """
        if frame is None:
            return False

        # Check dimensions
        if len(frame.shape) != 3:
            return False

        height, width, channels = frame.shape
        if height < 10 or width < 10 or channels != 3:
            return False

        # Check not all black (camera not ready)
        mean_brightness = np.mean(frame)
        if mean_brightness < 5:
            return False

        # Check not blown out/white
        if mean_brightness > 250:
            return False

        return True

    @staticmethod
    def list_available_cameras(max_cameras: int = 5) -> list:
        """
        Find available camera indices.
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            List of available camera indices
        """
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
