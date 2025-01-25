import face_recognition
import cv2
import numpy as np
import os

import xlrd, xlwt
from xlwt import Workbook
from datetime import date
from xlutils.copy import copy as xl_copy

import RPi.GPIO as GPIO
import time
from datetime import datetime

import sys
import select

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)









# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 11
LCD_D4 = 12
LCD_D5 = 13
LCD_D6 = 15
LCD_D7 = 16
Buzzer = 22

'''
define pin for lcd
'''
# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005
delay = 1

GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT) # RS
GPIO.setup(LCD_D4, GPIO.OUT) # DB4
GPIO.setup(LCD_D5, GPIO.OUT) # DB5
GPIO.setup(LCD_D6, GPIO.OUT) # DB6
GPIO.setup(LCD_D7, GPIO.OUT) # DB7
GPIO.setup(Buzzer, GPIO.OUT) # DB7

# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

'''
Function Name :lcd_init()
Function Description : this function is used to initialized lcd by sending the different commands
'''
def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)
'''
Function Name :lcd_byte(bits ,mode)
Fuction Name :the main purpose of this function to convert the byte data into bit and send to lcd port
'''
def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command
 
  GPIO.output(LCD_RS, mode) # RS
 
  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
'''
Function Name : lcd_toggle_enable()
Function Description:basically this is used to toggle Enable pin
'''
def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)
'''
Function Name :lcd_string(message,line)
Function  Description :print the data on lcd 
'''
def lcd_string(message, line):
    # Send string to display
    message = message.ljust(LCD_WIDTH," ")
    lcd_byte(line, LCD_CMD)
    
    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)



#--------------------------------------------
#checking camera type
try:
    from picamera2 import Picamera2
    picamera_available = True
except ImportError:
    picamera_available = False

def check_display_available():
    """Check if display is available for showing images"""
    try:
        if os.name == 'posix' and "DISPLAY" not in os.environ:
            return False
        # Try to create a test window
        cv2.namedWindow("test", cv2.WINDOW_AUTOSIZE)
        cv2.destroyWindow("test")
        return True
    except:
        return False
    

