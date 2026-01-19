# Creating a Clickable App Launcher (macOS)

This document explains how to launch the Visitor Check-In app without using the terminal.

## The Launcher File

The file `Visitor Check-In.command` is a shell script that macOS treats as double-clickable. It:

1. Changes to the application directory
2. Runs `main.py` using Python from the conda environment

## Setup Requirements

### 1. Conda Environment

The launcher expects a conda environment named `visitor-checkin` installed via Homebrew:

```bash
brew install --cask miniconda
conda create -n visitor-checkin python=3.11 -y
conda activate visitor-checkin
conda install -c conda-forge dlib -y
pip install face_recognition opencv-python pillow "numpy<2"
```

### 2. Make the Launcher Executable

```bash
chmod +x "Visitor Check-In.command"
```

### 3. Python Path

The launcher uses a hardcoded path to Python. If your conda is installed differently, edit line 9 of the `.command` file:

```bash
# Intel Mac (Homebrew)
PYTHON="/usr/local/Caskroom/miniconda/base/envs/visitor-checkin/bin/python"

# Apple Silicon Mac (Homebrew)
PYTHON="/opt/homebrew/Caskroom/miniconda/base/envs/visitor-checkin/bin/python"

# Standard miniconda install
PYTHON="$HOME/miniconda3/envs/visitor-checkin/bin/python"
```

To find your Python path:
```bash
conda activate visitor-checkin
which python
```

## Using the Launcher

### Double-Click to Launch
Simply double-click `Visitor Check-In.command` in Finder. A Terminal window will open briefly and the app will start.

### Add to Dock
Drag the `.command` file to the right side of the Dock (after the separator line).

### Create Desktop Shortcut
1. Right-click the `.command` file
2. Select "Make Alias"
3. Drag the alias to the Desktop
4. Rename it to "Visitor Check-In"

### Add a Custom Icon
1. Find or create an icon image (PNG, ICNS, or JPEG)
2. Open the image in Preview and press Cmd+C to copy
3. Right-click `Visitor Check-In.command` → "Get Info"
4. Click the small icon in the top-left corner of the Info window
5. Press Cmd+V to paste the new icon

## Troubleshooting

### "Permission denied" error
Run: `chmod +x "Visitor Check-In.command"`

### "Python not found" error
The conda environment path is wrong. Find your actual path with:
```bash
conda activate visitor-checkin
which python
```
Then update line 9 in the `.command` file.

### "No module named 'cv2'" or similar
Install the missing package in your conda environment:
```bash
conda activate visitor-checkin
pip install opencv-python face_recognition pillow "numpy<2"
```

### App won't open (macOS security)
First time running, macOS may block it:
1. Go to System Preferences → Privacy & Security
2. Look for a message about "Visitor Check-In.command" being blocked
3. Click "Open Anyway"

Or right-click the file and select "Open" instead of double-clicking.
