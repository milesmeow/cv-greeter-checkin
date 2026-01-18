"""
User interface module using Tkinter.

Provides the greeter interface for checking in visitors.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import numpy as np
from typing import Callable, Optional, List
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
        on_close: Callable[[], None],
        on_get_visitors: Callable[[], List[dict]] = None,
        on_delete_visitor: Callable[[int], bool] = None,
        on_get_checkins: Callable[[], List[dict]] = None,
        on_get_available_logs: Callable[[], List[str]] = None,
        on_get_checkins_for_date: Callable[[str], List[dict]] = None
    ):
        """
        Initialize the UI.

        Args:
            on_checkin: Callback when Check In button is clicked
            on_close: Callback when window is closed
            on_get_visitors: Callback to get all registered visitors
            on_delete_visitor: Callback to delete a visitor by ID
            on_get_checkins: Callback to get today's check-ins
            on_get_available_logs: Callback to get list of available log dates
            on_get_checkins_for_date: Callback to get check-ins for a specific date
        """
        self.on_checkin = on_checkin
        self.on_close = on_close
        self.on_get_visitors = on_get_visitors
        self.on_delete_visitor = on_delete_visitor
        self.on_get_checkins = on_get_checkins
        self.on_get_available_logs = on_get_available_logs
        self.on_get_checkins_for_date = on_get_checkins_for_date

        # Create main window
        self.root = tk.Tk()
        self.root.title("Visitor Check-In")
        self.root.geometry("800x800")
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
        # Two-column layout: main content (centered) + admin sidebar (right)
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Right sidebar for admin button
        sidebar = ttk.Frame(content_frame, padding=10)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, anchor=tk.N)

        self.admin_btn = ttk.Button(
            sidebar,
            text="Manage\nVisitors",
            style='Register.TButton',
            command=self._show_admin_dialog
        )
        self.admin_btn.pack(anchor=tk.N)

        self.history_btn = ttk.Button(
            sidebar,
            text="Today's\nCheck-ins",
            style='Register.TButton',
            command=self._show_history_dialog
        )
        self.history_btn.pack(anchor=tk.N, pady=(10, 0))

        self.browse_btn = ttk.Button(
            sidebar,
            text="Browse\nHistory",
            style='Register.TButton',
            command=self._show_history_browser
        )
        self.browse_btn.pack(anchor=tk.N, pady=(10, 0))

        # Spacer to push quit button to bottom
        spacer = ttk.Frame(sidebar)
        spacer.pack(fill=tk.Y, expand=True)

        # Quit button at bottom
        self.quit_btn = ttk.Button(
            sidebar,
            text="Quit",
            style='Register.TButton',
            command=self._handle_close
        )
        self.quit_btn.pack(anchor=tk.S, pady=(10, 0))

        # Create canvas with scrollbar for scrollable main content
        canvas = tk.Canvas(content_frame)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)

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

    def _show_admin_dialog(self):
        """Show the visitor management dialog."""
        if self.on_get_visitors and self.on_delete_visitor:
            AdminDialog(
                parent=self.root,
                on_get_visitors=self.on_get_visitors,
                on_delete_visitor=self.on_delete_visitor
            )

    def _show_history_dialog(self):
        """Show the check-in history dialog."""
        if self.on_get_checkins:
            CheckInHistoryDialog(
                parent=self.root,
                on_get_checkins=self.on_get_checkins
            )

    def _show_history_browser(self):
        """Show the history browser dialog."""
        if self.on_get_available_logs and self.on_get_checkins_for_date:
            HistoryBrowserDialog(
                parent=self.root,
                on_get_available_logs=self.on_get_available_logs,
                on_get_checkins_for_date=self.on_get_checkins_for_date
            )

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


class AdminDialog:
    """
    Modal dialog for managing registered visitors.

    Displays a list of visitors with details and allows deletion.
    """

    def __init__(
        self,
        parent: tk.Tk,
        on_get_visitors: Callable[[], List[dict]],
        on_delete_visitor: Callable[[int], bool]
    ):
        """
        Initialize the admin dialog.

        Args:
            parent: Parent window
            on_get_visitors: Callback to get visitor list
            on_delete_visitor: Callback to delete a visitor by ID
        """
        self.on_get_visitors = on_get_visitors
        self.on_delete_visitor = on_delete_visitor

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Visitors")
        self.dialog.geometry("600x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center over parent
        self.dialog.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 100}")

        self._build_ui()
        self._load_visitors()

    def _build_ui(self):
        """Construct the dialog UI."""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(
            main_frame,
            text="Registered Visitors",
            font=('Helvetica', 14, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))

        # Treeview frame (for scrollbar)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview with columns
        columns = ('id', 'name', 'registered', 'last_seen', 'visits')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

        # Define headings
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Name')
        self.tree.heading('registered', text='Registered')
        self.tree.heading('last_seen', text='Last Seen')
        self.tree.heading('visits', text='Visits')

        # Define column widths
        self.tree.column('id', width=40, anchor='center')
        self.tree.column('name', width=180)
        self.tree.column('registered', width=120)
        self.tree.column('last_seen', width=120)
        self.tree.column('visits', width=60, anchor='center')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=('Helvetica', 10),
            foreground='gray'
        )
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        # Delete button (disabled by default)
        self.delete_btn = ttk.Button(
            btn_frame,
            text="Delete Selected",
            command=self._on_delete,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT)

        # Close button
        ttk.Button(
            btn_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

    def _load_visitors(self):
        """Load visitors from database and populate the Treeview."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get visitors
        visitors = self.on_get_visitors()

        # Populate treeview
        for visitor in visitors:
            self.tree.insert('', tk.END, values=(
                visitor['id'],
                visitor['name'],
                self._format_date(visitor['created_at']),
                self._format_date(visitor['last_seen']),
                visitor['visit_count']
            ))

        # Update status
        count = len(visitors)
        self.status_label.configure(
            text=f"Total: {count} visitor{'s' if count != 1 else ''}"
        )

        # Reset delete button state
        self.delete_btn.configure(state=tk.DISABLED)

    def _format_date(self, date_str: str) -> str:
        """Format a database timestamp for display."""
        if not date_str:
            return "Never"
        try:
            dt = datetime.fromisoformat(date_str)
            today = datetime.now().date()
            if dt.date() == today:
                return "Today"
            elif (today - dt.date()).days == 1:
                return "Yesterday"
            else:
                return dt.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            return str(date_str)

    def _on_select(self, event):
        """Handle Treeview selection change."""
        selected = self.tree.selection()
        if selected:
            self.delete_btn.configure(state=tk.NORMAL)
        else:
            self.delete_btn.configure(state=tk.DISABLED)

    def _on_delete(self):
        """Handle delete button click."""
        selected = self.tree.selection()
        if not selected:
            return

        # Get visitor info
        item = self.tree.item(selected[0])
        values = item['values']
        visitor_id = values[0]
        visitor_name = values[1]

        # Confirm deletion
        if messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{visitor_name}'?\n\nThis cannot be undone.",
            parent=self.dialog
        ):
            if self.on_delete_visitor(visitor_id):
                self._load_visitors()  # Refresh list


