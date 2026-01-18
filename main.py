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

from src.camera import Camera
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
        
        # Start camera preview loop
        self._start_preview_loop()
    
    def _start_preview_loop(self):
        """Start the camera preview update loop."""
        def update_preview():
            if self.camera.is_running:
                frame = self.camera.get_frame_for_display()
                if frame is not None:
                    self.ui.update_camera_frame(frame)
            
            # Schedule next update (roughly 30 fps)
            self.ui.schedule(update_preview, 33)
        
        # Start the loop
        self.ui.schedule(update_preview, 100)
    
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

    def delete_visitor(self, visitor_id: int) -> bool:
        """
        Delete a visitor from the database.

        Args:
            visitor_id: The visitor's database ID

        Returns:
            True if deleted successfully
        """
        result = self.database.delete_visitor(visitor_id)
        if result:
            self._update_stats()
            print(f"Deleted visitor ID: {visitor_id}")
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
