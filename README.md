# Visitor Check-In System

A simple facial recognition check-in system for religious organizations. Designed to run locally on a single machine with no cloud backend required.

## Features

- **Greeter-controlled**: Click a button to capture and recognize visitors
- **Face recognition**: Identifies known visitors and displays their name
- **Arrival logging**: Timestamps every check-in
- **New visitor registration**: Simple flow to add new faces to the database
- **Fully local**: All data stays on your machine

## Requirements

- Python 3.11 (recommended)
- Webcam (built-in or external)
- Windows, macOS, or Linux

## Quick Start

### macOS (Recommended: Conda)

The `face_recognition` library requires `dlib`, which is difficult to build from source on macOS. Using Conda with pre-built binaries is the most reliable approach.

```bash
# 1. Install Miniconda (if not already installed)
brew install --cask miniconda

# 2. Initialize conda (then restart your terminal)
conda init "$(basename "${SHELL}")"

# 3. Accept terms of service (first time only)
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# 4. Create environment with Python 3.11
conda create -n visitor-checkin python=3.11 -y

# 5. Activate the environment
conda activate visitor-checkin

# 6. Install dlib from conda-forge (pre-built binary)
conda install -c conda-forge dlib -y

# 7. Install remaining dependencies with pip
# Note: numpy must be < 2.0 for dlib compatibility
pip install face_recognition opencv-python pillow "numpy<2"

# 8. Run the app
python main.py
```

### Ubuntu/Debian (pip)

```bash
# 1. Install build dependencies
sudo apt-get update
sudo apt-get install build-essential cmake python3-dev python3-venv

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

### Windows (pip)

```bash
# 1. Install cmake
pip install cmake

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

If dlib fails to build on Windows, try: `pip install dlib --prefer-binary` or use Conda as described in the macOS section.

## Running the Application

Once dependencies are installed, start the application with:

```bash
# Activate your environment first (if using conda)
conda activate visitor-checkin

# Or if using venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run the app
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

## Managing the Database

To view or edit the visitor database, use **DB Browser for SQLite**:

```bash
brew install --cask db-browser-for-sqlite
```

Then open the app and load `data/visitors.db`. You'll see the `visitors` table with columns:
- `id` - Visitor ID
- `name` - Visitor name
- `face_encoding` - Face encoding (BLOB)
- `created_at` - Registration timestamp
- `last_seen` - Last check-in timestamp
- `visit_count` - Total visits

## Troubleshooting

### "Unsupported image type, must be 8bit gray or RGB image"
This error occurs when numpy 2.x is installed. dlib is not compatible with numpy 2.x. Fix:
```bash
pip install "numpy<2"
```

### Camera permission denied (macOS)
Go to **System Settings** → **Privacy & Security** → **Camera** and enable access for your terminal app.

### dlib fails to build
Use Conda instead of pip to install dlib from conda-forge, which provides pre-built binaries. See the macOS installation instructions.

## Future Enhancements (TODO)

- [ ] Multiple camera support
- [ ] Export attendance reports
- [ ] Visitor notes/tags
- [ ] Automatic camera detection on startup
- [ ] Kiosk mode (auto-scan without button click)
