# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

# Import required KLibs classes & functions.
import klibs
from klibs import P
from klibs.KLConstants import *
from klibs.KLExceptions import TrialException
from klibs.KLUtilities import deg_to_px
from klibs.KLKeyMap import KeyMap
from klibs.KLTime import CountDown
from klibs.KLUserInterface import ui_request, any_key, key_pressed
from klibs.KLGraphics import flip, blit, fill, clear
from klibs.KLGraphics.colorspaces import const_lum
from klibs.KLGraphics import KLDraw as kld 
from klibs.KLCommunication import message, user_queries, query
from klibs.KLResponseCollectors import ResponseCollector
from klibs.KLEventInterface import TrialEventTicket as ET

# Import additional required libraries
import random
import sdl2

# Define some useful constants
LEFT = "left"
RIGHT = "right"
PROBE = "probe"
TRAINING = "training"
HIGH = "high"
LOW = "low"
NEUTRAL = "neutral"
GO = "go"
NOGO = "nogo"
YES = "yes"
NO = "no"

# Define colours for the experiment
WHITE = [255, 255, 255, 255]
GREY = [100, 100, 100, 255]
BLACK = [0, 0, 0, 255]

class IOReward_E2(klibs.Experiment):

	def setup(self):
		# ---------------------------------- #
		# 		  Setup Stimuli      		 #
		# ---------------------------------- #

		# Set stimulus sizes 
		line_length =       deg_to_px(2)
		line_thickness =    deg_to_px(0.5)
		thick_rect_border = deg_to_px(0.7)
		thin_rect_border =  deg_to_px(0.3)
		fix_size =          deg_to_px(0.6)
		fix_thickness =     deg_to_px(0.1)
		square_size =       deg_to_px(3)
		large_text_size =   deg_to_px(0.65)

		# Stimulus layout
		box_offset = deg_to_px(8.0)
		self.left_box_loc =  (P.screen_c[0] - box_offset, P.screen_c[1])
		self.right_box_loc = (P.screen_c[0] + box_offset, P.screen_c[1])

		# Generate target colouring
		# Select target colours from randomly rotated colourwheel
		# ensuring those selected are unique and equidistant
		self.color_selecter = kld.ColorWheel(diameter=1, rotation=random.randrange(0,360))
		self.target_colours = []
		for i in (0,120,240):
			self.target_colours.append(self.color_selecter.color_from_angle(i))

		# Assign colours to payout valences
		random.shuffle(self.target_colours)
		self.high_value_colour =    self.target_colours[0]
		self.low_value_colour =     self.target_colours[1]
		self.neutral_value_colour = self.target_colours[2]

		# Initialize drawbjects
		self.thick_rect =    kld.Rectangle(square_size, stroke=[thick_rect_border, WHITE, STROKE_CENTER])
		self.thin_rect =     kld.Rectangle(square_size, stroke=[thin_rect_border, WHITE, STROKE_CENTER])

		self.high_val_rect = kld.Rectangle(square_size, stroke=[thin_rect_border, self.high_value_colour, STROKE_CENTER])
		self.low_val_rect =  kld.Rectangle(square_size, stroke=[thin_rect_border, self.low_value_colour, STROKE_CENTER])

		self.fixation =      kld.Asterisk(fix_size, fix_thickness, fill=WHITE)
		self.fix_cueback =   kld.Asterisk(fix_size*2, fix_thickness*2, fill=WHITE)
		
		self.go =            kld.FixationCross(fix_size, fix_thickness, fill=BLACK)
		self.nogo = 	     kld.FixationCross(fix_size, fix_thickness, fill=BLACK, rotation=45)

		self.flat_line =     kld.Rectangle(line_length, line_thickness, fill=BLACK)
		self.tilt_line =     kld.Rectangle(line_length, line_thickness, fill=BLACK, rotation=45)

		self.probe =         kld.Ellipse(int(0.75 * square_size))

		# ---------------------------------- #
		#   Setup other experiment factors   #
		# ---------------------------------- #
		
		# COTOA = Cue-Offset|Target-Onset Asynchrony 
		self.cotoa = 800 # ms
		self.feedback_exposure_period = 1.25 # sec

		# Training block payout variables
		self.high_payout_baseline = 12
		self.low_payout_baseline = 8
		self.total_score = None
		self.penalty = -5


		# ---------------------------------- #
		#     Setup Response Collectors      #
		# ---------------------------------- #
		
		# Initialize response collectors
		self.probe_rc =    ResponseCollector(uses=RC_KEYPRESS)
		self.training_rc = ResponseCollector(uses=RC_KEYPRESS)
		
		# Initialize ResponseCollector keymaps
		self.training_keymap = KeyMap(
			'training_response', # Name
			['z', '/'], # UI labels
			["left", "right"], # Data labels
			[sdl2.SDLK_z, sdl2.SDLK_SLASH] # SDL2 Keysyms
		)
		self.probe_keymap = KeyMap(
			'probe_response',
			['spacebar'],
			["pressed"],
			[sdl2.SDLK_SPACE]
		)

		# --------------------------------- #
		#     Setup Experiment Messages     #
		# --------------------------------- #
		
		# Make default font size larger
		self.txtm.add_style('myText',large_text_size, WHITE)

		err_txt =              "{0}\n\nPress any key to continue."
		lost_fixation_txt =    err_txt.format("Eyes moved! Please keep your eyes on the asterisk.")
		probe_timeout_txt =    err_txt.format("No response detected! Please respond as fast and as accurately as possible.")
		training_timeout_txt = err_txt.format("Line response timed out!")
		response_on_nogo_txt = err_txt.format("\'nogo\' signal (x) presented\nPlease only respond when you see "
			                   "the \'go\' signal (+).")
		
		self.err_msgs = {
			'fixation':         message(lost_fixation_txt, 'myText', align='center', blit_txt=False),
			'probe_timeout':    message(probe_timeout_txt, 'myText', align='center', blit_txt=False),
			'training_timeout': message(training_timeout_txt, 'myText', align='center', blit_txt=False),
			'response_on_nogo': message(response_on_nogo_txt, 'myText', align='center', blit_txt=False)
		}

		self.rest_break_txt =   err_txt.format("Whew! that was tricky eh? Go ahead and take a break before continuing.")
		self.end_of_block_txt = "You're done the first task! Please buzz the researcher to let them know!"

		# -------------------------------- #
		#     Setup Eyelink boundaries     #
		# -------------------------------- #
		fix_bounds = [P.screen_c, square_size/2]
		self.el.add_boundary('fixation', fix_bounds, CIRCLE_BOUNDARY)

		# --------------------------------- #
		# Insert training block (line task) #
		# --------------------------------- #
		if P.run_practice_blocks:
			self.insert_practice_block(1, trial_counts=P.trials_training_block)


	def block(self):
		# Show total score following completion of training task
		if self.total_score:
			fill()
			score_txt = "Total block score: {0} points!".format(self.total_score)
			msg = message(score_txt, 'myText', blit_txt=False)
			blit(msg, 5, P.screen_c)
			flip()
			any_key()

		self.total_score = 0 # Reset score once presented
		
		# Training task
		if P.practicing:
			self.block_type = TRAINING
			# Initialize selection counters
			self.high_value_trial_count = 0
			self.low_value_trial_count = 0

		# End of block messaging
		if not P.practicing:
			self.block_type = PROBE
			fill()
			msg = message(self.end_of_block_txt, 'myText', blit_txt=False)
			blit(msg, 5, P.screen_c)
			flip()
			any_key()

	def setup_response_collector(self):
		# Configure probe response collector
		self.probe_rc.terminate_after = [1500, TK_MS] # Waits 1.5s for response
		self.probe_rc.display_callback = self.probe_callback # Continuousy called when collection loop is initiated
		self.probe_rc.flip = True 
		self.probe_rc.keypress_listener.key_map = self.probe_keymap
		self.probe_rc.keypress_listener.interrupts = True # Abort collection loop once response made
		
		# Configure training response collector
		self.training_rc.terminate_after = [1500, TK_MS]
		self.training_rc.display_callback = self.training_callback
		self.training_rc.flip = True
		self.training_rc.keypress_listener.key_map = self.training_keymap
		self.training_rc.keypress_listener.interrupts = True

	def trial_prep(self):
		# Reset error flag
		self.targets_shown = False
		self.err = None

		# TRAINING PROPERTIES
		if P.practicing:
			self.cotoa = 'NA' # No cue, so no COTOA
			# Establish location of target line
			if self.tilt_line_location == LEFT:
				self.tilt_line_loc = self.left_box_loc
				self.flat_line_loc = self.right_box_loc
			else:
				self.tilt_line_loc = self.right_box_loc
				self.flat_line_loc = self.left_box_loc

		
		# PROBE PROPERTIES
		else:
			# Rest breaks
			if P.trial_number % (P.trials_per_block/P.breaks_per_block) == 0:
				if P.trial_number < P.trials_per_block:
					fill()
					msg = message(self.rest_break_txt, 'myText', blit_txt=False)
					blit(msg, 5, P.screen_c)
					flip()
					any_key()

			# Establish & assign probe location
			self.probe_loc = self.right_box_loc if self.probe_location == RIGHT else self.left_box_loc
			# go/nogo signal always presented w/probe
			self.go_nogo_loc = self.probe_loc	

			# Establish & assign probe colour
			if self.probe_colour == HIGH:
				self.probe.fill = self.high_value_colour
			elif self.probe_colour == LOW:
				self.probe.fill = self.low_value_colour
			else:
				self.probe.fill = self.neutral_value_colour

		# Add timecourse of events to EventManager
		if P.practicing: # training trials
			events = [[1000, 'target_on']]
		else: # Probe trials
			events = [[1000, 'cue_on']]
			events.append([events[-1][0] + 200, 'cue_off'])
			events.append([events[-1][0] + 200, 'cueback_off'])
			events.append([events[-2][0] + 800, 'target_on'])
		for e in events:
			self.evm.register_ticket(ET(e[1], e[0]))

		# Perform drift correct on Eyelink before trial start
		self.el.drift_correct()

	def trial(self):
		# TRAINING TRIAL
		if P.practicing:
			cotoa, probe_rt = ['NA', 'NA'] # Don't occur in training blocks

			# Present placeholders
			while self.evm.before('target_on', True) and not self.err:
				self.confirm_fixation()
				self.present_boxes() 
				flip()

			# TRAINING RESPONSE PERIOD
			self.targets_shown = True # After trainings shown, don't recycle trial
			self.training_rc.collect() # Present trainings and listen for response
			
			# If wrong response made
			if self.err:
				line_response, line_rt, reward = ['NA', 'NA', 'NA']
			else:
				self.err = 'NA'
				# Retrieve responses from ResponseCollector & record data
				line_response, line_rt = self.training_rc.keypress_listener.response()

				if line_rt == TIMEOUT:
					reward = 'NA'
					self.show_error_message('training_timeout')
				else:
					reward = self.feedback(line_response) # Determine training payout & display

		# PROBE TRIAL
		else:
			line_response, line_rt, reward = ['NA', 'NA', 'NA'] # Don't occur in probe trials

			# Present placeholders & confirm fixation
			while self.evm.before('target_on', True):
				self.confirm_fixation()
				self.present_boxes()

				# Present cue
				if self.evm.between('cue_on', 'cue_off'):
					if self.cue_location == LEFT:
						blit(self.thick_rect, 5, self.left_box_loc)
					else:
						blit(self.thick_rect, 5, self.right_box_loc)
				# Present cueback
				elif self.evm.between('cue_off', 'cueback_off'):
					blit(self.fix_cueback, 5, P.screen_c)

				flip()

			# PROBE RESPONSE PERIOD
			self.targets_shown = True # After probe shown, don't recycle trial
			self.probe_rc.collect() # Present probes & listen for response

			# If 'go' trial, check for response
			if self.go_no_go == GO:
				
				if self.err: # If wrong response made
					probe_rt = 'NA'
				
				else: # If correct response OR timeout
					self.err = 'NA'
					probe_rt = self.probe_rc.keypress_listener.response(value=False,rt=True)

					if probe_rt == TIMEOUT:
						probe_rt = 'NA'
						self.show_error_message('probe_timeout')

			# Similarly, for 'nogo' trials
			else:
				probe_rt = 'NA'
				# If response made, penalize
				if len(self.probe_rc.keypress_listener.responses):
					self.show_error_message('response_on_nogo')
					self.err = 'response_on_nogo'
				# If no response, continue as normal
				else:
					self.err = 'NA'
		# Return trial data
		return {
			"block_num":      P.block_number,
			"trial_num":      P.trial_number,
			"block_type":     "training" if P.practicing else "probe",
			"high_value_col": self.high_value_colour[:3] if P.practicing else 'NA',
			"tilt_line_loc":  self.tilt_line_loc if P.practicing else 'NA',
			"low_value_col":  self.low_value_colour[:3] if P.practicing else 'NA',
			"flat_line_loc":  self.flat_line_loc if P.practicing else 'NA',
			"winning_trial":  self.winning_trial if P.practicing else 'NA',
			"line_response":  line_response,
			"line_rt":        line_rt,
			"reward":         reward,
			"cue_loc":        self.cue_location if not P.practicing else 'NA',
			"cotoa":          self.cotoa if not P.practicing else 'NA',
			"probe_loc":      self.probe_location if not P.practicing else 'NA',
			"probe_col":      self.probe_colour if not P.practicing else 'NA',
			"go_no_go":       self.go_no_go if not P.practicing else 'NA',
			"probe_rt":       probe_rt,
			"err":            self.err
		}
		# Clear remaining stimuli from screen
		clear()

	def trial_clean_up(self):
		# Clear responses from responses collectors before next trial
		self.probe_rc.keypress_listener.reset()
		self.training_rc.keypress_listener.reset()

	def clean_up(self):
		# Let Ss know when experiment is over
		self.all_done_text = "You're all done! Now I get to take a break.\nPlease buzz the researcher to let them know you're done!"
		fill()
		msg = message(self.all_done_text, 'myText', blit_txt=False)
		blit(msg, 5, P.screen_c)
		flip()
		any_key()

	# ------------------------------------ #
	# Experiment specific helper functions #
	# ------------------------------------ #

	def feedback(self, response):
		correct_response = True if response == self.tilt_line_location else False

		# Every 5 trials of a particular payoff, ask anticipated earnings
		if self.potential_payoff == HIGH:
			self.high_value_trial_count += 1
			if self.high_value_trial_count in [5,10,15]:
				self.query_learning(HIGH)
		else:
			self.low_value_trial_count += 1
			if self.low_value_trial_count in [5,10,15]:
				self.query_learning(LOW)
		
		# Determine payout for trial
		if correct_response & (self.winning_trial == YES):
			points = self.payout()
			msg = message("You won {0} points!".format(points), 'myText', blit_txt=False)
		else:
			points = self.penalty
			msg = message("You lost 5 points!", 'myText', blit_txt=False)
		# Keep tally of score
		self.total_score += points
		feedback = [points, msg]

		# Present score
		feedback_exposure = CountDown(self.feedback_exposure_period)
		fill()
		blit(feedback[1], location=P.screen_c, registration=5)
		flip()
		while feedback_exposure.counting():
			ui_request()

		return feedback[0]

	def payout(self): # Calculates payout
		mean = self.high_payout_baseline if self.potential_payoff == HIGH else self.low_payout_baseline

		return int(random.gauss(mean, 1) + 0.5)

	def confirm_fixation(self):
		if not self.el.within_boundary('fixation', EL_GAZE_POS):
			self.show_error_message('fixation')
			if self.targets_shown:
				self.err = 'left_fixation'
			else:
				raise TrialException('gaze left fixation') # recycle trial

	def show_error_message(self, msg_key):
		fill()
		blit(self.err_msgs[msg_key], location=P.screen_c, registration=5)
		flip()
		any_key()

	def present_boxes(self):
		fill()
		blit(self.fixation, 5, P.screen_c)
		if P.practicing: # During training, box colour indicates potential payout
			if self.potential_payoff == HIGH:
				blit(self.high_val_rect, 5, self.left_box_loc)
				blit(self.high_val_rect, 5, self.right_box_loc)
			else:
				blit(self.low_val_rect, 5, self.left_box_loc)
				blit(self.low_val_rect, 5, self.right_box_loc)
		else: # Probe trials, where boxes are white.
			blit(self.thin_rect, 5, self.left_box_loc)
			blit(self.thin_rect, 5, self.right_box_loc)
	
	# Presents target & non-target lines. Probably a better name for this out there....
	def training_callback(self):
		self.confirm_fixation()
		self.present_boxes()

		blit(self.tilt_line, 5, self.tilt_line_loc)
		blit(self.flat_line, 5, self.flat_line_loc)
	
	# Presents probes & go/no-go signal
	def probe_callback(self):
		self.confirm_fixation()
		self.present_boxes()

		# Present probe & go/nogo stimulus
		if self.go_no_go == GO:
			blit(self.probe, 5, self.probe_loc)
			blit(self.go, 5, self.probe_loc)
		else:
			blit(self.probe, 5, self.probe_loc)
			blit(self.nogo, 5, self.probe_loc)
	
	# Learning probe. Asks participants their anticipated earnings
	def query_learning(self, potential_payoff):
		if potential_payoff == HIGH:
			anticipated_reward_high = query(user_queries.experimental[0])
			anticipated_reward_survey = {
				'participant_id': P.participant_id,
				'anticipated_reward_high': anticipated_reward_high,
				'anticipated_reward_low': "NA"
			}
		else:
			anticipated_reward_low = query(user_queries.experimental[1])
			anticipated_reward_survey = {
				'participant_id': P.participant_id,
				'anticipated_reward_high': "NA",
				'anticipated_reward_low': anticipated_reward_low
			}

		self.db.insert(anticipated_reward_survey, table='surveys')