class CheckInHistoryDialog:
    """
    Modal dialog for viewing today's check-in history.
    """

    def __init__(
        self,
        parent: tk.Tk,
        on_get_checkins: Callable[[], List[dict]]
    ):
        """
        Initialize the check-in history dialog.

        Args:
            parent: Parent window
            on_get_checkins: Callback to get today's check-ins
        """
        self.on_get_checkins = on_get_checkins

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Today's Check-ins")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center over parent
        self.dialog.geometry(f"+{parent.winfo_x() + 100}+{parent.winfo_y() + 100}")

        self._build_ui()
        self._load_checkins()

    def _build_ui(self):
        """Construct the dialog UI."""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with date
        today = datetime.now().strftime("%A, %B %d, %Y")
        ttk.Label(
            main_frame,
            text=f"Check-ins for {today}",
            font=('Helvetica', 14, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))

        # Treeview frame (for scrollbar)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview with columns
        columns = ('time', 'name', 'type')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

        # Define headings
        self.tree.heading('time', text='Time')
        self.tree.heading('name', text='Visitor')
        self.tree.heading('type', text='Type')

        # Define column widths
        self.tree.column('time', width=100)
        self.tree.column('name', width=200)
        self.tree.column('type', width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=('Helvetica', 10),
            foreground='gray'
        )
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        # Close button
        ttk.Button(
            btn_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

    def _load_checkins(self):
        """Load check-ins and populate the Treeview."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get check-ins
        checkins = self.on_get_checkins()

        # Populate treeview (most recent first)
        for checkin in reversed(checkins):
            # Format time from timestamp
            time_str = self._format_time(checkin['timestamp'])
            check_type = "Check In" if checkin['recognized'] else "Registered"

            self.tree.insert('', tk.END, values=(
                time_str,
                checkin['visitor_name'],
                check_type
            ))

        # Update status
        count = len(checkins)
        self.status_label.configure(
            text=f"Total: {count} check-in{'s' if count != 1 else ''} today"
        )

    def _format_time(self, timestamp_str: str) -> str:
        """Format a timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace(" ", "T"))
            return dt.strftime("%I:%M %p")
        except (ValueError, TypeError):
            return timestamp_str


