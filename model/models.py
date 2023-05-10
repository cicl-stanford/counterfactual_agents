from blue_planner import *
from utils import *

import copy
import scipy as sp

# ------------------------------
class CounterfactualModel:
    def __init__(self,
            exp, env, red_path, blue_path, box_changes):
        """ Initiates counterfactual model """

        env.reset()
        self.exp = exp
        self.env = env.copy()
        self.env.generating_trials = False
        self.model_type = "counterfactual"
        self.red_path = [tuple(action) for action in red_path]
        self.blue_path = [tuple(action) for action in blue_path]
        self.box_changes = box_changes


    def simulate_once(self):
        """ Runs one trial within counterfactual world (no blue agent) """
        
        self.env.reset()
        
        # after blue's first move add simulation noise
        first_impact_at = 10
        for i in range(len(self.blue_path)):
            if tuple(self.blue_path[i]) != STAY:
                first_impact_at = i + 2
                break

        if self.exp == "exp1":
            red_path = self.red_path.copy()
            blue_path = []

            _, outcome = self.env.run_exp1(
                paths = [red_path, blue_path], 
                box_changes = self.box_changes, 
                cf_neutral = True)
            return outcome == 'succeeded'
            
        if self.exp == "exp2":
            self.env.setup_planners()
            self.env.red_agent.path = self.red_path.copy()
            self.env.blue_agent.path = [STAY]

            _, outcome = self.env.run_exp2(
                cf_neutral = True, 
                first_impact_at = first_impact_at)
            return outcome == 'success'


    def simulate_all(self, num_simulations, verbose = False):
        """ Runs many counterfactual simulations and tracks red's success rate """

        num_successes = 0
        total_distance = 0

        print("\nrunning {} model...\n".format(self.model_type))
        
        for i in range(num_simulations):
            if i > 0 and i % 100 == 0: print(i, 'simulations done')
            
            num_successes += self.simulate_once()
                        
        success_rate = int(num_successes / num_simulations * 100)

        print("red player achieved a {}% {} success rate across {} simulations\n".format(
               success_rate, self.model_type, num_simulations))

        return success_rate


