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
            on_register=self.handle_register,
            on_close=self.handle_close
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
        
        if result.success and result.visitor_id is not None:
            # Known visitor recognized!
            self._welcome_visitor(result.visitor_id, result.visitor_name, display_frame, result.face_location)
        else:
            # Unknown face - prompt for registration
            self.ui.set_status("New visitor detected. Please enter their name below.", "info")
            self.ui.enable_registration(result.face_encoding)
            
            # Show the captured frame with face box
            if result.face_location:
                # Need to mirror the face location since display is mirrored
                top, right, bottom, left = result.face_location
                frame_width = display_frame.shape[1]
                mirrored_location = (top, frame_width - left, bottom, frame_width - right)
                display_frame = draw_face_box(display_frame, mirrored_location, "New Visitor", (255, 165, 0))
            self.ui.update_camera_frame(display_frame)
    
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
    
    def handle_register(self, name: str):
        """
        Handle registration of a new visitor.
        
        Args:
            name: The name entered by the greeter
        """
        encoding = self.ui.get_pending_encoding()
        
        if encoding is None:
            self.ui.set_status("No face captured. Please click Check In first.", "error")
            return
        
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
