from klibs.KLIndependentVariable import IndependentVariableSet

IOReward_E2_ind_vars = IndependentVariableSet()

IOReward_E2_ind_vars.add_variable("potential_payoff", str, ["high", "low"])
IOReward_E2_ind_vars.add_variable("winning_trial", str, ["yes", "yes", "yes", "no"])
IOReward_E2_ind_vars.add_variable("tilt_line_location", str, ["left", "right"])
IOReward_E2_ind_vars.add_variable("cue_location", str, ["left", "right"])
IOReward_E2_ind_vars.add_variable("probe_location", str, ["left", "right"])
IOReward_E2_ind_vars.add_variable("probe_colour", str, ["high", "low", "neutral"])
IOReward_E2_ind_vars.add_variable("go_no_go", str, ["go","nogo"])