# ------------------------------
class IntentionModel():
    def __init__(self, exp, env, red_path, blue_path,
            box_changes, a, b, c, red_reward):
        """ Initiates intention inference model """

        self.exp = exp
        self.env = env.copy()
        self.env.reset()
        self.env.generating_trials = False
        self.model_type = "intention"

        self.red_path = [tuple(action) for action in red_path]
        self.blue_path = [tuple(action) for action in blue_path]
        
        self.box_changes = box_changes
        if self.box_changes is not None:
            self.box_timesteps_list = list(self.box_changes.keys())
            self.box_locations_list = list(self.box_changes.values())

        self.boxes = self.env.world.get_boxes()
        self.num_boxes = len(self.env.world.get_boxes())
        self.box_locations = [b.location for b in self.boxes]
        self.box_location_to_code = dict((location, num) 
            for num, location in enumerate(self.box_locations))
        
        # blue agent model parameters
        self.a = a
        self.b = b
        self.c = c
        self.red_reward = red_reward


    def setup_intention_model(self):
        """ Performs basic setup for doing intention inference """
        
        print("running intention model...\n")

        if self.exp == "exp1":
            multiple_boxes_moved = False # two boxes moved
            box_moved_far = False # box moved 2+ squares
            first_hold_at = 0
            box_location_two, box_action_two = None, None
        
            if len(self.box_locations_list) == 0:
                box_location = self.env.world.get_boxes()[0].location
                box_action = (0, 0)
            
            elif len(self.box_locations_list) == 2:
                box_location = tuple(self.box_locations_list[0][0])
                box_action = get_action_from_location(
                    box_location, tuple(self.box_locations_list[1][0]))
                
                if (box_action[0] > 1 
                    or box_action[1] > 1 
                    or box_action[0] < -1 
                    or box_action[1] < -1):
                    box_moved_far = True
            
            elif len(self.box_locations_list) == 4:
                multiple_boxes_moved = True
                box_location = tuple(self.box_locations_list[0][0])
                box_action = get_action_from_location(
                    box_location, tuple(self.box_locations_list[1][0]))
                
                box_location_two = tuple(self.box_locations_list[2][0])
                box_action_two = get_action_from_location(
                    box_location_two, tuple(self.box_locations_list[3][0]))
            
            if len(self.box_timesteps_list) > 0:
                first_hold_at = int(self.box_timesteps_list[0])
            
            return box_location, box_action, box_location_two, box_action_two, multiple_boxes_moved, box_moved_far, first_hold_at
        
        if self.exp == "exp2":
            box_location = (self.env.world.get_boxes()[0]).location
            first_hold_at = -1
            box_action = STAY

            for i in range(len(self.blue_path)):
                if self.blue_path[i] in HOLD_ACTIONS:
                    first_hold_at = i + 1

                if first_hold_at == i:
                    blue_action = tuple(self.blue_path[i])
                    box_action = blue_action if blue_action in ACTIONS else STAY
                    break

            if first_hold_at == -1: first_hold_at = 0 
            
            return box_location, box_action, first_hold_at


    def move_box_far(self, box, box_action, first_hold_at):
        """ Handles boxes that move more than one square """
        
        if box_action[0] > 1 or box_action[0] < -1:
            single_action = (1, 0) if box_action[0] > 1 else (-1, 0)
            for i in range(abs(box_action[0]) - 1):
                box.location = get_location_from_action(
                    self.env.world, box.location, single_action)
                first_hold_at += 1
            box_location = box.location
            box_action = single_action
        
        elif box_action[1] > 1 or box_action[1] < -1:
            single_action = (0, 1) if box_action[1] > 1 else (0, -1)
            for i in range(abs(box_action[1]) - 1):
                box.location = get_location_from_action(
                    self.env.world, box.location, single_action)
                first_hold_at += 1
            box_location = box.location
            box_action = single_action
        
        return box_location, box_action, first_hold_at

    
    def test_rollout(self, blue_path, first_hold_at):
        """ Simulates the game up until blue first holds a box """
        
        running_env = self.env.copy()
        running_env.reset()
        
        # simulate the trial with red/blue path, no stalling
        running_env.red_agent.location = self.env.red_agent.start_location
        running_env.blue_agent.location = self.env.blue_agent.start_location

        running_env.red_agent.path = []
        running_env.red_agent.level = 0  
        running_env.blue_agent.path = blue_path

        _, _ = running_env.run_exp2(
            verbose = False,
            no_stall = True,
            time_limit = first_hold_at,
            copy_trial_blue = True)

        final_red_location = running_env.red_agent.location
        final_blue_location = running_env.blue_agent.location

        return final_red_location, final_blue_location


    def simulate_intention_exp1(self, intention, box_moved_far, multiple_boxes_moved, 
            first_hold_at, box = None, box_location = None, box_action = None, 
            first_box_mod_location = None, box_moves = None, box_moves_opp = None):
        """ Returns box moves and Q-values for specified blue intention """
        
        self.env.reset()

        if box_moved_far:
            box_location, box_action, first_hold_at = self.move_box_far(box, box_action, first_hold_at)

        # condition on original red path up until blue first picks up box
        red_location = self.env.agents[0].start_location
        remaining_red_path = []
        for timestep in range(first_hold_at):
            red_location = get_location_from_action(
                self.env.world, red_location, tuple(self.red_path[timestep]))
            remaining_red_path.append(STAY)
        for action in self.red_path[first_hold_at:]:
            remaining_red_path.append(tuple(action))
        
        # run blue's forward planner to get its possible policies + Q-values
        blue_planner = L1BluePlanner(self.exp, self.env, social_type = intention)
        blue_planner.simulate_all_box_moves()

        if not box_moves and not box_moves_opp:
            box_moves, box_moves_opp = blue_planner.plan_box_moves(red_location, 
                self.env.world.get_goal_location(), try_multiple = True, 
                time_limit = 10 - first_hold_at)

        mod_box_location = None
        if box_moved_far: mod_box_location = box_location
        if multiple_boxes_moved: mod_box_location = first_box_mod_location

        Q_values = blue_planner.train_blue(
            box_moves, box_moves_opp, get_Q = True, 
            observed_red_location = red_location, 
            observed_red_path = remaining_red_path, 
            observed_box_move = (box_location, box_action), 
            mod_box_location = mod_box_location, 
            a = self.a, b = self.b, c = self.c, 
            red_reward = self.red_reward)
        
        blue_paths = blue_planner.train_blue(
            box_moves, box_moves_opp, get_all_blue_paths = True)

        return box_moves, box_moves_opp, box_location, box_action, Q_values, blue_paths
    

    def simulate_intention_exp2(self, intention, first_hold_at):
        """ Returns box moves and Q-values for specified blue intention """
        
        blue_planning_env = self.env.copy()
        blue_planning_env.reset()
        
        # condition on original red path up until blue first picks up box
        observed_red_location, observed_blue_location = self.test_rollout(self.blue_path.copy(), first_hold_at)

        blue_planner = L1BluePlanner(self.exp, blue_planning_env, social_type = intention)
        blue_planner.simulate_all_box_moves()

        box_moves, box_moves_opp = blue_planner.plan_box_moves(
            observed_red_location, self.env.world.get_goal_location(),
            try_multiple = True, time_limit = 10 - first_hold_at)
        
        Q_values = blue_planner.train_blue(
            box_moves, box_moves_opp, get_Q = True,
            observed_red_location = observed_red_location,
            observed_blue_location = observed_blue_location,
            time_limit = 10 - first_hold_at, 
            a = self.a, b = self.b, c = self.c)

        return box_moves, Q_values


    def infer_intention(self):
        """ Uses bayesian inference infer blue agent's helping or hindering intention """
        
        inferred_intention = ""
        confidence = 100
        prob_help = 0.5
        prob_hinder = 0.5
        prob_action_given_help = 0
        prob_action_given_hinder = 0
        prob_help_given_action = 0
        prob_hinder_given_action = 0
        multiple_boxes_moved = False
        box_moved_far = False

        # softmax temperature parameter
        beta = 0.4 if self.exp == "exp1" else 0.3

        if self.exp == "exp1":
            box_location, box_action, box_location_two, box_action_two, multiple_boxes_moved, box_moved_far, first_hold_at = self.setup_intention_model()

            box_code = self.box_location_to_code[box_location]
            box = self.boxes[box_code]
            original_box_location = box_location
            original_box_action = box_action
            original_first_hold_at = first_hold_at
            
            if multiple_boxes_moved:
                box_code_two = self.box_location_to_code[box_location_two]
                box_two = self.boxes[box_code_two]
                original_box_location_two = box_location_two
                original_box_action_two = box_action_two
                first_box_mod_location = self.env.world.get_new_location(original_box_location, original_box_action)
                observed_box_move_multiple = ((box_location, box_action), (box_location_two, box_action_two))
            
            if box_moved_far:
                box_moves_help, _, box_location, box_action, Q_values_help, _ = self.simulate_intention_exp1(
                    "help", box_moved_far, multiple_boxes_moved, original_first_hold_at, 
                    box, original_box_location, original_box_action)
                box_moves_hinder, _, box_location, box_action, Q_values_hinder, _ = self.simulate_intention_exp1(
                    "hinder", box_moved_far, multiple_boxes_moved, original_first_hold_at, 
                    box, original_box_location, original_box_action)
            
            elif multiple_boxes_moved:
                box_moves_help, box_moves_hinder, _, _, Q_values_help, _ = self.simulate_intention_exp1(
                    "help", box_moved_far, multiple_boxes_moved, first_hold_at, 
                    box_two, original_box_location_two, original_box_action_two, first_box_mod_location)
                _, _, _, _, Q_values_hinder, _ = self.simulate_intention_exp1(
                    "hinder", box_moved_far, multiple_boxes_moved, first_hold_at, 
                    box_two, original_box_location_two, original_box_action_two, first_box_mod_location, 
                    box_moves_hinder, box_moves_help)
            
            else:
                box_moves_help, _, _, _, Q_values_help, _ = self.simulate_intention_exp1(
                    "help", box_moved_far, multiple_boxes_moved, first_hold_at, 
                    box, original_box_location, original_box_action)
                box_moves_hinder, _, _, _, Q_values_hinder, _ = self.simulate_intention_exp1(
                    "hinder", box_moved_far, multiple_boxes_moved, first_hold_at, 
                    box, original_box_location, original_box_action)
    
        if self.exp == "exp2":
            box_location, box_action, first_hold_at = self.setup_intention_model()
            box_moves_help, Q_values_help = self.simulate_intention_exp2("help", first_hold_at)
            box_moves_hinder, Q_values_hinder = self.simulate_intention_exp2("hinder", first_hold_at)

        # bayesian inference to get posterior probabilities over help and hinder
        help_values = [beta * val for val in list(Q_values_help.values())]
        hinder_values = [beta * val for val in list(Q_values_hinder.values())]
        softmax_help = list(sp.special.softmax(help_values))
        softmax_hinder = list(sp.special.softmax(hinder_values))
        action_probs_help = dict(zip(list(Q_values_help.keys()), softmax_help))
        action_probs_hinder = dict(zip(list(Q_values_hinder.keys()), softmax_hinder))

        if multiple_boxes_moved:
            prob_action_given_help = action_probs_help[(box_location, box_action), (box_location_two, box_action_two)]
            prob_action_given_hinder = action_probs_hinder[(box_location, box_action), (box_location_two, box_action_two)]
        else:
            prob_action_given_help = action_probs_help[(box_location, box_action)]
            prob_action_given_hinder = action_probs_hinder[(box_location, box_action)]
            
        norm_const = (prob_action_given_help * prob_help) + (prob_action_given_hinder * prob_hinder)
        prob_help_given_action = prob_action_given_help * prob_help / norm_const
        prob_hinder_given_action = prob_action_given_hinder * prob_hinder / norm_const
        
        if prob_help_given_action > prob_hinder_given_action:
            inferred_intention = "help"
            confidence *= prob_help_given_action
        else:
            inferred_intention = "hinder"
            confidence *= prob_hinder_given_action
            
        numerical_intention = round(confidence, 4) if inferred_intention == "help" else round(100 - confidence, 4)
        print("inferred intention: {}".format(inferred_intention))
        print("numerical intention: {}\n".format(numerical_intention))
        return inferred_intention, numerical_intention


