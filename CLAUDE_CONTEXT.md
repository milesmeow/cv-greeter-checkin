# Claude Code Context

This document provides context for Claude Code to understand and work on this project effectively.

## Project Purpose

This is a **visitor check-in system for a religious organization**. A greeter sits at the front door and uses this app to:
1. Check in arriving visitors by capturing their face
2. See if the visitor is recognized (display their name)
3. Register new visitors by entering their name
4. Log all arrivals with timestamps

## Key Design Decisions

### Greeter-Controlled (Not Automatic)
The greeter manually clicks a button to initiate check-in. This is intentional:
- More respectful/less surveillance-like
- Gives greeter control over the interaction
- Avoids false triggers from people walking by

### Local-Only Database
No cloud backend. Everything runs on one machine:
- SQLite for visitor records
- Face encodings stored as numpy arrays (pickled or in SQLite BLOB)
- CSV logs for easy export

### No Pre-trained Data
The system starts empty. Visitors are added one at a time as they arrive and the greeter registers them.

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    main.py                               │
│                 (Application entry)                      │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    ui.py                                 │
│              (Tkinter interface)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Camera View │  │ Check-In Btn│  │ Result Display  │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────┬───────────────┬───────────────┬───────────────┘
          │               │               │
┌─────────▼───────┐ ┌─────▼─────┐ ┌───────▼───────┐
│   camera.py     │ │recognition│ │  database.py  │
│ (OpenCV capture)│ │   .py     │ │   (SQLite)    │
└─────────────────┘ └───────────┘ └───────────────┘
```

## User Flow

### Check-In (Known Visitor)
```
Greeter clicks "Check In"
    → Camera captures frame
    → Face detected and encoded
    → Encoding compared to database
    → Match found!
    → Display: "Welcome back, [Name]!"
    → Log arrival to CSV
```

### Check-In (New Visitor)
```
Greeter clicks "Check In"
    → Camera captures frame
    → Face detected and encoded
    → No match in database
    → Display: "New visitor detected"
    → Greeter enters name in text field
    → Greeter clicks "Register"
    → Face encoding + name saved to database
    → Log arrival to CSV
```

## Database Schema

### visitors table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Visitor's name |
| face_encoding | BLOB | 128-dim numpy array (pickled) |
| created_at | TIMESTAMP | When first registered |
| last_seen | TIMESTAMP | Most recent check-in |
| visit_count | INTEGER | Total visits |

### Arrival Log (CSV)
```
timestamp,visitor_id,visitor_name,recognized
2024-01-15 09:30:00,1,John Smith,true
2024-01-15 09:45:00,2,Jane Doe,true
2024-01-15 10:00:00,3,New Person,false
```

## Face Recognition Approach

Using the `face_recognition` library (wrapper around dlib):

1. **Detection**: Find face bounding boxes in image
2. **Encoding**: Convert face to 128-dimensional vector
3. **Comparison**: Euclidean distance between vectors
   - Distance < 0.6 = same person (adjustable threshold)

```python
import face_recognition

# Encode a face
image = face_recognition.load_image_file("photo.jpg")
encodings = face_recognition.face_encodings(image)

# Compare faces
distance = face_recognition.face_distance([known_encoding], unknown_encoding)
is_match = distance[0] < 0.6
```

## UI Layout (Tkinter)

```
┌─────────────────────────────────────────────┐
│          Visitor Check-In System            │
├─────────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐    │
│  │                                     │    │
│  │         Camera Preview              │    │
│  │         (640 x 480)                 │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │         [  CHECK IN  ]              │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Status: Ready                      │    │
│  │  Last Check-in: John Smith (9:30am) │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ── New Visitor Registration ──             │
│  Name: [________________]  [Register]       │
│                                             │
└─────────────────────────────────────────────┘
```

## Common Tasks for Claude Code

### "Add a feature to export attendance"
- Add export button to UI
- Read from CSV logs in data/logs/
- Format as Excel or PDF

### "Improve recognition accuracy"
- Adjust threshold in recognition.py (currently 0.6)
- Consider storing multiple encodings per person
- Add lighting normalization

### "Add visitor notes"
- Add notes column to database
- Add text field in UI for viewing/editing notes
- Show notes when visitor is recognized

### "Make it work with multiple cameras"
- Modify camera.py to enumerate available cameras
- Add camera selector dropdown in UI

## Testing

Run tests with:
```bash
python -m pytest tests/
```

Test without a camera by mocking the camera input with static images.

## Dependencies Explained

- **face_recognition**: High-level face recognition (uses dlib under the hood)
- **opencv-python**: Camera capture and image processing
- **numpy**: Array operations for face encodings
- **Pillow**: Image format conversions for Tkinter display
