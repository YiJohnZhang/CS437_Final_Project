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

from random import randint
from time import sleep, time
from config import GENERAL_SETTINGS, ULTRASONIC_SENSOR_SETTINGS
import RPi.GPIO as GPIO
'''
Note: need to write a low-level library compatible with OPi, e.g.:
import OPi.GPIO as GPIO
Also need mangopi's equivalent gpio library

'''
_IS_DEBUG_MODE = GENERAL_SETTINGS['IS_DEBUG_MODE']

DEFAULT_SPEED_OF_SOUND = ULTRASONIC_SENSOR_SETTINGS['DEFAULT_SPEED_OF_SOUND']
DEFAULT_AMBIENT_TEMPERATURE = ULTRASONIC_SENSOR_SETTINGS['DEFAULT_TEMPERATURE']
DEFAULT_TRIGGER_PIN = ULTRASONIC_SENSOR_SETTINGS['DEFAULT_TRIG_PIN']
MINIMUM_DISTANCE_MM = ULTRASONIC_SENSOR_SETTINGS['MINIMUM_DETECTION_DISTANCE']
MAXIMUM_DISTANCE_MM = ULTRASONIC_SENSOR_SETTINGS['MAXIMUM_DETECTION_DISTANCE']
TRIGGER_PULSE_TIME_LENGTH = ULTRASONIC_SENSOR_SETTINGS['TRIGGER_PULSE_TIME_LENGTH']
SETUP_SETTLING_TIME = ULTRASONIC_SENSOR_SETTINGS['SETUP_SETTLING_TIME']

class UltrasonicSensor:
	def __init__(self, trigger_pin: int = DEFAULT_TRIGGER_PIN, 
			  min_distance_cm: float = MINIMUM_DISTANCE_MM, 
			  max_distance_cm: float = MAXIMUM_DISTANCE_MM, 
			  echo_pin: int = None, thermostat_object = None, 
			  frequency_hop_range: tuple[int] = (),				# kHz
			  _is_debug_mode: bool = _IS_DEBUG_MODE):
		'''
			Initialize `UltrasonicSensor` object
		'''
		if (min_distance_cm == 0):
			raise Exception(f'UltrasonicSensor::__init__():: cannot set minimum distance to be {min_distance_cm} cm')
		
		if (max_distance_cm < min_distance_cm):
			raise Exception(f'UltrasonicSensor::__init__():: cannot set max. distance ({max_distance_cm}) to be less than min. distance ({min_distance_cm})')

		self.echo_pin = trigger_pin if echo_pin is None else echo_pin
		self.trigger_pin = trigger_pin
		self.min_distance_cm = min_distance_cm
		self.max_distance_cm = max_distance_cm
		self.thermostat = thermostat_object

		# for a frequency hop enabled sensor
		self.frequency_hop_range = frequency_hop_range
		self.is_frequency_hop_mode = len(self.frequency_hop_range) > 1
		
		self._is_debug_mode = _is_debug_mode

		# if (self.trigger_pin == self.echo_pin):
		# todo: need to set a minimum distance for trig->echo handover; if t compesnated calculate minimum distance sensed using some kind of get speed fn

		self._setup_GPIO_pin()
		time.sleep(SETUP_SETTLING_TIME)

	def __enter__(self):
		return self

	def __exit__(self) -> None:
		self.teardown()

	def _setup_GPIO_pin(self) -> None:
		GPIO.setup(channel = self.trigger_pin, dir = GPIO.OUT, pull_up_down = GPIO.PUD_DOWN)
		GPIO.output(self.trigger_pin, False)

		if (self.trigger_pin != self.echo_pin):
				GPIO.setup(channel = self.echo_pin, dir = GPIO.IN, pull_up_down = GPIO.PUD_OFF)
	
	def teardown(self) -> None:
		# Lifecycle Method: Release GPIO resources
		GPIO.cleanup(self.trigger_pin)
		if (self.echo_pin != self.trigger_pin):
			GPIO.cleanup(self.echo_pin)
		
	def return_random_frequency(self, start_frequency_kHz: int = 40, end_frequency_kHz: int = 40, frequency_step_kHz: int = 5):
		'''
			Return a random frequency within this interval, uniform.
			For frequency hopping.	
		'''
		return_frequency = start_frequency_kHz

		if start_frequency_kHz != end_frequency_kHz:
			frequency_range = range(start_frequency_kHz, end_frequency_kHz, frequency_step_kHz)
			return_frequency_index = randint(0, len(frequency_range))
			return_frequency = frequency_range[return_frequency_index]
		
		return return_frequency

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
				GPIO.setup(channel = self.echo_pin, dir = GPIO.IN, pull_up_down = GPIO.PUD_OFF)

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
				if (not self._is_debug_mode):
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
	CURRENT_SCOPE = 'ultrasonic_sensor.py::main()::'
	ultrasonic_object_1 = UltrasonicSensor(18)
	ultrasonic_object_2 = UltrasonicSensor(14)

	try:
		print(f'{CURRENT_SCOPE}{ultrasonic_object_1.return_distance()}')
		print(f'{CURRENT_SCOPE}{ultrasonic_object_2.return_distance()}')

	except KeyboardInterrupt:
		print(f'{CURRENT_SCOPE}program interrupted')
	
	finally:
		ultrasonic_object_1.teardown()
		ultrasonic_object_2.teardown()


if __name__ == '__main__':
	main()