class HistoryBrowserDialog:
    """
    Modal dialog for browsing historical check-in logs.
    """

    def __init__(
        self,
        parent: tk.Tk,
        on_get_available_logs: Callable[[], List[str]],
        on_get_checkins_for_date: Callable[[str], List[dict]]
    ):
        """
        Initialize the history browser dialog.

        Args:
            parent: Parent window
            on_get_available_logs: Callback to get list of available log dates
            on_get_checkins_for_date: Callback to get check-ins for a specific date
        """
        self.on_get_available_logs = on_get_available_logs
        self.on_get_checkins_for_date = on_get_checkins_for_date

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Browse Check-in History")
        self.dialog.geometry("650x450")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center over parent
        self.dialog.geometry(f"+{parent.winfo_x() + 75}+{parent.winfo_y() + 75}")

        self._build_ui()
        self._load_available_dates()

    def _build_ui(self):
        """Construct the dialog UI."""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(
            main_frame,
            text="Browse Check-in History",
            font=('Helvetica', 14, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))

        # Content frame - two panes
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left pane - date list
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(
            left_frame,
            text="Available Dates:",
            font=('Helvetica', 10, 'bold')
        ).pack(anchor=tk.W)

        # Date listbox with scrollbar
        date_frame = ttk.Frame(left_frame)
        date_frame.pack(fill=tk.Y, expand=True, pady=(5, 0))

        self.date_listbox = tk.Listbox(date_frame, width=15, height=15)
        date_scrollbar = ttk.Scrollbar(date_frame, orient=tk.VERTICAL, command=self.date_listbox.yview)
        self.date_listbox.configure(yscrollcommand=date_scrollbar.set)

        self.date_listbox.pack(side=tk.LEFT, fill=tk.Y)
        date_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.date_listbox.bind('<<ListboxSelect>>', self._on_date_select)

        # Right pane - check-ins for selected date
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.date_label = ttk.Label(
            right_frame,
            text="Select a date to view check-ins",
            font=('Helvetica', 10, 'bold')
        )
        self.date_label.pack(anchor=tk.W)

        # Treeview for check-ins
        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        columns = ('time', 'name', 'type')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

        self.tree.heading('time', text='Time')
        self.tree.heading('name', text='Visitor')
        self.tree.heading('type', text='Type')

        self.tree.column('time', width=80)
        self.tree.column('name', width=180)
        self.tree.column('type', width=100)

        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=('Helvetica', 10),
            foreground='gray'
        )
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            btn_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

    def _load_available_dates(self):
        """Load available log dates into the listbox."""
        dates = self.on_get_available_logs()

        self.date_listbox.delete(0, tk.END)
        for date_str in dates:
            # Format date for display
            display_date = self._format_date_for_list(date_str)
            self.date_listbox.insert(tk.END, display_date)

        # Store the raw dates for lookup
        self._date_map = {self._format_date_for_list(d): d for d in dates}

        if not dates:
            self.status_label.configure(text="No check-in logs found")

    def _format_date_for_list(self, date_str: str) -> str:
        """Format a date string for display in the list."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%b %d, %Y")
        except ValueError:
            return date_str

    def _on_date_select(self, event):
        """Handle date selection."""
        selection = self.date_listbox.curselection()
        if not selection:
            return

        display_date = self.date_listbox.get(selection[0])
        date_str = self._date_map.get(display_date, display_date)

        # Update header
        self.date_label.configure(text=f"Check-ins for {display_date}:")

        # Load check-ins for this date
        self._load_checkins_for_date(date_str)

    def _load_checkins_for_date(self, date_str: str):
        """Load check-ins for a specific date."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get check-ins
        checkins = self.on_get_checkins_for_date(date_str)

        # Populate treeview (most recent first)
        for checkin in reversed(checkins):
            time_str = self._format_time(checkin['timestamp'])
            check_type = "Check In" if checkin['recognized'] else "Registered"

            self.tree.insert('', tk.END, values=(
                time_str,
                checkin['visitor_name'],
                check_type
            ))

        # Update status
        count = len(checkins)
        self.status_label.configure(
            text=f"Total: {count} check-in{'s' if count != 1 else ''}"
        )

    def _format_time(self, timestamp_str: str) -> str:
        """Format a timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace(" ", "T"))
            return dt.strftime("%I:%M %p")
        except (ValueError, TypeError):
            return timestamp_str
