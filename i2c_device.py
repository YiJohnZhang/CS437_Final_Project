'''
Currently for PCA9685. Written to be configurable b/c anticipating to replace with tlc59108f

Python 3 I2C smbus lib Documentation: https://pypi.org/project/smbus3/
I2C smbus Documentation: https://www.kernel.org/doc/html/v4.13/driver-api/i2c.html

'''
from math import floor
from time import sleep
from smbus3 import SMBus

from config import GENERAL_SETTINGS, GENERAL_I2C_DEVICE_SETTINGS, GENERAL_I2C_PWM_DRIVER_SETTINGS, MAIN_I2C_DRIVER_CHANNEL_CONSTANTS

_IS_DEBUG_MODE = GENERAL_SETTINGS['_IS_DEBUG_MODE']
I2C_DRIVER_MAX_BITS = GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_MAX_BITS']


config_i2c_device_name = GENERAL_I2C_DEVICE_SETTINGS['I2C_DRIVER_DEVICE_NAME']
I2C_DRIVER_DEVICE_NAME = config_i2c_device_name if ((type(config_i2c_device_name) == str) and (len(config_i2c_device_name) > 0)) else 'Generic I2C PWM Driver'
I2C_CHANNEL = GENERAL_I2C_DEVICE_SETTINGS['I2C_BUS_CHANNEL_NUMBER']
DEFAULT_DEVICE_ADDRESS = GENERAL_I2C_DEVICE_SETTINGS['DEFAULT_I2C_DEVICE_ADDRESS']

LSB_MASK = 0XFF
MSB_MASK_BIT_SHIFTS = 8

class I2C_Device:

	def __init__(self, device_address: int = DEFAULT_DEVICE_ADDRESS, 
			  _is_debug_mode: bool = _IS_DEBUG_MODE, device_name: str = None):
		self.smbus_obj = SMBus(I2C_CHANNEL)
		self.device_address = device_address
		self._is_debug_mode = _is_debug_mode
		self.device_name = device_name or I2C_DRIVER_DEVICE_NAME
	
	def __enter__(self):
		return self

	def __exit__(self) -> None:
		self._teardown()

	def _debug(self, method_name: str, message: str, class_name: str = 'I2C_Device') -> None:
		if self._is_debug_mode:
			print(f'{class_name}::{method_name}::{message}')

	def _teardown(self) -> None:
		'''
			Teardown the object
			[Example 1a](https://pypi.org/project/smbus3/)
		'''
		self.smbus_obj.close()

	def _read_from_register(self, register_address: int) -> int:
		'''
			Reads from a given `register_address`.
			[Example 1a](https://pypi.org/project/smbus3/)
		'''
		return self.smbus_obj.read_byte_data(self.device_address, register_address)
		## return self.smbus_obj.read_byte_data(self.device_address, register_address, 0)
	
	def _write_value_to_register(self, register_address: int, data: int) -> None:
		'''
			Writers to a given `register_address`.
			[Example 3](https://pypi.org/project/smbus3/)
		'''		
		self.smbus_obj.write_byte_data(self.device_address, register_address, data)
	
	def bound_duty_cycle(self, input_duty_cycle: int) -> int:
		output_duty_cycle = input_duty_cycle

		'''
		if self._is_debug_mode:
			if output_duty_cycle < 0:
				raise ValueError(f'I2C_Device::bound_duty_cycle()::{input_duty_cycle} < 0')
		'''
		output_duty_cycle = abs(output_duty_cycle)

		if self._is_debug_mode:
			if output_duty_cycle > I2C_DRIVER_MAX_BITS:
				raise ValueError(f'I2C_Device::bound_duty_cycle()::{input_duty_cycle} > max bits ({I2C_DRIVER_MAX_BITS})')
		output_duty_cycle = output_duty_cycle if output_duty_cycle < I2C_DRIVER_MAX_BITS else I2C_DRIVER_MAX_BITS
		
		return output_duty_cycle
	
	def read(self, register_address: int) -> int:
		'''
		'''
		read_value = self._read_from_register(register_address)
		self._debug('_read_from_register', f'read {read_value} from reg{register_address}@{self.device_address}')

		return read_value
	
	def write(self, register_address: int, data: int) -> None:
		'''
		just a nicer name to call I guess ¯\_(ツ)_/¯
		'''
		self._debug('write', f'writing {data} to reg{register_address}@{self.device_address}')
			# can `import inspect` and do `inspect.currentframe().f_code_co_name`
			# Source: https://stackoverflow.com/a/1140513

		self._write_value_to_register(register_address = register_address, data = data)

	def write_pwm(self, register_address: int, data: int) -> None:
		'''
			Expect subclasses to implement this where applicable.
		'''
		raise NotImplementedError

