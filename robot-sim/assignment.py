from __future__ import print_function

import time
from sr.robot import *


R = Robot()
t = 1 # action time
a_th = 4.0 # angle threshold
d_th = 0.4 # distance threshold
collected_tokens = [] # array to store collected silver tokens
visited_checkpoints = [] # array to store visited gold tokens

# lambda to delay actions
delay = lambda x : time.sleep(x)


# drive the robot forward/backwards
def drive(speed, seconds):
	R.motors[0].m0.power = speed
	R.motors[0].m1.power = speed
	delay(seconds)
	R.motors[0].m0.power = 0
	R.motors[0].m1.power = 0


# turn the robot left/right
def turn(speed, seconds):
	R.motors[0].m0.power = speed
	R.motors[0].m1.power = -speed
	delay(seconds)
	R.motors[0].m0.power = 0
	R.motors[0].m1.power = 0


# search for tokens and return distance, angle e code of the nearest token that asn't already been delpoyed
def find_token(token_type, visited_tokens):
	dist = 100
	rot_y = 0
	token_code = -1

	for token in R.see():
		if (token.dist < dist) and (token.info.marker_type is token_type) and (token.info.code not in visited_tokens):
			dist = token.dist
			token_code = token.info.code
			rot_y = token.rot_y

	if dist >= 100:
		print('No token in range')
		return -1, -1, token_code
	else:
		return dist, rot_y, token_code


# update position of the robot in respect of the given token
def update_pos(target_code):
	for token in R.see():
		if token.info.code == target_code:
			return token.dist, token.rot_y
	return -1, -1


# bring the grabbed silver token near to a gold token
def bring_to_checkpoint(token_code):
	checkpoint = False
	lock = False
	checkpoint_code = -1
	e = 1

	while not checkpoint:
		if not lock:
			dist, rot_y, checkpoint_code = find_token(MARKER_TOKEN_GOLD, visited_checkpoints)
			while dist == -1 or checkpoint_code == -1:
				turn(30*e, t)
				drive(30*e, t)
				dist, rot_y, checkpoint_code = find_token(MARKER_TOKEN_GOLD, visited_checkpoints)
				if checkpoint_code != -1:
					print('Locked gold token ' + str(checkpoint_code))
				else:
					print('No gold token in range')
				e += 0.2
				delay(1)
		else:
			print('Delivering to gold token ' + str(checkpoint_code))
			dist, rot_y = update_pos(checkpoint_code)

		e = 1
		lock = True

		if dist < d_th * 1.5:
			checkpoint = True
			R.release()
			collected_tokens.append(token_code)
			visited_checkpoints.append(checkpoint_code)
			lock = False
		elif rot_y < -a_th:
			turn(-2, t)
		elif rot_y > a_th:
			turn(2, t)
		else:
			drive(30, t)


# locate a silver token, grab it and deploy it to a gold token
def collect_silver_tokens(n_tokens):
	drive(40, t*3)
	delay(1)

	lock = False
	token_code = -1
	e = 1

	while n_tokens > 0:
		if not lock:
			dist, rot_y, token_code = find_token(MARKER_TOKEN_SILVER, collected_tokens)
		else:
			dist, rot_y = update_pos(token_code)

		while dist == -1 or token_code == -1:
			turn(30*e, t)
			drive(30*e, t)
			dist, rot_y, token_code = find_token(MARKER_TOKEN_SILVER, collected_tokens)
			if token_code != -1:
				print('Locked token ' + str(token_code))
			else:
				print('No silver token in range')
			delay(1)
			e += 0.2
		
		e = 1
		lock = True

		if dist < d_th:
			if R.grab():
				print('Grabbed token ' + str(token_code))
				delay(0.5)
				print('Delivering token ' + str(token_code))
				drive(-30, t)
				turn(30, t)
				bring_to_checkpoint(token_code)
				n_tokens -= 1
				drive(-30, t)
				turn(45, t)
				lock = False
			else:
				print('[ERROR] Unable to grab token!')
				exit()
		elif rot_y < -a_th:
			turn(-2, t)
		elif rot_y > a_th:
			turn(2, t)
		else:
			drive(30, t)


# collect 6 silver tokens and take every token near to a gold token
collect_silver_tokens(6)
print('All tokens delivered successfully!')