# ------------------------------
class EffortModel():
    def __init__(self, exp, env, box_changes, blue_path):
        """ Initiates blue agent effort model """

        env.reset()
        self.exp = exp
        self.env = copy.deepcopy(env)
        self.box_changes = box_changes
        
        if self.box_changes is not None:
            self.box_timesteps_list = list(self.box_changes.keys())
            self.box_locations_list = list(self.box_changes.values())
        
        self.blue_path = [tuple(action) for action in blue_path]
        self.model_type = "effort"

    def compute(self):
        """ Computes effort exerted by blue agent in the trial """
        
        print("running effort model...\n")
        num_boxes_moved = 1
        box_move_distance = 1
        movement_cost = 1
        box_cost = 2
        
        if self.exp == "exp1":
            if len(self.box_locations_list) == 0:
                box_location = self.env.world.get_boxes()[0].location
                box_action = (0, 0)
                num_boxes_moved = 0
                box_move_distance = 0
            
            elif len(self.box_locations_list) == 2:
                box_location = tuple(self.box_locations_list[0][0])
                box_action = get_action_from_location(
                    box_location, tuple(self.box_locations_list[1][0]))
                
                if box_action[0] > 1 or box_action[0] < -1: 
                    box_move_distance = abs(box_action[0])
                if box_action[1] > 1 or box_action[1] < -1: 
                    box_move_distance = abs(box_action[1])
            
            elif len(self.box_locations_list) == 4:
                num_boxes_moved = 2
                box_location = tuple(self.box_locations_list[0][0])
                box_action = get_action_from_location(
                    box_location, tuple(self.box_locations_list[1][0]))
                
                box_location_two = tuple(self.box_locations_list[2][0])
                box_action_two = get_action_from_location(
                    box_location_two, tuple(self.box_locations_list[3][0]))

            blue_path = [action for action in self.blue_path if action != STAY]

        if self.exp == "exp2":
            blue_path = []
            for i, action in enumerate(self.blue_path):
                if action in HOLD_ACTIONS:
                    box_action = self.blue_path[i + 1]
                    if self.blue_path[i + 2] not in RELEASE_ACTIONS:
                        box_move_distance = 2
                if (action not in HOLD_ACTIONS 
                    and action not in RELEASE_ACTIONS 
                    and action != STAY):
                    blue_path.append(action)

            if box_action == STAY:
                num_boxes_moved = 0
                box_move_distance = 0
        
        if num_boxes_moved > 1:
            num_blue_moves = len(blue_path) - num_boxes_moved
        else:
            num_blue_moves = len(blue_path) - box_move_distance

        effort = (movement_cost * num_blue_moves) + (box_cost * num_boxes_moved * box_move_distance)
        print("blue agent effort: {}\n".format(effort))
        return effort
