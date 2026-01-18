"""
User interface module using Tkinter.

Provides the greeter interface for checking in visitors.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
from typing import Callable, Optional
from datetime import datetime


class CheckInUI:
    """
    Main application window for the visitor check-in system.
    
    Layout:
    - Camera preview at top
    - Check-in button
    - Status/result display
    - New visitor registration section
    """
    
    def __init__(
        self,
        on_checkin: Callable[[], None],
        on_register: Callable[[str], None],
        on_close: Callable[[], None]
    ):
        """
        Initialize the UI.
        
        Args:
            on_checkin: Callback when Check In button is clicked
            on_register: Callback when Register button is clicked (passes name)
            on_close: Callback when window is closed
        """
        self.on_checkin = on_checkin
        self.on_register = on_register
        self.on_close = on_close
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Visitor Check-In")
        self.root.geometry("700x700")
        self.root.resizable(False, False)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)
        
        # Style configuration
        self._setup_styles()
        
        # Build UI components
        self._build_ui()
        
        # State
        self._current_frame: Optional[ImageTk.PhotoImage] = None
        self._pending_encoding: Optional[np.ndarray] = None
    
    def _setup_styles(self):
        """Configure ttk styles for a clean look."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure(
            'CheckIn.TButton',
            font=('Helvetica', 16, 'bold'),
            padding=15
        )
        style.configure(
            'Register.TButton',
            font=('Helvetica', 12),
            padding=8
        )
        
        # Label styles
        style.configure(
            'Status.TLabel',
            font=('Helvetica', 14),
            padding=10
        )
        style.configure(
            'Header.TLabel',
            font=('Helvetica', 18, 'bold'),
            padding=10
        )
    
    def _build_ui(self):
        """Construct all UI elements."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(
            main_frame,
            text="Visitor Check-In",
            style='Header.TLabel'
        )
        header.pack()
        
        # Camera preview frame
        self.camera_frame = ttk.Frame(main_frame, relief='sunken', borderwidth=2)
        self.camera_frame.pack(pady=10)
        
        self.camera_label = ttk.Label(self.camera_frame)
        self.camera_label.pack()
        
        # Placeholder for camera
        self._show_placeholder()
        
        # Check-in button
        self.checkin_btn = ttk.Button(
            main_frame,
            text="📸  Check In",
            style='CheckIn.TButton',
            command=self._handle_checkin
        )
        self.checkin_btn.pack(pady=15)
        
        # Status display
        status_frame = ttk.Frame(main_frame, relief='groove', borderwidth=1)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready - Click 'Check In' when visitor arrives",
            style='Status.TLabel',
            wraplength=600
        )
        self.status_label.pack()
        
        # Last check-in info
        self.last_checkin_label = ttk.Label(
            status_frame,
            text="",
            font=('Helvetica', 10),
            foreground='gray'
        )
        self.last_checkin_label.pack()
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # New visitor registration section
        reg_frame = ttk.LabelFrame(main_frame, text="New Visitor Registration", padding=10)
        reg_frame.pack(fill=tk.X)
        
        # Name entry
        name_frame = ttk.Frame(reg_frame)
        name_frame.pack(fill=tk.X)
        
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT, padx=5)
        
        self.name_entry = ttk.Entry(name_frame, width=30, font=('Helvetica', 12))
        self.name_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.register_btn = ttk.Button(
            name_frame,
            text="Register",
            style='Register.TButton',
            command=self._handle_register,
            state='disabled'
        )
        self.register_btn.pack(side=tk.LEFT, padx=5)
        
        # Registration hint
        self.reg_hint = ttk.Label(
            reg_frame,
            text="First capture face with 'Check In', then enter name and click 'Register'",
            font=('Helvetica', 9),
            foreground='gray'
        )
        self.reg_hint.pack(pady=5)
        
        # Stats at bottom
        self.stats_label = ttk.Label(
            main_frame,
            text="",
            font=('Helvetica', 9),
            foreground='gray'
        )
        self.stats_label.pack(side=tk.BOTTOM, pady=10)
    
    def _show_placeholder(self):
        """Show placeholder when camera not active."""
        # Create a gray placeholder image
        placeholder = Image.new('RGB', (640, 480), color=(200, 200, 200))
        self._current_frame = ImageTk.PhotoImage(placeholder)
        self.camera_label.configure(image=self._current_frame)
    
    def update_camera_frame(self, frame: np.ndarray):
        """
        Update the camera preview with a new frame.
        
        Args:
            frame: RGB image as numpy array
        """
        # Convert to PIL Image
        image = Image.fromarray(frame)
        
        # Resize if needed
        image = image.resize((640, 480), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage for Tkinter
        self._current_frame = ImageTk.PhotoImage(image)
        self.camera_label.configure(image=self._current_frame)
    
    def set_status(self, message: str, status_type: str = "info"):
        """
        Update the status message.
        
        Args:
            message: Status text to display
            status_type: "info", "success", "warning", or "error"
        """
        colors = {
            "info": "black",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        self.status_label.configure(
            text=message,
            foreground=colors.get(status_type, "black")
        )
    
    def set_last_checkin(self, name: str, time: datetime):
        """
        Update the last check-in display.
        
        Args:
            name: Visitor name
            time: Check-in time
        """
        time_str = time.strftime("%I:%M %p")
        self.last_checkin_label.configure(
            text=f"Last check-in: {name} at {time_str}"
        )
    
    def set_stats(self, total_visitors: int, today_checkins: int):
        """
        Update the stats display.
        
        Args:
            total_visitors: Total registered visitors
            today_checkins: Number of check-ins today
        """
        self.stats_label.configure(
            text=f"Registered visitors: {total_visitors}  |  Today's check-ins: {today_checkins}"
        )
    
    def enable_registration(self, encoding: np.ndarray):
        """
        Enable the registration section for a new visitor.
        
        Args:
            encoding: The face encoding to register
        """
        self._pending_encoding = encoding
        self.register_btn.configure(state='normal')
        self.name_entry.focus_set()
        self.reg_hint.configure(
            text="Face captured! Enter the visitor's name and click 'Register'",
            foreground='green'
        )
    
    def disable_registration(self):
        """Disable the registration section."""
        self._pending_encoding = None
        self.register_btn.configure(state='disabled')
        self.name_entry.delete(0, tk.END)
        self.reg_hint.configure(
            text="First capture face with 'Check In', then enter name and click 'Register'",
            foreground='gray'
        )
    
    def get_pending_encoding(self) -> Optional[np.ndarray]:
        """Get the face encoding waiting to be registered."""
        return self._pending_encoding
    
    def _handle_checkin(self):
        """Handle Check In button click."""
        self.disable_registration()
        self.on_checkin()
    
    def _handle_register(self):
        """Handle Register button click."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name Required", "Please enter the visitor's name.")
            return
        
        self.on_register(name)
        self.disable_registration()
    
    def _handle_close(self):
        """Handle window close."""
        self.on_close()
        self.root.destroy()
    
    def run(self):
        """Start the UI event loop."""
        self.root.mainloop()
    
    def schedule(self, callback: Callable, delay_ms: int = 0):
        """
        Schedule a callback to run in the UI thread.
        
        Args:
            callback: Function to call
            delay_ms: Delay in milliseconds
        """
        self.root.after(delay_ms, callback)
