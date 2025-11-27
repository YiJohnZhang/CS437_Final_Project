'''
Designed for use with the DRV8835 Motor Driver IC.

Note: alter LEDs should be controlled by Car obj when turning/stopping/reversing etc.
- [] a neat feature would be to allow a config variable (and config file) to translate duty (bits) from real-world movement

'''
import gpiozero as GPIO
from actuation_models import SteeringModels, ManueverType

# expose to potential `config` file
I2C_BIT_RESOLUTION = 12				# set depending on I2C driver used
I2C_MAX_BITS = 2 ** I2C_BIT_RESOLUTION - 1
ARE_MOTORS_REVERSE_MOUNTED = False

DEFAULT_FRONT_LEFT_MOTOR_PIN = 26
DEFAULT_FRONT_RIGHT_MOTOR_PIN = 5
DEFAULT_REAR_LEFT_MOTOR_PIN = 16
DEFAULT_REAR_RIGHT_MOTOR_PIN = 5

class TravelMotor:
	def __init__(self, 
			  front_left_motor_pin: int = DEFAULT_FRONT_LEFT_MOTOR_PIN,
			  front_right_motor_pin: int  = DEFAULT_FRONT_RIGHT_MOTOR_PIN,
			  rear_left_motor_pin: int  = DEFAULT_REAR_LEFT_MOTOR_PIN,
			  rear_right_motor_pin: int  = DEFAULT_REAR_RIGHT_MOTOR_PIN,
			  are_motors_reverse_mounted: bool = ARE_MOTORS_REVERSE_MOUNTED,
			  steering_model: SteeringModels = SteeringModels.CRAB_WALKING,
			  _is_debug_mode: bool = False
			  ):
		'''

		'''
		# todo: assert steering_model is valid

		self._is_debug_mode = _is_debug_mode

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

		self.motor_fl_direction = 1
		self.motor_fr_direction = 1
		self.motor_rl_direction = 1
		self.motor_rr_direction = 1

	def __enter__(self):
		return self

	def __exit__(self) -> None:
		self._teardown()

	def _setup_GPIO_pin(self):
		pass
	
	def _teardown(self) -> None:
		self.stop()

		for pin_id in self.travelling_motors_pins_list:
			if pin_id is not None:
				GPIO.cleanup(pin_id)
	
	def _send_debug_message(method_name, speed_in_duty, manuever, is_reversing) -> None:
		# later generalize this
		direction_str = "backwards" if is_reversing else ""
		print(f'TravelMotor()::{method_name}()::manuever: {manuever}@{speed_in_duty} {direction_str}')

	def crab_walk_motor_setup():
		pass

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

		pass

	def stop(self) -> None:

		pass

	def maintain_lane(self) -> None:
		# do later and figure out how to integrate with `turn_right` and `turn_left`
		pass

	def turn_right(self) -> None:
		
		pass

	def turn_left(self) -> None:
		
		pass
	
	def move(self, speed_in_duty: int = 0,
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

		pass

def main():
	pass

if __name__ == '__main__':
	main()