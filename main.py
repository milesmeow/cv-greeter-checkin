#!/usr/bin/env python3
"""
Visitor Check-In System

A facial recognition check-in system for religious organizations.
Run this file to start the application.

Usage:
    python main.py
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.camera import Camera, CameraState
from src.recognition import FaceRecognizer, draw_face_box
from src.database import VisitorDatabase, AttendanceLogger
from src.ui import CheckInUI


class CheckInApp:
    """
    Main application controller.
    
    Coordinates between camera, recognition, database, and UI components.
    """
    
    def __init__(self):
        """Initialize all components."""
        print("Initializing Visitor Check-In System...")
        
        # Initialize components
        self.camera = Camera()
        self.recognizer = FaceRecognizer(tolerance=0.6)
        self.database = VisitorDatabase()
        self.logger = AttendanceLogger()
        
        # Initialize UI with callbacks
        self.ui = CheckInUI(
            on_checkin=self.handle_checkin,
            on_close=self.handle_close,
            on_get_visitors=self.get_visitors,
            on_delete_visitor=self.delete_visitor,
            on_get_checkins=self.get_checkins,
            on_get_available_logs=self.get_available_logs,
            on_get_checkins_for_date=self.get_checkins_for_date
        )
        
        # Start camera
        if not self.camera.start():
            print("Warning: Could not start camera. Check-in will not work.")
        
        # Update stats display
        self._update_stats()

        # Warmup state
        self._warmup_attempt = 0
        self._warmup_delay = 100

        # Start camera preview loop
        self._start_preview_loop()

    def _is_frame_valid(self, frame) -> bool:
        """Check if frame is valid for display."""
        if frame is None:
            print("  [DEBUG] Frame is None")
            return False
        if len(frame.shape) != 3:
            print(f"  [DEBUG] Frame has wrong shape: {frame.shape}")
            return False
        import numpy as np
        mean_brightness = np.mean(frame)
        print(f"  [DEBUG] Frame brightness: {mean_brightness:.1f} (valid range: 5-250)")
        return 5 < mean_brightness < 250

    def _start_preview_loop(self):
        """Start the camera preview update loop with warmup and recovery."""

        def do_warmup():
            """Perform camera warmup with user feedback."""
            self.ui.set_camera_status("Connecting to camera...", "info")
            self._warmup_attempt = 0
            self._warmup_delay = 100
            check_warmup()

        def check_warmup():
            """Check if camera is producing valid frames."""
            print(f"[DEBUG] Warmup attempt {self._warmup_attempt + 1}/15, delay={self._warmup_delay}ms")

            if self._warmup_attempt >= 15:
                # Max attempts reached, keep trying at slower rate
                print("[DEBUG] Max warmup attempts reached, switching to slow retry (1s)")
                self.ui.set_camera_status("Camera warming up...", "warning")
                self._warmup_attempt = 0
                self.ui.schedule(check_warmup, 1000)
                return

            frame = self.camera.get_frame_for_display()
            if frame is not None and self._is_frame_valid(frame):
                # Camera ready
                print("[DEBUG] Camera ready! Starting preview loop.")
                self.camera.set_ready()
                self.ui.set_status("Ready - Click 'Check In' when visitor arrives", "info")
                start_preview()
            else:
                # Not ready yet, try again with exponential backoff
                self._warmup_attempt += 1
                self._warmup_delay = min(int(self._warmup_delay * 1.3), 500)
                self.ui.schedule(check_warmup, self._warmup_delay)

        def start_preview():
            """Start the regular preview update loop."""
            def update_preview():
                try:
                    if self.camera.is_running:
                        frame = self.camera.get_frame_for_display()
                        if frame is not None:
                            self.ui.update_camera_frame(frame)
                        elif self.camera.state == CameraState.ERROR:
                            # Camera failed, attempt recovery
                            self.ui.set_camera_status("Camera error - reconnecting...", "error")
                            self.ui.schedule(do_warmup, 1000)
                            return  # Stop this loop, warmup will restart it

                    # Schedule next update (roughly 30 fps)
                    self.ui.schedule(update_preview, 33)
                except Exception as e:
                    print(f"Preview error: {e}")
                    self.ui.schedule(update_preview, 100)

            update_preview()

        # Start with warmup
        if self.camera.is_running:
            self.ui.schedule(do_warmup, 50)
        else:
            self.ui.set_camera_status("Camera not available", "error")
            self.ui.set_status("Camera not available. Check connection and restart.", "error")
    
    def _update_stats(self):
        """Update the statistics display."""
        total_visitors = self.database.get_visitor_count()
        today_checkins = len(self.logger.get_today_checkins())
        self.ui.set_stats(total_visitors, today_checkins)
    
    def handle_checkin(self):
        """
        Handle the Check In button click.
        
        Captures a frame, runs face recognition, and either:
        - Welcomes a known visitor (logs their arrival)
        - Prompts to register an unknown face
        """
        self.ui.set_status("Capturing...", "info")
        
        # Capture frame for recognition
        display_frame, recognition_frame = self.camera.capture_for_recognition()
        
        if recognition_frame is None:
            self.ui.set_status("Camera error. Please check connection.", "error")
            return
        
        # Get all known face encodings from database
        known_encodings = self.database.get_all_encodings()
        
        # Run recognition
        result = self.recognizer.recognize(recognition_frame, known_encodings)
        
        if not result.success and result.face_encoding is None:
            # No face detected
            self.ui.set_status(result.message, "warning")
            return
        
        # Define register callback (used in both flows)
        def on_register(new_name, encoding):
            self._register_new_visitor(new_name, encoding)

        if result.success and result.visitor_id is not None:
            # Known visitor recognized - show confirmation dialog
            def on_confirm():
                self._welcome_visitor(result.visitor_id, result.visitor_name, display_frame, result.face_location)

            self.ui.show_recognition_dialog(
                recognized_name=result.visitor_name,
                encoding=result.face_encoding,
                on_confirm=on_confirm,
                on_register=on_register
            )
        else:
            # Unknown face - show dialog to register
            self.ui.show_recognition_dialog(
                recognized_name=None,
                encoding=result.face_encoding,
                on_confirm=None,
                on_register=on_register
            )
    
    def _welcome_visitor(self, visitor_id: int, name: str, frame, face_location):
        """
        Welcome a recognized visitor.
        
        Args:
            visitor_id: Database ID of the visitor
            name: Visitor's name
            frame: The captured frame for display
            face_location: Where the face was detected
        """
        # Update database
        self.database.record_visit(visitor_id)
        
        # Log the check-in
        self.logger.log_checkin(visitor_id, name, recognized=True)
        
        # Update UI
        self.ui.set_status(f"✓ Welcome back, {name}!", "success")
        self.ui.set_last_checkin(name, datetime.now())
        self._update_stats()
        
        # Show frame with green box around face
        if face_location:
            top, right, bottom, left = face_location
            frame_width = frame.shape[1]
            mirrored_location = (top, frame_width - left, bottom, frame_width - right)
            frame = draw_face_box(frame, mirrored_location, name, (0, 255, 0))
        self.ui.update_camera_frame(frame)
        
        print(f"Check-in: {name} (ID: {visitor_id}) at {datetime.now()}")
    
    def _register_new_visitor(self, name: str, encoding):
        """
        Register a new visitor with the given name and face encoding.

        Args:
            name: The visitor's name
            encoding: The face encoding
        """
        # Add to database
        visitor_id = self.database.add_visitor(name, encoding)

        # Log the check-in
        self.logger.log_checkin(visitor_id, name, recognized=False)

        # Update UI
        self.ui.set_status(f"✓ Registered and checked in: {name}", "success")
        self.ui.set_last_checkin(name, datetime.now())
        self._update_stats()

        print(f"New registration: {name} (ID: {visitor_id}) at {datetime.now()}")
    
    def handle_close(self):
        """Clean up when the application closes."""
        print("Shutting down...")
        self.camera.stop()

    def get_visitors(self) -> list:
        """
        Get all registered visitors for admin display.

        Returns:
            List of visitor dictionaries with id, name, created_at, last_seen, visit_count
        """
        return self.database.get_all_visitors()

    def delete_visitor(self, visitor_id: int, visitor_name: str = None) -> bool:
        """
        Delete a visitor from the database.

        Args:
            visitor_id: The visitor's database ID
            visitor_name: The visitor's name (for logging)

        Returns:
            True if deleted successfully
        """
        # Get visitor name for logging if not provided
        if visitor_name is None:
            visitor = self.database.get_visitor(visitor_id)
            visitor_name = visitor['name'] if visitor else f"Unknown (ID: {visitor_id})"

        result = self.database.delete_visitor(visitor_id)
        if result:
            self.logger.log_deletion(visitor_id, visitor_name)
            self._update_stats()
            print(f"Deleted visitor: {visitor_name} (ID: {visitor_id})")
        return result

    def get_checkins(self) -> list:
        """
        Get today's check-ins for display.

        Returns:
            List of check-in dictionaries with timestamp, visitor_id, visitor_name, recognized
        """
        return self.logger.get_today_checkins()

    def get_available_logs(self) -> list:
        """
        Get list of available log dates.

        Returns:
            List of date strings (YYYY-MM-DD) sorted newest first
        """
        return self.logger.get_available_logs()

    def get_checkins_for_date(self, date_str: str) -> list:
        """
        Get check-ins for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            List of check-in dictionaries
        """
        return self.logger.get_checkins_for_date(date_str)

    def run(self):
        """Start the application."""
        print("Starting UI...")
        print(f"Database: {self.database.get_visitor_count()} registered visitors")
        self.ui.run()


def main():
    """Entry point."""
    try:
        app = CheckInApp()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
