'''
Currently for PCA9685. Written to be configurable b/c anticipating to replace with tlc59108f

Python 3 I2C smbus lib Documentation: https://pypi.org/project/smbus3/
I2C smbus Documentation: https://www.kernel.org/doc/html/v4.13/driver-api/i2c.html

'''
from time import sleep
from smbus3 import SMBus

from config import GENERAL_SETTINGS, GENERAL_I2C_PWM_DRIVER_SETTINGS, MAIN_I2C_DRIVER_CHANNEL_CONSTANTS

_IS_DEBUG_MODE = GENERAL_SETTINGS['_IS_DEBUG_MODE']
I2C_DRIVER_MAX_BITS = GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_MAX_BITS']


config_i2c_device_name = GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_DRIVER_DEVICE_NAME']
I2C_DRIVER_DEVICE_NAME = config_i2c_device_name if ((type(config_i2c_device_name) == str) and (len(config_i2c_device_name) > 0)) else 'Generic I2C PWM Driver'
I2C_CHANNEL = GENERAL_I2C_PWM_DRIVER_SETTINGS['I2C_BUS_CHANNEL_NUMBER']
DEFAULT_DEVICE_ADDRESS = GENERAL_I2C_PWM_DRIVER_SETTINGS['DEFAULT_I2C_DEVICE_ADDRESS']

LSB_MASK = 0XFF
MSB_MASK_BIT_SHIFTS = 8

class I2C_PWM_Driver:

	def __init__(self, device_address: int = DEFAULT_DEVICE_ADDRESS, 
			  _is_debug_mode: bool = _IS_DEBUG_MODE, device_name: str = None):
		self.smbus_obj = SMBus(I2C_CHANNEL)
		self.device_address = device_address
		self._is_debug_mode = _is_debug_mode
		self.device_name = device_name or I2C_DRIVER_DEVICE_NAME
	
	def __exit__(self) -> None:
		self._teardown()

	def _teardown(self) -> None:
		'''
			Teardown the object
			[Example 1a](https://pypi.org/project/smbus3/)
		'''
		self.smbus_obj.close()

	def _print_debug_message(self, register_address: int, method_name: str, 
						  operation_string: str) -> None:
		print(f'I2C_PWM_DRIVER::{method_name}():: {operation_string} {self.device_address}(@{self.device_address}) reg {register_address}')

	def _setup_frequency(self) -> None:
		'''
		
			[PWM frequency PRE_SCALE](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf) 7.3.5
		'''
		raise NotImplementedError

	def _read_from_register(self, register_address: int) -> int:
		'''
			Reads from a given `register_address`.
			[Example 1a](https://pypi.org/project/smbus3/)
		'''
		read_value = self.smbus_obj.read_byte_data(self.device_address, register_address)

		if self._is_debug_mode:
			self._print_debug_message(register_address, '_read_from_register', f'read {read_value} from')

		return read_value

	def _write_value_to_register(self, register_address: int, data: int) -> None:
		'''
			Writers to a given `register_address`.
			[Example 3](https://pypi.org/project/smbus3/)
		'''
		if self._is_debug_mode:
			self._print_debug_message(register_address, '_write_value_to_register', f'writing {data} to')
				# can `import inspect` and do `inspect.currentframe().f_code_co_name`
				# Source: https://stackoverflow.com/a/1140513
		
		self.smbus_obj.write_byte_data(self.device_address, register_address, data)
	
	def bound_duty_cycle(self, input_duty_cycle: int) -> int:
		output_duty_cycle = input_duty_cycle

		if self._is_debug_mode:
			if output_duty_cycle < 0:
				raise ValueError(f'I2C_PWM_Driver::bound_duty_cycle()::{input_duty_cycle} < 0')
		output_duty_cycle = abs(output_duty_cycle)

		if self._is_debug_mode:
			if output_duty_cycle > I2C_DRIVER_MAX_BITS:
				raise ValueError(f'I2C_PWM_Driver::bound_duty_cycle()::{input_duty_cycle} > max bits ({I2C_DRIVER_MAX_BITS})')
		output_duty_cycle = output_duty_cycle if output_duty_cycle < I2C_DRIVER_MAX_BITS else I2C_DRIVER_MAX_BITS
		
		return output_duty_cycle

	def write(self, register_address: int, data: int) -> None:
		'''
			Expect subclasses to implement this.
		'''
		raise NotImplementedError
	
	def read(self, register_address: int) -> None:
		'''
			Expect subclasses to implement this.
		'''
		raise NotImplementedError

class PCA9685_PWM_Driver(I2C_PWM_Driver):

	# PCA9685 Constants
	_MODE1				= 0x00	# 7.3.1
	_MODE2				= 0x01	# 7.3.2
	_SUBADR1			= 0x02	# 7.3.6
	_SUBADR2			= 0x03	# ""
	_SUBADR3			= 0x04	# ""
	_CHANNEL_0_ON_LSB	= 0x06	# 7.3.3 Table 7
	_CHANNEL_0_ON_MSB	= 0x07	# 7.3.3 Table 7
	_CHANNEL_0_OFF_LSB	= 0x08	# 7.3.3 Table 7
	_CHANNEL_0_OFF_MSB	= 0x09	# 7.3.3 Table 7
	_ALLLED_OFF_LSB		= 0xFC	# 7.3.4 Table 8
	_ALLLED_OFF_MSB		= 0xFD	# 7.3.4 Table 8

	def __init__(self):
		super().__init__(self, device_address = DEFAULT_DEVICE_ADDRESS, 
			  _is_debug_mode = _IS_DEBUG_MODE, device_name = 'PCA9685_Main')
		# ...
	
	def two_byte_parser(self, unsigned_double_byte: int):
		'''
			Extracts the least significant byte (LSB) and most significant byte (MSB) from a double byte.
			Method useful for PCA9685.
		'''
		LSB = unsigned_double_byte & LSB_MASK
		MSB = unsigned_double_byte >> MSB_MASK_BIT_SHIFTS
		return MSB, LSB
	
	def write(self, channel: int, data: int) -> None:
		raise NotImplementedError
	
	def read(self, channel: int) -> None:
		raise NotImplementedError
	
class TLC59108F_PWM_Driver(I2C_PWM_Driver):

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
	
	def write(self):
		pass