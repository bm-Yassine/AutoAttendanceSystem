***Facial Recognition Attendance System***

This project implements an automated attendance tracking system using facial recognition on a Raspberry Pi. It combines image processing, face recognition, and Excel integration to streamline and digitize classroom or organizational attendance logging.


**Features**

- Real-time face detection and recognition.
- Excel-based attendance sheet generation and updates.
- LCD display for visual feedback.
- Buzzer for audio confirmation.
- Duplicate attendance prevention.
- Compatible with both Pi Camera and USB cameras.
- Supports headless (console) mode.
- Organized data by class name and date.


**Hardware Requirements**

- Raspberry Pi (preferably with Raspbian OS 64-bit).
- Pi Camera or USB webcam.
- 16x2 LCD display.
- Buzzer.
- GPIO wires.

**Software Requirements**

Python 3.x and the following Python libraries:

- opencv-python
- face_recognition
- xlwt
- xlrd
- xlutils

To install all dependencies at once:
- pip install -r libraries.txt

**How to Run**

1. Capture Known Faces
Before running the main script, capture and label known faces using:
python capture_face.py

This will store images in a faces/ folder by pressing SPACE or Q to quit.

2. Run Attendance System
Once faces are stored, launch the main attendance system:
python face_recognition_code.py

The script will:
- Load known faces
- Start video capture
- Recognize and mark attendance in Excel
- Show feedback on LCD and buzzer
- Log time of attendance for each individual