class PCA9685_PWM_Driver(I2C_Device):

	# PCA9685 Constants
	_MODE1				= 0x00	# 7.3.1
	_MODE2				= 0x01	# 7.3.2
	_SUBADR1			= 0x02	# 7.3.6
	_SUBADR2			= 0x03	# ""
	_SUBADR3			= 0x04	# ""
	_ALLLED_OFF_LSB		= 0xFC	# 7.3.4 Table 8
	_ALLLED_OFF_MSB		= 0xFD	# 7.3.4 Table 8
	_PRESCALE			= 0xFE	# 7.3.4 Table 8

	_CHANNEL_0_ON_LSB	= 0x06	# 7.3.3 Table 7
	_CHANNEL_0_ON_MSB	= 0x07	# 7.3.3 Table 7
	_CHANNEL_0_OFF_LSB	= 0x08	# 7.3.3 Table 7
	_CHANNEL_0_OFF_MSB	= 0x09	# 7.3.3 Table 7

	def __init__(self, address: int = 0x40, global_frequency: int = 50, name: str = None):
		super().__init__(self, device_address = address or DEFAULT_DEVICE_ADDRESS, 
			  _is_debug_mode = _IS_DEBUG_MODE, device_name = name or 'PCA9685_Main')
		# ...

		self._frequency = global_frequency
		self._set_frequency()
		# note one reason for migration is that PCA9685 has a 
		# global frequency setting, each channel cannot be independently set
	
	def _set_frequency(self, frequency: int = None) -> None:
		'''
			Default: 50 Hz
			[PWM frequency PRE_SCALE](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf) 7.3.5
		'''
		OSCILLATOR_CLOCK_FREQUENCY = 25000000.0		# internal clock is default 25 MHz (pp1)

		frequency = frequency if frequency else self._frequency

		prescale_value = OSCILLATOR_CLOCK_FREQUENCY / 4096.0
			# TODO: magic ##: 4096 b/c 12-bits
		prescale_value /= float(frequency)
		prescale_value -= 1.0
		prescale_value = int(floor(prescale_value + 0.5))
		self._debug('_setup_frequency', f'prescale_value is: {prescale_value}', 'PCA9685')

		# bunch of code from https://github.com/sunfounder/SunFounder_PCA9685/blob/master/PCA9685.py
		old_mode = self.read(self._MODE1)
		new_mode = (old_mode & 0x7F) | 0x10
		self.write(self._MODE1, new_mode)
		self.write(self._PRESCALE, prescale_value)

		self.write(self._MODE1, old_mode)
		sleep(0.005)
		self.write(self._MODE1, old_mode | 0x80)
	
	def two_byte_parser(self, unsigned_double_byte: int):
		'''
			Extracts the least significant byte (LSB) and most significant byte (MSB) from a double byte.
			Method useful for PCA9685.
		'''
		LSB = unsigned_double_byte & LSB_MASK
		MSB = unsigned_double_byte >> MSB_MASK_BIT_SHIFTS
		return LSB, MSB
	
	def write_pwm(self, channel: int, off_step: int, on_step: int = 0) -> None:
		on_LSB, on_MSB = self.two_byte_parser(on_step)
		off_LSB, off_MSB = self.two_byte_parser(off_step)
		
		self.write(self._CHANNEL_0_ON_LSB + 4 * channel, on_LSB)
		self.write(self._CHANNEL_0_ON_MSB + 4 * channel, on_MSB)
		self.write(self._CHANNEL_0_OFF_LSB + 4 * channel, off_LSB)
		self.write(self._CHANNEL_0_OFF_MSB + 4 * channel, off_MSB)

	def set_motor_pwm(self, channel: int, duty_cycle: int) -> None:
		self.write_pwm(channel, duty_cycle)
	
	def set_servomotor_pwm(self, channel: int, pulse: int) -> None:
		'''
		Note: servomotor pulse needs to be at a frequency of 50 Hz
		'''
		pulse = pulse * 4096 // 20000
			# TODO: magic ##: 4096 is resolution for 12-bits
			# TODO: magic ##: Servomotors like 50 Hz; 20k us is time period for that		
		self.write_pwm(channel, pulse)

class ATMEGA328P_DEVICE(I2C_Device):
	# TODO: prototype for our first MCU I2C slave, before moving onto less-documented CH592F
	pass

class CH592F_Device(I2C_Device):
	# TODO: for later versions when we I2C slave the MCU
	pass

'''
class TLC59108F_PWM_Driver(I2C_Device):

	# TLC59108F Constants
	_MODE1		= 0x00	# 8.6.2
	_MODE2		= 0x01	# 8.6.3
	_SUBADR1	= 0x0E	# 8.6.8
	_SUBADR2	= 0x0F	# 8.6.8
	_SUBADR3	= 0x10	# 8.6.8
	_CHANNEL_0	= 0x02	# 8.6.4
	_ALLCALLADR = 0x11	# 8.6.9 (turn off for all)
	_GRPFREQ	= 0x0B	# 8.6.6

	def __init__(self):
		super().__init__(self, device_address = DEFAULT_DEVICE_ADDRESS, 
			  _is_debug_mode = _IS_DEBUG_MODE, device_name = 'TLC59108F_Main')
		# ...
	
	def write(self, channel: int, data: int) -> None:
		raise NotImplementedError
'''