'''
To make the code as hardware agnostic as possible, we re-implemented 
the `DistanceSensor` class using only the `GPIO` library.

We added optional temperature compensation for calculating distance.
For cost measure and pin economy, we have developed it to work with
a common TRIG-ECHO pin topology. 

Todo:
- [] select between TMP102 / DS18B20T; expects `get_temperature()` method
- [] decide: do I need to use `lock`? should I allow concurrent triggers OR 
	should I just assume they do it sequentially; or add multi-threading?
	- concurrent triggers: noisy
	- a even greedier implementation: shared echo and trig pin for all, use MUX to determine which sensor it is connected to
- [] add optional humidity compensation


'''

# RaspberryPi
import gpiozero as GPIO
'''
Note: need to write a low-level library compatible with OPi, e.g.:
import OPi.GPIO as GPIO
Also need mangopi's equivalent gpio library

'''
from time import sleep, time

DEFAULT_AMBIENT_TEMPERATURE = 298.15	# [K]
DEFAULT_SPEED_OF_SOUND = 346.2			# [m/s]: 298.15 K, 1 atm, dry air
DEFAULT_TRIGGER_PIN = 18
MINIMUM_DISTANCE_MM = 2.5
MAXIMUM_DISTANCE_MM = 3000.0
TRIGGER_PULSE_TIME_LENGTH = 0.00001		# 10 us (10 us if 40 kHz)
SETUP_SETTLING_TIME = 0.5				# 0.5 s

class UltrasonicSensor:
	def __init__(self, trigger_pin: int = DEFAULT_TRIGGER_PIN, 
			  min_distance_cm: float = MINIMUM_DISTANCE_MM, 
			  max_distance_cm: float = MAXIMUM_DISTANCE_MM, 
			  echo_pin: int = None, thermostat_object = None, 
			  _debug_is_no_object_detected_ignored: bool = True):
		'''
			Initialize `UltrasonicSensor` object


		'''
		if (min_distance_cm == 0):
			raise Exception(f'UltrasonicSensor::__init__():: cannot set minimum distance to be {min_distance_cm} cm')
		

		self.echo_pin = trigger_pin if echo_pin is None else echo_pin
		self.trigger_pin = trigger_pin
		self.min_distance_cm = min_distance_cm
		self.max_distance_cm = max_distance_cm
		self.thermostat = thermostat_object
		
		self._debug_is_no_object_detected_ignored = _debug_is_no_object_detected_ignored

		# if (self.trigger_pin == self.echo_pin):
		# todo: need to set a minimum distance for trig->echo handover; if t compesnated calculate minimum distance sensed using some kind of get speed fn

		self._setup_GPIO_pin()
		time.sleep(SETUP_SETTLING_TIME)

	def __enter__(self):
		return self

	def __exit__(self) -> None:
		self.teardown()

	def _setup_GPIO_pin(self) -> None:
		GPIO.setup(self.trigger_pin, GPIO.OUT)
		GPIO.output(self.trigger_pin, False)

		if (self.trigger_pin != self.echo_pin):
			GPIO.setup(self.echo_pin, GPIO.IN)
	
	def teardown(self) -> None:
		# Lifecycle Method: Release GPIO resources
		GPIO.cleanup(self.trigger_pin)
		if (self.echo_pin != self.trigger_pin):
			GPIO.cleanup(self.echo_pin)

	def get_speed_of_sound_in_dry_air(self, temperature: int = DEFAULT_AMBIENT_TEMPERATURE) -> float:
		'''
			Equation Source: https://www.engineeringtoolbox.com/air-speed-sound-d_603.html
			v = 20.05 * \sqrt{T}
			- v [=] [m/s]
			- T [=] K

			# doctests (0 C, 25 C, 40 C)
			>>> get_speed_of_sound_in_dry_air(273.15)
			331.371
			>>> get_speed_of_sound_in_dry_air(298.15)
			346.204
			>>> get_speed_of_sound_in_dry_air(313.15)
			354.806
		'''
		return round(20.05 * (temperature ** 0.5), 3)

	def return_distance(self, significant_figures: int = 2) -> float:
		'''
			Returns the distance [cm] of an object to the ultrasonic sensor.
			Optional temperature compensation built in.

			Convention:
			- `None`: no object detected (either too close or too far)
			- `float` otherwise
		'''
		distance = None
		ambient_temperature = DEFAULT_AMBIENT_TEMPERATURE if self.thermostat is None else self.thermostat.get_temperature()

		speed_of_sound = self.get_speed_of_sound_in_dry_air(ambient_temperature) if (self.thermostat is not None) else DEFAULT_SPEED_OF_SOUND
			# [m/s]
		
		speed_of_sound_cm_s = speed_of_sound * 100
			# [cm/s]
		timeout_time_length = 2 * self.max_distance_cm / speed_of_sound_cm_s
			# magic ## 2 to compensate for double distance travelled
		
		try:
			is_echo_timed_out = False
			pulse_start_time = pulse_end_time = None
			echo_timeout_time = time() + TRIGGER_PULSE_TIME_LENGTH + timeout_time_length
			
			GPIO.output(self.trigger_pin, True)
			sleep(TRIGGER_PULSE_TIME_LENGTH)
			GPIO.output(self.trigger_pin, False)

			if (self.trigger_pin == self.echo_pin):
				GPIO.setup(self.echo_pin, GPIO.IN)

			# wait for echo
			while ((GPIO.input(self.echo_pin) == 0) and (not is_echo_timed_out)):
				pulse_start_time = time()
				if (pulse_start_time > echo_timeout_time):
					is_echo_timed_out = True
			
			while ((GPIO.input(self.echo_pin) == 1) and (not is_echo_timed_out)):
				pulse_end_time = time()
				if (pulse_start_time > echo_timeout_time):
					is_echo_timed_out = True

			# calculate distance	
			if (is_echo_timed_out):
				if (not self._debug_is_no_object_detected_ignored):
					raise Exception(f'no object detected!')
			else:
				pulse_duration = pulse_end_time - pulse_start_time
				distance = speed_of_sound_cm_s * pulse_duration / 2
					# magic ## 2 to compensate for double distance travelled

		except Exception as e:
			print(f'UltrasonicSensor::get_distance()::{e}')

		self._setup_GPIO_pin()
		return round(distance, significant_figures)
	
def main():
	pass


if __name__ == '__main__':
	main()