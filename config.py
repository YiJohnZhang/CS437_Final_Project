'''

lmao, decide if you want to do enum or map for channel
'''
from enum import Enum

class I2C_Driver_Model(Enum):
	TLC59108F = 'tlc59108f'
	PCA9685 = 'pca9685'

GENERAL_SETTINGS = {
	'_IS_DEBUG_MODE': False
}
"""
merge below with `GENERAL_SETTINGS`?
class I2C_Device_Channels(Enum):
	'''
		crab walking: all wheels skid to turn
		mecanum: can turn in place
		single pivoting axle: typical car design, note the wheels of the non-pivoting axle for this kit will slip b/c there is no differential
		dual pivoting axle: high-end car designs
	'''
	PWM_SPEAKER_CHANNEL = 0		# SPEAKER_CHANNEL
	LIDAR_MOTOR_PWM_CHANNEL = 1	#
	TURNING_SERVO_1 = 2
	TURNING_SERVO_2 = 3
"""

MAIN_I2C_DRIVER_CHANNEL_CONSTANTS = {
	'SPEAKER_CHANNEL': 0,
	'LIDAR_MOTOR_PWM_CHANNEL': 1,
	'TURNING_SERVOMOTOR_1_CHANNEL': 2,
	'TURNING_SERVOMOTOR_2_CHANNEL': 3,
	'FRONT_LEFT_MOTOR_CHANNEL': 4,
	'FRONT_RIGHT_MOTOR_CHANNEL': 5,
	'REAR_LEFT_MOTOR_CHANNEL': 6,
	'REAR_RIGHT_MOTOR_CHANNEL': 7
}

# --------- `ultrasonic_sensor.py` (Ultrasonic Sensor Config)
ULTRASONIC_SENSOR_SETTINGS = {
	'DEFAULT_SPEED_OF_SOUND': 346.2,		# [m/s]: 298.15 K, 1 atm, dry air
	'DEFAULT_TEMPERATURE': 298.15,			# [K], fallback temperature
	'DEFAULT_TRIG_PIN': 18,
	'MINIMUM_DETECTION_DISTANCE': 2.5,		# [mm]
	'MAXIMUM_DETECTION_DISTANCE': 3000.0,	# [mm]
	'TRIGGER_PULSE_TIME_LENGTH': 0.00001,	# [s]: 10 us
	'SETUP_SETTLING_TIME': 0.5				# [s]: 0.5 s
}

# --------- `i2c_pwm_driver.py` (I2C Driver Config)
# change this `GENERAL_I2C_PWM_DRIVER_SETTINGS` to `MAIN_i2c...` for all devices connected to the main i2c driver
GENERAL_I2C_PWM_DRIVER_SETTINGS = {
	'I2C_DRIVER': I2C_Driver_Model.PCA9685,
	'I2C_DRIVER_DEVICE_NAME': None,
		# change to tlc... later
	'I2C_BUS_CHANNEL_NUMBER': 1,
		# for RPi, [i2c is on bus ## 1](https://forums.raspberrypi.com/viewtopic.php?t=73363)
		# note: `sudo apt-get install python3-smbus i2c-tools`; 
		# and use `i2cdetect -l` to list all channels for i2c;
		# or use `i2cdetect -y <CH##>` to detect if it is the correct bus channel ##
		# MangoPi: Ch 0, OrangePi: Ch ??
	'I2C_BIT_RESOLUTION': 12,
	'I2C_MAX_BITS': None,
	'PWM_CHANNELS': 16,
	# === hard config code over to i2c_pwm_driver.py
	'I2C_DEVICE_ADDRESS': 0x40,
}

GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_DRIVER_DEVICE_NAME'] = 'MAIN_PCA9685' if GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_DRIVER'] is I2C_Driver_Model.PCA9685 else 'MAIN_TLC59108'
GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_MAX_BITS'] = 2 ** GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_BIT_RESOLUTION'] - 1

# --------- `travel_motor.py` (DRV8835 Config)
DRV8835_SETTINGS = {
	'ARE_MOTORS_REVERSE_MOUNTED': False,
	'DEFAULT_FRONT_LEFT_MOTOR_PIN': 26,
	'DEFAULT_FRONT_RIGHT_MOTOR_PIN': 5,
	'DEFAULT_REAR_LEFT_MOTOR_PIN': 16,
	'DEFAULT_REAR_RIGHT_MOTOR_PIN': 5,
	'I2C_DRIVER_FRONT_LEFT_MOTOR_CHANNEL': 0,
	'I2C_DRIVER_FRONT_RIGHT_MOTOR_CHANNEL': 1,
	'I2C_DRIVER_REAR_LEFT_MOTOR_CHANNEL': 2,
	'I2C_DRIVER_REAR_RIGHT_MOTOR_CHANNEL': 3
}

# --------- `servomotor.py` (Servomotor Config)
SERVOMOTOR_SETTINGS = {

}