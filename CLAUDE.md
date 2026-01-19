# CLAUDE.md

This file provides guidance to Claude Code for working on this project.

## Project Overview

A facial recognition visitor check-in system for a religious organization. A greeter at the front door uses this app to check in arriving visitors. The system recognizes known visitors and allows registration of new ones.

**Key constraint:** Greeter-controlled (not automatic scanning). The greeter clicks a button to initiate each check-in.

## Tech Stack

- **Python 3.9+**
- **face_recognition** - Face detection and encoding (wrapper around dlib)
- **OpenCV** - Camera capture
- **Tkinter** - GUI (built into Python)
- **SQLite** - Local database for visitor records
- **Pillow** - Image conversion for display

## Project Structure

```
visitor-checkin/
├── main.py              # Entry point - run this to start the app
├── requirements.txt     # Python dependencies
├── CLAUDE.md           # This file
├── CLAUDE_CONTEXT.md   # Detailed architecture docs
├── README.md           # User-facing documentation
│
├── src/
│   ├── camera.py       # Webcam capture with state machine & retry logic
│   ├── recognition.py  # Face detection & matching
│   ├── database.py     # SQLite + CSV logging (incl. deletion events)
│   └── ui.py           # Tkinter interface + admin modal dialogs
│
├── data/               # Created at runtime
│   ├── visitors.db     # SQLite database
│   └── logs/           # Daily attendance CSVs
│
└── tests/
    └── test_recognition.py
```

## Quick Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run the app
python main.py

# Run tests
python -m pytest tests/ -v
```

## Installing Dependencies

The `face_recognition` library requires `dlib`, which needs a C++ compiler.

### macOS
```bash
brew install cmake
pip install -r requirements.txt
```

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install build-essential cmake python3-dev
pip install -r requirements.txt
```

### Windows
Easiest approach - use pre-built wheels:
```bash
pip install cmake
pip install dlib
pip install face_recognition
pip install opencv-python pillow numpy
```

If dlib fails, try: `pip install dlib --prefer-binary`

Or use conda: `conda install -c conda-forge dlib`

## Architecture Notes

### Data Flow
```
User clicks "Check In"
    → camera.py captures frame
    → recognition.py detects face & creates encoding
    → database.py compares against stored encodings
    → ui.py displays result
    → database.py logs the visit
```

### Camera State Machine
The camera uses a state machine for reliable initialization:
```
CameraState: DISCONNECTED → CONNECTING → WARMING_UP → READY
                                                    ↘ ERROR
```
- **Warmup phase**: Requires 3 consecutive successful frame reads before marking ready
- **Retry logic**: Up to 20 attempts with 100ms delays (helps with macOS camera quirks)
- **Frame validation**: Checks brightness, dimensions, and validity before display/processing
- **Graceful degradation**: Continues even if warmup incomplete

### Admin Tools
Three modal dialogs accessible from the sidebar:
- **Manage Visitors** (`AdminDialog`): View/delete registered visitors
- **Today's Check-ins** (`CheckInHistoryDialog`): View today's activity
- **Browse History** (`HistoryBrowserDialog`): Browse check-ins by date

### Modal Architecture
All modals follow a consistent pattern:
- Use `tk.Toplevel()` with `transient()` and `grab_set()` for modal behavior
- Callback-based data retrieval from main app
- Auto-center over parent window

### Face Encodings
- 128-dimensional numpy arrays
- Stored as pickled BLOBs in SQLite
- Compared using Euclidean distance
- Tolerance threshold: 0.6 (adjustable in recognition.py)

### Database Schema
```sql
visitors (
    id INTEGER PRIMARY KEY,
    name TEXT,
    face_encoding BLOB,  -- pickled numpy array
    created_at TIMESTAMP,
    last_seen TIMESTAMP,
    visit_count INTEGER
)
```

## Common Tasks

### Add a new feature to the UI
Edit `src/ui.py`. The main class is `CheckInUI`. Add new widgets in `_build_ui()` method.

### Add a new admin dialog
1. Create a new class inheriting from `tk.Toplevel` in `src/ui.py`
2. Follow the modal pattern: `transient(parent)`, `grab_set()`, center over parent
3. Add callback parameter for data retrieval
4. Add button in sidebar (`_build_sidebar()`) to open the dialog
5. Wire up the callback in `main.py`

### Change recognition sensitivity
In `src/recognition.py`, adjust `tolerance` parameter in `FaceRecognizer.__init__()`. Lower = stricter matching.

### Add a new database field
1. Update schema in `database.py` `_init_db()`
2. Update relevant methods (add_visitor, get_visitor, etc.)
3. Consider migration for existing databases

### Export attendance data
The `AttendanceLogger` class in `database.py` writes daily CSVs to `data/logs/`. Format:
```
timestamp,visitor_id,visitor_name,action
```
Action types: `checkin`, `register`, `delete`

### Test without a camera
Mock the camera in tests or use static images:
```python
import face_recognition
image = face_recognition.load_image_file("test_photo.jpg")
```

## Code Style

- Type hints on function signatures
- Docstrings on classes and public methods
- Keep UI callbacks thin - business logic in main.py
- Log important events to console with print()

## Known Limitations

1. Single camera only (camera index 0)
2. One face at a time (rejects frames with multiple faces)
3. No photo storage (only encodings) - can't show visitor photos
4. No network features - fully local

## Future Enhancements (if user requests)

- Multiple camera support
- Attendance reports / Excel export
- Visitor photos (optional)
- Kiosk mode (auto-scan)
- Sound notifications
- Adjustable tolerance slider in UI
- Visitor notes/tags

## Troubleshooting

### "No module named 'face_recognition'"
Install failed. Check C++ compiler and cmake are installed, then retry pip install.

### "Could not open camera" / Camera black screen
- Check camera permissions (especially macOS)
- Try different camera_index in Camera() constructor
- Close other apps using the camera
- The camera has built-in warmup logic - wait for "READY" state
- Check debug output for frame validation failures

### Recognition too strict/lenient
Adjust tolerance in `FaceRecognizer(tolerance=0.6)`. Range 0.4-0.8 typical.

### Slow recognition
- Normal on first run (model loading)
- Consider reducing frame size before recognition
- Intel Core Ultra with NPU will help

## Testing Checklist

Before deploying:
- [ ] Camera preview works (waits for warmup)
- [ ] Can register a new visitor
- [ ] Recognizes registered visitor on return
- [ ] Attendance log CSV is created
- [ ] App closes cleanly
- [ ] Works after restart (database persists)
- [ ] Admin: Can view visitor list
- [ ] Admin: Can delete a visitor
- [ ] Admin: Can view today's check-ins
- [ ] Admin: Can browse history by date
