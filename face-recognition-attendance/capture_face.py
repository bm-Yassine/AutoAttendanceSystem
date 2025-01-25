import cv2
import time
import os

try:
    from picamera2 import Picamera2
    picamera_available = True
except ImportError:
    picamera_available = False


def capture_image():
	
	if picamera_available:
		camera = Picamera2()
		config = camera.create_preview_configuration()
		camera.configure(config)
		camera.start()
		using_picamera = True
		
	elif not picamera_available:
		camera = cv2.VideoCapture(0)
		using_picamera = False
		
    
              
    #create directory if inexistant
	if not os.path.exists('faces'):
		os.makedirs('faces')
           
           
	inp = input('Enter person name: ')
	print("Press SPACE to capture or ESC to quit")
	while True:
        
        #read frame
		frame = camera.capture_array()
            
        #display
		cv2.imshow('Press SPACE to capture', frame)
            
        #wait for keypress
		key= cv2.waitKey(1)
            
		if key == 27: # ESC key
			break
            
		elif key == 32: # SAPCE key
            #save image
			image_path = f'faces/{inp}.jpg'
			cv2.imwrite(image_path, frame)
			print(f"Image saved to {image_path}")
                
            #display on screen
            #cv2.putText(frame, "Image Captured!", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            #cv2.imshow('Capture Image', frame)
            #cv2.waitKey(1000)
			break
          
        
    #release
	if using_picamera:
		camera.stop()
	else:
		camera.release()
        
        
	cv2.destroyAllWindows()
    
    
    
if __name__ == "__main__":
	print("Image Capture Program for Attendance System with Facial Recognition ")
	try:
		capture_image()
	except Exception as e:
		print(f"An error occurred: {str(e)} ")
    
