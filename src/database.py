"""
Database module for visitor storage.

Handles all SQLite operations for storing and retrieving visitor data,
including face encodings and visit history.
"""

import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np


class VisitorDatabase:
    """Manages the local SQLite database for visitor records."""
    
    def __init__(self, db_path: str = "data/visitors.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS visitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    face_encoding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    visit_count INTEGER DEFAULT 1
                )
            """)
            conn.commit()
    
    def add_visitor(self, name: str, face_encoding: np.ndarray) -> int:
        """
        Add a new visitor to the database.
        
        Args:
            name: Visitor's name
            face_encoding: 128-dimensional face encoding array
            
        Returns:
            The new visitor's ID
        """
        encoding_blob = pickle.dumps(face_encoding)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO visitors (name, face_encoding) VALUES (?, ?)",
                (name, encoding_blob)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_all_encodings(self) -> List[Tuple[int, str, np.ndarray]]:
        """
        Retrieve all visitor encodings for comparison.
        
        Returns:
            List of tuples: (visitor_id, name, face_encoding)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, name, face_encoding FROM visitors"
            )
            results = []
            for row in cursor.fetchall():
                visitor_id, name, encoding_blob = row
                encoding = pickle.loads(encoding_blob)
                results.append((visitor_id, name, encoding))
            return results
    
    def record_visit(self, visitor_id: int):
        """
        Update last_seen and increment visit_count for a visitor.
        
        Args:
            visitor_id: The visitor's database ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE visitors 
                SET last_seen = ?, visit_count = visit_count + 1 
                WHERE id = ?
                """,
                (datetime.now(), visitor_id)
            )
            conn.commit()
    
    def get_visitor(self, visitor_id: int) -> Optional[dict]:
        """
        Get visitor details by ID.
        
        Args:
            visitor_id: The visitor's database ID
            
        Returns:
            Dictionary with visitor info, or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, name, created_at, last_seen, visit_count FROM visitors WHERE id = ?",
                (visitor_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_visitors(self) -> List[dict]:
        """
        Get all visitors (without encodings, for display purposes).
        
        Returns:
            List of visitor dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, name, created_at, last_seen, visit_count FROM visitors ORDER BY name"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_visitor(self, visitor_id: int) -> bool:
        """
        Remove a visitor from the database.
        
        Args:
            visitor_id: The visitor's database ID
            
        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM visitors WHERE id = ?",
                (visitor_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_visitor_count(self) -> int:
        """Get total number of registered visitors."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM visitors")
            return cursor.fetchone()[0]


class AttendanceLogger:
    """Logs check-in events to CSV files for easy export."""
    
    def __init__(self, log_dir: str = "data/logs"):
        """
        Initialize the attendance logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_path(self) -> Path:
        """Get today's log file path."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"attendance_{today}.csv"
    
    def log_checkin(self, visitor_id: int, visitor_name: str, recognized: bool):
        """
        Log a check-in event.
        
        Args:
            visitor_id: The visitor's database ID
            visitor_name: The visitor's name
            recognized: Whether this was a recognized visitor or new registration
        """
        log_path = self._get_log_path()
        
        # Write header if new file
        write_header = not log_path.exists()
        
        with open(log_path, "a") as f:
            if write_header:
                f.write("timestamp,visitor_id,visitor_name,recognized\n")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp},{visitor_id},{visitor_name},{recognized}\n")
    
    def get_today_checkins(self) -> List[dict]:
        """
        Get all check-ins from today.

        Returns:
            List of check-in records
        """
        log_path = self._get_log_path()
        return self._parse_log_file(log_path)

    def get_available_logs(self) -> List[str]:
        """
        Get list of available log dates.

        Returns:
            List of date strings (YYYY-MM-DD) sorted newest first
        """
        dates = []
        for log_file in self.log_dir.glob("attendance_*.csv"):
            # Extract date from filename: attendance_YYYY-MM-DD.csv
            date_str = log_file.stem.replace("attendance_", "")
            dates.append(date_str)
        return sorted(dates, reverse=True)

    def get_checkins_for_date(self, date_str: str) -> List[dict]:
        """
        Get check-ins for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            List of check-in records
        """
        log_path = self.log_dir / f"attendance_{date_str}.csv"
        return self._parse_log_file(log_path)

    def _parse_log_file(self, log_path: Path) -> List[dict]:
        """
        Parse a log file and return check-in records.

        Args:
            log_path: Path to the log file

        Returns:
            List of check-in records
        """
        if not log_path.exists():
            return []

        checkins = []
        with open(log_path, "r") as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) == 4:
                    checkins.append({
                        "timestamp": parts[0],
                        "visitor_id": int(parts[1]),
                        "visitor_name": parts[2],
                        "recognized": parts[3].lower() == "true"
                    })

        return checkins
