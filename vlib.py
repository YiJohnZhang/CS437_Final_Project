'''
Code modified from Sunfoudner's `vilib`
https://github.com/sunfounder/vilib/blob/main/vilib/vilib.py
'''

import os
import logging
import time
import datetime
import threading
from multiprocessing import Process, Manager


from picamera2 import Picamera2
import libcamera

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
DEFAULT_PICTURES_PATH = './'
DEFAULT_VIDEOS_PATH = './'

class Vilib(object):

	picam2 = Picamera2()

	camera_size = (640, 480)
	camera_width = 640
	camera_height = 480
	camera_vflip = False
	camera_hflip = False
	camera_run = False

	flask_thread = None
	camera_thread = None
	flask_start = False

	qrcode_display_thread = None
	qrcode_making_completed = False
	qrcode_img = Manager().list(range(1))
	qrcode_img_encode = None
	qrcode_win_name = 'qrcode'

	img = Manager().list(range(1))
	flask_img = Manager().list(range(1))

	Windows_Name = "picamera"
	imshow_flag = False
	web_display_flag = False
	imshow_qrcode_flag = False
	web_qrcode_flag = False

	draw_fps = False
	fps_origin = (camera_width-105, 20)
	fps_size = 0.6
	fps_color = (255, 255, 255)

	detect_obj_parameter = {}
	color_detect_color = None
	face_detect_sw = False
	hands_detect_sw = False
	pose_detect_sw = False
	image_classify_sw = False
	image_classification_model = None
	image_classification_labels = None
	objects_detect_sw = False
	objects_detection_model = None
	objects_detection_labels = None
	qrcode_detect_sw = False
	traffic_detect_sw = False
		
	@staticmethod
	def get_instance():
		return Vilib.picam2

	@staticmethod
	def set_controls(controls):
		Vilib.picam2.set_controls(controls)

	@staticmethod
	def get_controls():
		return Vilib.picam2.capture_metadata()

	@staticmethod
	def camera():
		Vilib.camera_width = Vilib.camera_size[0]
		Vilib.camera_height = Vilib.camera_size[1]

		picam2 = Vilib.picam2

		preview_config = picam2.preview_configuration
		# preview_config.size = (800, 600)
		preview_config.size = Vilib.camera_size
		preview_config.format = 'RGB888'  # 'XRGB8888', 'XBGR8888', 'RGB888', 'BGR888', 'YUV420'
		preview_config.transform = libcamera.Transform(
										hflip=Vilib.camera_hflip,
										vflip=Vilib.camera_vflip
									)
		preview_config.colour_space = libcamera.ColorSpace.Sycc()
		preview_config.buffer_count = 4
		preview_config.queue = True
		# preview_config.raw = {'size': (2304, 1296)}
		preview_config.controls = {'FrameRate': 60} # change picam2.capture_array() takes time

		try:
			picam2.start()
		except Exception as e:
			print(f"\033[38;5;1mError:\033[0m\n{e}")
			print("\nPlease check whether the camera is connected well" +\
				"You can use the \"libcamea-hello\" command to test the camera"
				)
			exit(1)
		Vilib.camera_run = True
		Vilib.fps_origin = (Vilib.camera_width-105, 20)
		fps = 0
		start_time = 0
		framecount = 0
		try:
			start_time = time.time()
			while True:
				# ----------- extract image data ----------------
				# st = time.time()
				Vilib.img = picam2.capture_array()
				# print(f'picam2.capture_array(): {time.time() - st:.6f}')
				# st = time.time()

				# ----------- image gains and effects ----------------

				# ----------- image detection and recognition ----------------
				Vilib.img = Vilib.color_detect_func(Vilib.img)
				Vilib.img = Vilib.face_detect_func(Vilib.img)
				Vilib.img = Vilib.traffic_detect_fuc(Vilib.img)
				Vilib.img = Vilib.qrcode_detect_func(Vilib.img)

				Vilib.img = Vilib.image_classify_fuc(Vilib.img)
				Vilib.img = Vilib.object_detect_fuc(Vilib.img)
				Vilib.img = Vilib.hands_detect_fuc(Vilib.img)
				Vilib.img = Vilib.pose_detect_fuc(Vilib.img)

				# ----------- calculate fps and draw fps ----------------
				# calculate fps
				framecount += 1
				elapsed_time = float(time.time() - start_time)
				if (elapsed_time > 1):
					fps = round(framecount/elapsed_time, 1)
					framecount = 0
					start_time = time.time()

				# print(f"elapsed_time: {elapsed_time}, fps: {fps}")

				# draw fps
				if Vilib.draw_fps:
					cv2.putText(
							# img, # image
							Vilib.img,
							f"FPS: {fps}", # text
							Vilib.fps_origin, # origin
							cv2.FONT_HERSHEY_SIMPLEX, # font
							Vilib.fps_size, # font_scale
							Vilib.fps_color, # font_color
							1, # thickness
							cv2.LINE_AA, # line_type: LINE_8 (default), LINE_4, LINE_AA
						)

				# ---- copy img for flask --- 
				# st = time.time()
				Vilib.flask_img = Vilib.img
				# print(f'vilib.flask_img: {time.time() - st:.6f}')

				# ----------- display on desktop ----------------
				if Vilib.imshow_flag == True:
					try:
						try:
							prop = cv2.getWindowProperty(Vilib.Windows_Name, cv2.WND_PROP_VISIBLE)
							qrcode_prop = cv2.getWindowProperty(Vilib.qrcode_win_name, cv2.WND_PROP_VISIBLE)
							if prop < 1 or qrcode_prop < 1:
								break
						except:
							pass

						cv2.imshow(Vilib.Windows_Name, Vilib.img)

						if Vilib.imshow_qrcode_flag and Vilib.qrcode_making_completed:
								Vilib.qrcode_making_completed = False
								cv2.imshow(Vilib.qrcode_win_name, Vilib.qrcode_img)

						cv2.waitKey(1)

					except Exception as e:
						Vilib.imshow_flag = False
						print(f"imshow failed:\n  {e}")
						break

				# ----------- exit ----------------
				if Vilib.camera_run == False:
					break

				# print(f'loop end: {time.time() - st:.6f}')
				
		except KeyboardInterrupt as e:
			print(e)
		finally:
			picam2.close()
			cv2.destroyAllWindows()

	@staticmethod
	def camera_start(vflip=False, hflip=False, size=None):
		if size is not None:
			Vilib.camera_size = size
		Vilib.camera_hflip = hflip
		Vilib.camera_vflip = vflip
		Vilib.camera_thread = threading.Thread(target=Vilib.camera, name="vilib")
		Vilib.camera_thread.daemon = False
		Vilib.camera_thread.start()
		while not Vilib.camera_run:
			time.sleep(0.1)

	@staticmethod
	def camera_close():
		if Vilib.camera_thread != None:
			Vilib.camera_run = False
			time.sleep(0.1)

	'''
	@staticmethod
	def display(local=True, web=True):
		# cheack camera thread is_alive
		if Vilib.camera_thread != None and Vilib.camera_thread.is_alive():
			# check gui
			if local == True:
				if 'DISPLAY' in os.environ.keys():
					Vilib.imshow_flag = True  
					print("Imgshow start ...")
				else:
					Vilib.imshow_flag = False 
					print("Local display failed, because there is no gui.") 
			# web video
			if web == True:
				Vilib.web_display_flag = True
				print("\nWeb display on:")
				wlan0, eth0 = getIP()
				if wlan0 != None:
					print(f"	  http://{wlan0}:9000/mjpg")
				if eth0 != None:
					print(f"	  http://{eth0}:9000/mjpg")
				print() # new line

				# ----------- flask_thread ----------------
				if Vilib.flask_thread == None or Vilib.flask_thread.is_alive() == False:
					print('Starting web streaming ...')
					Vilib.flask_thread = threading.Thread(name='flask_thread',target=web_camera_start)
					Vilib.flask_thread.daemon = True
					Vilib.flask_thread.start()
		else:
			print('Error: Please execute < camera_start() > first.')
	'''

	@staticmethod
	def show_fps(color=None, fps_size=None, fps_origin=None):
		if color is not None:
			Vilib.fps_color = color
		if fps_size is not None:
			Vilib.fps_size = fps_size
		if fps_origin is not None:
			Vilib.fps_origin = fps_origin

		Vilib.draw_fps = True

	@staticmethod
	def hide_fps():
		Vilib.draw_fps = False

	# take photo
	# =================================================================
	@staticmethod
	def take_photo(photo_name, path=DEFAULT_PICTURES_PATH):
		# ----- check path -----
		if not os.path.exists(path):
			# print('Path does not exist. Creating path now ... ')
			os.makedirs(name=path, mode=0o751, exist_ok=True)
			time.sleep(0.01) 
		# ----- save photo -----
		status = False
		for _ in range(5):
			if  Vilib.img is not None:
				status = cv2.imwrite(path + '/' + photo_name +'.jpg', Vilib.img)
				break
			else:
				time.sleep(0.01)
		else:
			status = False

		# if status:
		#	 print('The photo is saved as '+path+'/'+photo_name+'.jpg')
		# else:
		#	 print('Photo save failed .. ')

		return status


	# record video
	# =================================================================
	rec_video_set = {}

	rec_video_set["fourcc"] = cv2.VideoWriter_fourcc(*'XVID') 
	#rec_video_set["fourcc"] = cv2.cv.CV_FOURCC("D", "I", "B", " ") 

	rec_video_set["fps"] = 30.0
	rec_video_set["framesize"] = (640, 480)
	rec_video_set["isColor"] = True

	rec_video_set["name"] = "default"
	rec_video_set["path"] = DEFAULT_VIDEOS_PATH

	rec_video_set["start_flag"] = False
	rec_video_set["stop_flag"] =  False

	rec_thread = None

	@staticmethod
	def rec_video_work():
		if not os.path.exists(Vilib.rec_video_set["path"]):
			# print('Path does not exist. Creating path now ... ')
			os.makedirs(name=Vilib.rec_video_set["path"],
						mode=0o751,
						exist_ok=True
			)
			time.sleep(0.01)
		video_out = cv2.VideoWriter(Vilib.rec_video_set["path"]+'/'+Vilib.rec_video_set["name"]+'.avi',
									Vilib.rec_video_set["fourcc"], Vilib.rec_video_set["fps"], 
									Vilib.rec_video_set["framesize"], Vilib.rec_video_set["isColor"])
	
		while True:
			if Vilib.rec_video_set["start_flag"] == True:
				# video_out.write(Vilib.img_array[0])
				video_out.write(Vilib.img)
			if Vilib.rec_video_set["stop_flag"] == True:
				video_out.release() # note need to release the video writer
				Vilib.rec_video_set["start_flag"] == False
				break

	@staticmethod
	def rec_video_run():
		if Vilib.rec_thread != None:
			Vilib.rec_video_stop()
		Vilib.rec_video_set["stop_flag"] = False
		Vilib.rec_thread = threading.Thread(name='rec_video', target=Vilib.rec_video_work)
		Vilib.rec_thread.daemon = True
		Vilib.rec_thread.start()

	@staticmethod
	def rec_video_start():
		Vilib.rec_video_set["start_flag"] = True 
		Vilib.rec_video_set["stop_flag"] = False

	@staticmethod
	def rec_video_pause():
		Vilib.rec_video_set["start_flag"] = False

	@staticmethod
	def rec_video_stop():
		Vilib.rec_video_set["start_flag"] == False
		Vilib.rec_video_set["stop_flag"] = True
		if Vilib.rec_thread != None:
			Vilib.rec_thread.join(3)
			Vilib.rec_thread = None

   # traffic sign detection
	# =================================================================
	'''
	@staticmethod
	def traffic_detect_switch(flag=False):
		Vilib.traffic_detect_sw  = flag
		if Vilib.traffic_detect_sw:
			from .traffic_sign_detection import traffic_sign_detect, traffic_sign_obj_parameter
			Vilib.traffic_detect_work = traffic_sign_detect
			Vilib.traffic_sign_obj_parameter = traffic_sign_obj_parameter
			Vilib.detect_obj_parameter['traffic_sign_x'] = Vilib.traffic_sign_obj_parameter['x']
			Vilib.detect_obj_parameter['traffic_sign_y'] = Vilib.traffic_sign_obj_parameter['y']
			Vilib.detect_obj_parameter['traffic_sign_w'] = Vilib.traffic_sign_obj_parameter['w']
			Vilib.detect_obj_parameter['traffic_sign_h'] = Vilib.traffic_sign_obj_parameter['h']
			Vilib.detect_obj_parameter['traffic_sign_t'] = Vilib.traffic_sign_obj_parameter['t']
			Vilib.detect_obj_parameter['traffic_sign_acc'] = Vilib.traffic_sign_obj_parameter['acc']

	@staticmethod
	def traffic_detect_fuc(img):
		if Vilib.traffic_detect_sw and hasattr(Vilib, "traffic_detect_work"):
			img = Vilib.traffic_detect_work(img, border_rgb=(255, 0, 0))
			Vilib.detect_obj_parameter['traffic_sign_x'] = Vilib.traffic_sign_obj_parameter['x']
			Vilib.detect_obj_parameter['traffic_sign_y'] = Vilib.traffic_sign_obj_parameter['y']
			Vilib.detect_obj_parameter['traffic_sign_w'] = Vilib.traffic_sign_obj_parameter['w']
			Vilib.detect_obj_parameter['traffic_sign_h'] = Vilib.traffic_sign_obj_parameter['h']
			Vilib.detect_obj_parameter['traffic_sign_t'] = Vilib.traffic_sign_obj_parameter['t']
			Vilib.detect_obj_parameter['traffic_sign_acc'] = Vilib.traffic_sign_obj_parameter['acc']
		return img
	'''