class FaceRecognitionSystem:
    def __init__(self):
        #initialize vars
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True
        self.already_marked_attendance = set()
        
        #initialize camera, load faces, setup excel sheet
        self.setup_camera()
        self.load_known_faces()
        self.setup_excel()
        self.display_available = check_display_available()
    
    
    def setup_camera(self):
        """Initialize camera"""
        if picamera_available:
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main ={"format": 'RGB888', "size": (640,480)}
                )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2) #warmup
            self.using_picamera = True
        else:
            self.camera = cv2.VideoCapture(0)
            self.using_picamera = False
    
            
    def load_known_faces(self):
        """Load annd learn faces from 'faces' folder"""
        faces_folder = "faces" #folder with faces data
        if not os.path.exists(faces_folder):
            print(f"folder not found, creating {faces_folder} folder")
            os.makedirs(faces_folder)
            return
        
        print("Loading known faces...")
        for filename in os.listdir(faces_folder):
            if filename.endswith((".png",".jpg",".jpeg")):
                path = os.path.join(faces_folder, filename)
                person_name = os.path.splitext(filename)[0]
                
                try:
                    image = face_recognition.load_image_file(path)
                    encoding = face_recognition.face_encodings(image)[0]
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(person_name)
                    print(f"Loaded face: {person_name}")
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")
                
        print (f"Loaded {len(self.known_face_names)} faces successfully")
                    
    def setup_excel(self):
        """Setup Excel workbook for attendance"""

        today = datetime.now().strftime('%Y-%m-%d')
        try:
            inp = input('Please give current class name: ')
        except:
            print("Error getting class name input - default class : 'maes'")
            ''' default sheet '''
            inp = "maes"
            return

        try:
            self.rb = xlrd.open_workbook('attendance_excel.xls', formatting_info=True)
            self.wb = xl_copy(self.rb)
            sheet_names = self.rb.sheet_names()
        
            if inp in sheet_names:
                sheet_index = sheet_names.index(inp)
                rb_sheet = self.rb.sheet_by_index(sheet_index)
                self.sheet = self.wb.get_sheet(sheet_index)
                self.col = rb_sheet.ncols
                self.sheet.write(0, self.col, today)
                self.row = 1
            else:
                self.sheet = self.wb.add_sheet(inp)
                self.sheet.write(0, 0, 'Name')
                self.col = 1
                self.sheet.write(0, self.col, today)
                self.row = 1

        except FileNotFoundError:
            self.wb = xlwt.Workbook()
            self.sheet = self.wb.add_sheet(inp)
            self.sheet.write(0, 0, 'Name')
            self.col = 1
            self.sheet.write(0, self.col, today)
            self.row = 1
        
        self.wb.save('attendance_excel.xls')

       

    def get_frame(self):
        """Capture frame from camera"""
        if self.using_picamera:
            return True, self.camera.capture_array()
        else :
            return self.camera.read()

    def process_frame(self, frame):
        """"Process frame for Face Recognition"""
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
        
        
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        
        if len(small_frame.shape) ==2:
            small_frame = cv2.cvtColor(small_frame, cv2.COLOR_GRAY2RGB)
        
        if self.process_this_frame:
            # Find faces in frame
            self.face_locations = face_recognition.face_locations(small_frame)
            self.face_encodings = face_recognition.face_encodings(small_frame, self.face_locations)

            self.face_names = []
            for face_encoding in self.face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]

                    #mark attendance if not done yet
                    if name not in self.already_marked_attendance:
                        self.mark_attendance(name)
                        self.already_marked_attendance.add(name)

                self.face_names.append(name)
                
        self.process_this_frame = not self.process_this_frame


    def mark_attendance(self, name):
        """Mark attendance in Excel sheet"""
        current_time = time.strftime('%H:%M:%S')
    
        # Store sheet name during setup_excel
        try:
            rb_sheet = self.rb.sheet_by_index(self.rb.sheet_names().index(inp))
        
            # Check if name exists in first column
            for row in range(rb_sheet.nrows):
                existing_name = rb_sheet.cell_value(row, 0)
                if existing_name.lower() == name.lower():
                    self.sheet.write(row, self.col, current_time)
                    self.wb.save('attendance_excel.xls')
                    print(f"Updated Attendance for {name} at {current_time}")
                    lcd_string("Attendance", LCD_LINE_1)
                    lcd_string("taken...", LCD_LINE_2)
                    GPIO.output(Buzzer, GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(Buzzer, GPIO.LOW)
                    time.sleep(2)
                    lcd_string("Next Student", LCD_LINE_1)
                    lcd_string("<3", LCD_LINE_2)
                    return
                
        except:
            # For new sheets that don't exist in rb yet
            pass
        
        # New name on the list
        self.sheet.write(self.row, 0, name)
        self.sheet.write(self.row, self.col, current_time)
        self.row += 1
        self.wb.save('attendance_excel.xls')
        print(f"Marked Attendance for {name} at {current_time}")
        lcd_string("Attendance", LCD_LINE_1)
        lcd_string("taken...", LCD_LINE_2)
        GPIO.output(Buzzer, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(Buzzer, GPIO.LOW)
        time.sleep(2)
        lcd_string("Next Student", LCD_LINE_1)
        lcd_string("<3", LCD_LINE_2)
        

    def draw_results(self, frame):
        """Draw recognition results on frame"""
        for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
            #scale back up
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2
    
            #draw box and label
            cv2.rectangle(frame, (left,top), (right,bottom), (0,0,255),2)
            cv2.rectangle(frame, (left, bottom - 35), (right,bottom), (0,0,255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom -6), font, 0.6,(255,255,255),1)

    def run(self):
        """Main Loop"""
        lcd_init()
        time.sleep(0.1)
        lcd_string("Starting up", LCD_LINE_1)
        lcd_string("Attendance...", LCD_LINE_2)
        print("Starting the face recognition...")
        print(f"Loaded {len(self.known_face_names)} known faces")
        time.sleep(0.9)

        try:
            while True:
                ret, frame = self.get_frame()
                if not ret:
                    print("Failed to grab frame")
                    break

                
                self.process_frame(frame)

                #only if display is available
                if self.display_available:
                    self.draw_results(frame)
                    cv2.imshow('Face Recognition', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                else:
                    time.sleep(0.1)
                    # Check for quit command from terminal
                    if not os.isatty(sys.stdin.fileno()):
                        continue
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = input()
                        if line.strip() == 'q':
                            break

        except KeyboardInterrupt:
            print("\nStopping face recognition...")


        #cleanup
        if self.using_picamera:
            self.camera.stop()
        else:
            self.camera.release()

        if self.display_available:
            cv2.destroyAllWindows()

        lcd_byte(0x01, LCD_CMD)
        GPIO.cleanup()


        
if __name__ == "__main__" :
    system = FaceRecognitionSystem()
    system.run()

         
        
        
    