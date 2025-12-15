'''
Designed for use with the DRV8835 Motor Driver IC in `PH/EN` mode.

Note: alter LEDs should be controlled by Car obj when turning/stopping/reversing etc.
- [] a neat feature would be to allow a config variable (and config file) to translate duty (bits) from real-world movement


'''
from time import sleep
import RPi.GPIO as GPIO
from actuation_models import SteeringModels, ManueverType
from i2c_device import PCA9685_PWM_Driver, CH592F_Device
# from pca9685 import QwiicPCA9685
from config import GENERAL_SETTINGS, GENERAL_I2C_PWM_DRIVER_SETTINGS, DRV8835_SETTINGS

# expose to potential `config` file
_IS_DEBUG_MODE = GENERAL_SETTINGS['IS_DEBUG_MODE']

I2C_BIT_RESOLUTION = GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_BIT_RESOLUTION'] or 12
	# note: change when I switch over to tlc59108f
I2C_MAX_BITS = GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_MAX_BITS'] or (2 ** I2C_BIT_RESOLUTION - 1)

ARE_MOTORS_REVERSE_MOUNTED = DRV8835_SETTINGS['ARE_MOTORS_REVERSE_MOUNTED']
DEFAULT_FRONT_LEFT_MOTOR_PIN = DRV8835_SETTINGS['DEFAULT_FRONT_LEFT_MOTOR_PIN']
DEFAULT_FRONT_RIGHT_MOTOR_PIN = DRV8835_SETTINGS['DEFAULT_FRONT_RIGHT_MOTOR_PIN']
DEFAULT_REAR_LEFT_MOTOR_PIN = DRV8835_SETTINGS['DEFAULT_REAR_LEFT_MOTOR_PIN']
DEFAULT_REAR_RIGHT_MOTOR_PIN = DRV8835_SETTINGS['DEFAULT_REAR_RIGHT_MOTOR_PIN']

I2C_DRIVER_FRONT_LEFT_MOTOR_CHANNEL = DRV8835_SETTINGS['I2C_DRIVER_FRONT_LEFT_MOTOR_CHANNEL']
I2C_DRIVER_FRONT_RIGHT_MOTOR_CHANNEL = DRV8835_SETTINGS['I2C_DRIVER_FRONT_RIGHT_MOTOR_CHANNEL']
I2C_DRIVER_REAR_LEFT_MOTOR_CHANNEL = DRV8835_SETTINGS['I2C_DRIVER_REAR_LEFT_MOTOR_CHANNEL']
I2C_DRIVER_REAR_RIGHT_MOTOR_CHANNEL = DRV8835_SETTINGS['I2C_DRIVER_REAR_RIGHT_MOTOR_CHANNEL']

