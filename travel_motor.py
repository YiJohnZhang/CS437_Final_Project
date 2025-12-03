'''
Designed for use with the DRV8835 Motor Driver IC in `PH/EN` mode.

Note: alter LEDs should be controlled by Car obj when turning/stopping/reversing etc.
- [] a neat feature would be to allow a config variable (and config file) to translate duty (bits) from real-world movement


'''
import gpiozero as GPIO
from actuation_models import SteeringModels, ManueverType
from pca9685 import QwiicPCA9685
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
		# todo: assert steering_model is valid

		self._is_debug_mode = _is_debug_mode
		self.i2c_driver = QwiicPCA9685(0x40, debug = True)

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

		self.are_motors_reverse_mounted = 1 if are_motors_reverse_mounted else 0
			# used to toggle phase
		self.steering_model = steering_model

		self.motor_fl_direction = 1
		self.motor_fr_direction = 1
		self.motor_rl_direction = 1
		self.motor_rr_direction = 1

	def __enter__(self):
		return self

	def __exit__(self) -> None:
		self._teardown()

	def _setup_GPIO_pin(self) -> None:
		'''
		'''
		raise NotImplementedError
	
	def _teardown(self) -> None:
		self.stop()

		for pin_id in self.travelling_motors_pins_list:
			if pin_id is not None:
				GPIO.cleanup(pin_id)
	
	def _send_debug_message(method_name, speed_in_duty, manuever, is_reversing) -> None:
		# later generalize this
		direction_str = "backwards" if is_reversing else ""
		print(f'TravelMotor()::{method_name}()::manuever: {manuever}@{speed_in_duty} {direction_str}')

	def crab_walk_motor_setup() -> None:
		'''
		'''
		raise NotImplementedError

	def bound_motor_duty(self, duty: int = 0) -> int:
		'''
			Sets valid duty cycle
		'''
		duty = duty if duty >= 0 else abs(duty)
		duty = duty if duty < I2C_MAX_BITS else I2C_MAX_BITS

		return duty

	def drive(self,
		   front_left_motor_duty: int,
		   front_right_motor_duty: int,
		   rear_left_motor_duty: int,
		   rear_right_motor_duty: int) -> None:
		# requires i2c connection 
		'''
		'''
		raise NotImplementedError

	def stop(self) -> None:
		'''
		'''
		raise NotImplementedError

	def maintain_lane(self) -> None:
		# do later and figure out how to integrate with `turn_right` and `turn_left`
		'''
		'''
		raise NotImplementedError

	def turn_right(self) -> None:
		'''
		'''
		raise NotImplementedError

	def turn_left(self) -> None:
		'''
		'''
		raise NotImplementedError
	
	def move(self, 
		  speed_in_duty: int = 0,
		  manuever: ManueverType = ManueverType.STRAIGHT,
		  is_reversing: bool = False) -> None:

		speed_in_duty = self.bound_motor_duty(speed_in_duty)
		if self._is_debug_mode:
			self._send_debug_message('move', speed_in_duty, manuever, is_reversing)

		if (speed_in_duty == 0):
			self.stop()
		else:
			# 
			pass

		raise NotImplementedError

def main():
	pass

if __name__ == '__main__':
	main()