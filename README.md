# Visitor Check-In System

A simple facial recognition check-in system for religious organizations. Designed to run locally on a single machine with no cloud backend required.

## Features

- **Greeter-controlled**: Click a button to capture and recognize visitors
- **Face recognition**: Identifies known visitors and displays their name
- **Arrival logging**: Timestamps every check-in
- **New visitor registration**: Simple flow to add new faces to the database
- **Fully local**: All data stays on your machine

## Requirements

- Python 3.9+
- Webcam (built-in or external)
- Windows, macOS, or Linux

## Quick Start

### Prerequisites

The `face_recognition` library requires `dlib`, which needs cmake and a C++ compiler:

**macOS:**
```bash
brew install cmake
```

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential cmake python3-dev
```

**Windows:**
```bash
pip install cmake
```

### Installation

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

## Project Structure

```
visitor-checkin/
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── CLAUDE_CONTEXT.md   # Context for Claude Code to understand the project
│
├── src/
│   ├── __init__.py
│   ├── camera.py       # Webcam capture handling
│   ├── recognition.py  # Face detection & recognition logic
│   ├── database.py     # Local SQLite database for visitors
│   └── ui.py           # User interface (tkinter)
│
├── data/               # Created at runtime
│   ├── visitors.db     # SQLite database
│   ├── faces/          # Stored face encodings
│   └── logs/           # Check-in logs (CSV)
│
└── tests/
    └── test_recognition.py
```

## How It Works

1. **Greeter clicks "Check In"** → Camera captures a frame
2. **Face detection** → Finds faces in the image using dlib/face_recognition
3. **Face encoding** → Converts face to a 128-dimension vector
4. **Database lookup** → Compares against stored encodings
5. **Result displayed** → Shows name if recognized, or prompts to register

## Technology Choices

- **face_recognition library**: Built on dlib, good accuracy, easy to use
- **SQLite**: Simple local database, no server needed
- **Tkinter**: Built into Python, no extra dependencies for UI
- **OpenCV**: Camera capture and image processing

## Privacy Notes

- All data stored locally in `data/` directory
- Face encodings are mathematical representations, not photos
- Original photos are not stored (only encodings)
- Easy to delete individual visitors or wipe all data

## Future Enhancements (TODO)

- [ ] Multiple camera support
- [ ] Export attendance reports
- [ ] Visitor notes/tags
- [ ] Automatic camera detection on startup
- [ ] Kiosk mode (auto-scan without button click)
