# CS437_Final_Project
rPi Car Codebase

# Todo
- [x] `ultrasonic.py`
- [x] `pca9685.py` (eventually switch to PCA9634PW or **TLC59108F**; currently using [Sparkfun QWIIC PCA9685](https://github.com/sparkfun/qwiic_pca9685_py/blob/main/qwiic_pca9685.py))
- [ ] `travel_motor.py` (using **DRV8835DSSR**)
- [ ] 
- [ ] `camera.py` (consider using [`vilib.py` from sunfounder (GPL-2.0)?](https://github.com/sunfounder/vilib/blob/main/vilib/vilib.py))
- [ ] `main.py`
- [ ] `thermostat.py`? (if entirely digital, o.w. abandon if analog b/c needs adc)
- [ ] `line_detector.py` (optional: for fun)
- [ ] `tcp_server.py` (optional: this our lab 2 code, [CS437 Lab 02](https://github.com/YiJohnZhang/CS437_IoT_Labs/tree/main/CS437_L02))
- [ ] **Bonus**: `servomotor.py`

# Structure
```sh

```
## Dependency Map
Most libraries are anticipated to (in)directly depend on a `GPIO`-equivalent library.

### Module-Independent Modules
- `ultrasonic.py`
- `travel_motor.py`
- i2c_driver (`pca9685.py` / `tlc59108f.py`)
- `thermostat.py` (if entirely digital, o.w. abandon if analog b/c needs adc)
- `line_detector.py`

### Module-Dependent Modules
- `tcp_server.py`
- `servomotor.py`: i2c_driver
- `main.py`: all (but `tcp_server.py`?)

# Notes
## Current Dependencies
- `sparkfun-qwiic-pca9685`

## Quick References
https://github.com/sparkfun/qwiic_pca9685_py/blob/main/qwiic_pca9685.py

# Future Developments
- [ ] Remove all external dependencies
	- [ ] Develop a `TLC59108F` library
	- [ ]
- `adc.py`: potentially use `TM7711` (24-bit)/`ADS7830` (8-bit)
- `photodector.py`: detects ambient light levels (needs `ADS7830`); depends on an `adc` library
- `buzzer.py`/`speaker.py`: plays sound
- `lighting.py`: controls taillights/headlights/indicators. depends on `photodetector.py`, `buzzer.py`/`speaker.py`
- 