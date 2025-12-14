'''
Steering models available for this kit.
'''
from enum import Enum

class SteeringModels(Enum):
	'''
		crab walking: all wheels skid to turn
		mecanum: can turn in place
		single pivoting axle: typical car design, note the wheels of the non-pivoting axle for this kit will slip b/c there is no differential
		dual pivoting axle: high-end car designs
	'''
	CRAB_WALKING = 1
	MECANUM = 2
	SINGLE_PIVOTING_AXLE = 3
	DUAL_PIVOTING_AXLE = 4

class ManueverType(Enum):
	'''
		straight: don't turn
		turn left: ...
		turn right: ...
		maintain lane: maybe use line sensor OR camera to maintain lane (note camera is the most weather independent)
	'''
	STRAIGHT = 1
	TURN_LEFT = 2
	TURN_RIGHT = 3
	MAINTAIN_LANE = 4
		# for self-driving only; use in conjunction with a line detector library
		# probably needs a dedicated thread?
	
	EMERGENCY_BRAKE = 5
		# not implemented, but the idea is to mimic ABS?