class TravelMotor:
	def __init__(self, 
			  front_left_motor_pin: int = DEFAULT_FRONT_LEFT_MOTOR_PIN,
			  front_right_motor_pin: int  = DEFAULT_FRONT_RIGHT_MOTOR_PIN,
			  rear_left_motor_pin: int  = DEFAULT_REAR_LEFT_MOTOR_PIN,
			  rear_right_motor_pin: int  = DEFAULT_REAR_RIGHT_MOTOR_PIN,
			  are_motors_reverse_mounted: bool = ARE_MOTORS_REVERSE_MOUNTED,
			  steering_model: SteeringModels = SteeringModels.CRAB_WALKING,
			  _is_debug_mode: bool = _IS_DEBUG_MODE
			  ):
		'''

		'''
		assert isinstance(steering_model, SteeringModels)

		self._is_debug_mode = _is_debug_mode
		self.i2c_driver = PCA9685_PWM_Driver(address = 0x40, global_frequency = 50)

		# sets direction of motors
		self.motor_fl_pin = front_left_motor_pin
		self.motor_fr_pin = front_right_motor_pin
		self.motor_rl_pin = rear_left_motor_pin
		self.motor_rr_pin = rear_right_motor_pin
		self.travelling_motors_pins_list = [
			self.motor_fl_pin,
			self.motor_fr_pin,
			self.motor_rl_pin,
			self.motor_rr_pin
		]

		self.are_motors_reverse_mounted = True if are_motors_reverse_mounted else False
			# used to toggle phase
		self.steering_model = steering_model

	def __enter__(self):
		return self

	def __exit__(self) -> None:
		self._teardown()

	def _setup_GPIO_pin(self) -> None:
		'''
		'''
		GPIO.setup(channel = self.motor_fl_pin, dir = GPIO.OUT)
		GPIO.setup(channel = self.motor_fr_pin, dir = GPIO.OUT)
		GPIO.setup(channel = self.motor_rl_pin, dir = GPIO.OUT)
		GPIO.setup(channel = self.motor_rr_pin, dir = GPIO.OUT)

	def _teardown(self) -> None:
		self.stop()

		for pin_id in self.travelling_motors_pins_list:
			if pin_id is not None:
				GPIO.cleanup(pin_id)
	
	def _send_debug_message(self, method_name, speed_in_duty, manuever, is_reversing) -> None:
		# later generalize this
		if self._is_debug_mode:
			direction_str = "backwards" if is_reversing else ""
			print(f'TravelMotor()::{method_name}()::manuever: {manuever}@{speed_in_duty} {direction_str}')

	def bound_motor_duty(self, duty: int = 0) -> int:
		'''
			Sets valid duty cycle
		'''
		'''
		duty = duty if duty >= 0 else abs(duty)
		duty = duty if duty < I2C_MAX_BITS else I2C_MAX_BITS
		'''
		return self.i2c_driver.bound_duty_cycle(duty)

	def drive(self,
		   front_left_motor_duty: int,
		   front_right_motor_duty: int,
		   rear_left_motor_duty: int,
		   rear_right_motor_duty: int) -> None:
		# requires i2c connection 
		'''
		'''

		self.i2c_driver.set_motor_pwm(I2C_DRIVER_FRONT_LEFT_MOTOR_CHANNEL, front_left_motor_duty)
		self.i2c_driver.set_motor_pwm(I2C_DRIVER_FRONT_RIGHT_MOTOR_CHANNEL, front_right_motor_duty)
		self.i2c_driver.set_motor_pwm(I2C_DRIVER_REAR_LEFT_MOTOR_CHANNEL, rear_left_motor_duty)
		self.i2c_driver.set_motor_pwm(I2C_DRIVER_REAR_RIGHT_MOTOR_CHANNEL, rear_right_motor_duty)
		raise NotImplementedError

	def stop(self) -> None:
		'''
		'''
		self.drive(0, 0, 0, 0)

	def move(self, 
		  speed_in_duty: int = 0,
		  manuever: ManueverType = ManueverType.STRAIGHT,
		  is_reversing: bool = False) -> None:
		'''
			Hard-coded crab walk manuevering
		'''

		# an alternative quick and dirty way to reverse without the verbosity
		if speed_in_duty < 0:
			is_reversing = True

		speed_in_duty = self.bound_motor_duty(speed_in_duty)
		if self._is_debug_mode:
			self._send_debug_message('move', speed_in_duty, manuever, is_reversing)

		if (speed_in_duty == 0) or (manuever == ManueverType.EMERGENCY_BRAKE):
			self.stop()
		else:			
			'''
				Table 4 (Section 7.4.1): https://www.ti.com/lit/ds/symlink/drv8835.pdf
				1/True => Reverse
				0/False => Forward
			'''
			
			if manuever == ManueverType.STRAIGHT:
				if is_reversing:
					GPIO.output(self.motor_fl_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_fr_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rl_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rr_pin, not self.are_motors_reverse_mounted)
				else:
					# go forwards
					GPIO.output(self.motor_fl_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_fr_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rl_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rr_pin, self.are_motors_reverse_mounted)
			elif manuever == ManueverType.TURN_LEFT:
				if is_reversing:
					GPIO.output(self.motor_fl_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_fr_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rl_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rr_pin, not self.are_motors_reverse_mounted)
				else:
					# turn left forwards
					GPIO.output(self.motor_fl_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_fr_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rl_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rr_pin, self.are_motors_reverse_mounted)
			elif manuever == ManueverType.TURN_RIGHT:
				if is_reversing:
					GPIO.output(self.motor_fl_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_fr_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rl_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rr_pin, self.are_motors_reverse_mounted)
				else:
					# turn right forwards ()
					GPIO.output(self.motor_fl_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_fr_pin, not self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rl_pin, self.are_motors_reverse_mounted)
					GPIO.output(self.motor_rr_pin, not self.are_motors_reverse_mounted)
			
			self.drive(speed_in_duty, speed_in_duty, speed_in_duty, speed_in_duty)
				# drive with pin setup

def main():
	travel_motor_obj = TravelMotor()

	try:

		# go forwards
		travel_motor_obj.move(100)
		sleep(0.5)
		# TODO: distance interface sets the sleep time as well... time_sleep * pwm_duty_to_speed = distance?

		# "", faster
		travel_motor_obj.move(1000)
		sleep(0.5)
		
		## reverse
		travel_motor_obj.move(100, is_reversing = True)
		sleep(0.5)
		
		# left
		travel_motor_obj.move(100, manuever = ManueverType.TURN_LEFT)
		sleep(0.5)
		travel_motor_obj.move(100, manuever = ManueverType.TURN_LEFT, is_reversing = True)
		sleep(0.5)

		# right
		travel_motor_obj.move(100, manuever = ManueverType.TURN_RIGHT)
		sleep(0.5)
		travel_motor_obj.move(100, manuever = ManueverType.TURN_RIGHT, is_reversing = True)
		sleep(0.5)

		# stop
		travel_motor_obj.stop()

	except KeyboardInterrupt:
		print(f'\ntravel_motor.py::main()::program interrupted')
	finally:
		travel_motor_obj._teardown()

if __name__ == '__main__':
	main()