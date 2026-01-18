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
        on_close: Callable[[], None]
    ):
        """
        Initialize the UI.

        Args:
            on_checkin: Callback when Check In button is clicked
            on_close: Callback when window is closed
        """
        self.on_checkin = on_checkin
        self.on_close = on_close

        # Create main window
        self.root = tk.Tk()
        self.root.title("Visitor Check-In")
        self.root.geometry("700x750")
        self.root.resizable(True, True)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

        # Style configuration
        self._setup_styles()

        # Build UI components
        self._build_ui()

        # State
        self._current_frame: Optional[ImageTk.PhotoImage] = None
    
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
        # Create canvas with scrollbar for scrollable content
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)

        # Main container with padding (inside canvas)
        main_frame = ttk.Frame(canvas, padding=20)

        # Configure canvas scrolling
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

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
    
    def _handle_checkin(self):
        """Handle Check In button click."""
        self.on_checkin()

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

    def show_recognition_dialog(
        self,
        recognized_name: Optional[str],
        encoding: np.ndarray,
        on_confirm: Optional[Callable[[], None]],
        on_register: Callable[[str, np.ndarray], None]
    ):
        """
        Show a dialog after face detection.

        Args:
            recognized_name: The recognized visitor's name, or None if not recognized
            encoding: The face encoding
            on_confirm: Callback when user confirms the recognition (only if recognized)
            on_register: Callback to register a new person (passes name, encoding)
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Check In")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center over main window
        dialog.geometry(f"+{self.root.winfo_x() + 150}+{self.root.winfo_y() + 200}")

        # Main frame with padding
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        if recognized_name:
            # RECOGNIZED FLOW
            ttk.Label(
                frame,
                text=f"Recognized: {recognized_name}",
                font=('Helvetica', 16, 'bold'),
                foreground='green'
            ).pack(pady=(0, 15))

            # OK button
            def handle_confirm():
                dialog.destroy()
                on_confirm()

            ok_btn = ttk.Button(
                frame,
                text="✓  OK - Check In",
                style='CheckIn.TButton',
                command=handle_confirm
            )
            ok_btn.pack(pady=(0, 15))
            ok_btn.focus_set()

            # Bind Enter key to confirm
            dialog.bind('<Return>', lambda e: handle_confirm())

            # Separator
            ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)

            # "Not correct?" section
            ttk.Label(
                frame,
                text="Not correct?",
                font=('Helvetica', 10),
                foreground='gray'
            ).pack()
        else:
            # NOT RECOGNIZED FLOW
            ttk.Label(
                frame,
                text="Not Recognized",
                font=('Helvetica', 16, 'bold'),
                foreground='red'
            ).pack(pady=(0, 10))

            ttk.Label(
                frame,
                text="Face not recognized. Please enter name to register.",
                font=('Helvetica', 11),
                foreground='gray'
            ).pack(pady=(0, 15))

        # Name entry and register button (shown in both cases)
        reg_frame = ttk.Frame(frame)
        reg_frame.pack(fill=tk.X, pady=10)

        ttk.Label(reg_frame, text="Name:").pack(side=tk.LEFT, padx=5)

        name_entry = ttk.Entry(reg_frame, width=20, font=('Helvetica', 12))
        name_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        def handle_register():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Name Required", "Please enter the visitor's name.", parent=dialog)
                return
            dialog.destroy()
            on_register(new_name, encoding)

        reg_btn = ttk.Button(
            reg_frame,
            text="Register",
            command=handle_register
        )
        reg_btn.pack(side=tk.LEFT, padx=5)

        # If not recognized, focus on name entry and bind Enter to register
        if not recognized_name:
            name_entry.focus_set()
            dialog.bind('<Return>', lambda e: handle_register())

        # Cancel button
        def handle_cancel():
            dialog.destroy()

        ttk.Button(
            frame,
            text="Cancel",
            command=handle_cancel
        ).pack(pady=(15, 0))
