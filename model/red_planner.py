from collections import defaultdict
import numpy as np
import scipy as sp
import functools
import copy
from itertools import chain

from environment import *
from agent import *
from gridworld import *
from utils import *
from blue_planner import *

class L0RedPlanner():
    def __init__(self, exp, env):
        """ Initiates level-0 red agent planner """

        self.exp = exp
        self.env = env
        self.env.reset()
        self.red_agent, self.blue_agent = self.env.agents
        self.goal_location = self.env.world.get_goal_location()
        
        # joint state and action space per timestep
        self.state_space = {}
        # self.state_space[timestep] = location that agent starts out at on that timestep
        self.action_space = {}
        # self.action_space[timestep] = action that agent takes during that timestep


    def plan_red_path(self, get_all_paths = False, only_shortest_paths = True, time_limit = 10, count_boxes = True):
        """ Plan path to star by sampling from distribution over all paths """

        path = []

        # get softmaxed probability distribution over all possible paths
        all_paths, path_probs = self.env.world.get_distribution_over_paths(
            self.red_agent.location, self.goal_location, self.blue_agent.location,
            only_shortest_paths = only_shortest_paths, time_limit = time_limit, count_boxes = count_boxes)
        
        # if there's no path to the goal
        if not all_paths:
            if get_all_paths:
                all_paths = []
                path_probs = 1
            else: return [STAY]

        if get_all_paths: return all_paths, path_probs
        
        # choose a path according to the probability distribution
        np.random.seed()
        choice = np.random.choice(len(path_probs), 1, p = path_probs)[0]
        locations_in_path = all_paths[choice]

        for i in range(1, len(locations_in_path)):
            path.append(get_action_from_location(locations_in_path[i - 1], locations_in_path[i]))
        
        return path
        

class L2RedPlanner():
    def __init__(self, exp, env, actual_blue_path = [], visualize = True):
        """ Initiates level-2 red agent planner """

        self.exp = exp
        self.env = env
        self.env.reset()
        self.blue_planning_env = self.env.copy()
        self.red_agent, self.blue_agent = self.env.agents
        self.goal_location = self.env.world.get_goal_location()

        self.visualize = visualize
        self.actual_blue_path = actual_blue_path
        
        # joint state and action space per timestep
        self.state_space = {}
        # self.state_space[timestep] = location agent starts at for that timestep
        self.action_space = {}
        # self.action_space[timestep] = action that agent takes during that timestep
        
        # estimates of blue's intention per timestep
        self.intention_estimates = {}
        self.intention_probs = {}
        
        self.locations = self.env.world.get_all_locations()
        self.actions = [DOWN, UP, LEFT, RIGHT, STAY]
        self.num_actions = len(self.actions)
        self.num_states = len(self.locations)
        self.boxes = self.env.world.get_boxes()
        self.num_boxes = len(self.env.world.get_boxes())
        self.box_locations = [b.location for b in self.boxes]
        
        self.location_to_state = dict((location, state) for state, location in enumerate(self.locations))
        self.state_to_location = dict((state, location) for location, state in self.location_to_state.items())
        self.action_to_code = dict((action, num) for num, action in enumerate(self.actions))
        self.code_to_action = dict((num, action) for action, num in self.action_to_code.items())
        self.box_location_to_code = dict((location, num) for num, location in enumerate(self.box_locations))


    def plan_red_path(self, get_all_paths = False, only_shortest_paths = True, time_limit = 10, count_boxes = True):
        """ Plan path to star by sampling from distribution over all paths """

        path = []

        # get softmaxed probability distribution over all possible paths
        all_paths, path_probs = self.env.world.get_distribution_over_paths(
            self.red_agent.location, self.goal_location, self.blue_agent.location,
            only_shortest_paths = only_shortest_paths, time_limit = time_limit, count_boxes = count_boxes)
        
        # if there's no path to the goal
        if not all_paths:
            if get_all_paths:
                all_paths = []
                path_probs = 1
            else: return [STAY]

        if get_all_paths: return all_paths, path_probs
        
        # choose a path according to the probability distribution
        np.random.seed()
        choice = np.random.choice(len(path_probs), 1, p = path_probs)[0]
        locations_in_path = all_paths[choice]

        for i in range(1, len(locations_in_path)):
            path.append(get_action_from_location(locations_in_path[i - 1], locations_in_path[i]))
        
        return path


    def estimate_blue_intention(self,
            timestep, prev_est_blue_intention = "help", 
            prev_est_prob = 0.5, verbose = False):
        """ From L2 red's POV, estimates blue's intention (help/hinder) and associated probability """
        
        blue_planning_env = self.env.copy()
        blue_planning_env.reset()
        
        prev_blue_action = self.action_space[timestep - 1, 1]
        prev_red_location = self.state_space[timestep - 1, 0]
        prev_blue_location = self.state_space[timestep - 1, 1]

        # if blue just holds or releases a box, don't change the estimate
        if prev_blue_action in HOLD_ACTIONS or prev_blue_action in RELEASE_ACTIONS:
            self.intention_estimates[timestep] = prev_est_blue_intention
            self.intention_probs[timestep] = prev_est_prob
            return prev_est_blue_intention, prev_est_prob

        # L2 red agent simulates what helping L1 blue agent would do
        blue_planner_help = L1BluePlanner(self.exp,
            blue_planning_env, social_type = "help")
        blue_planner_help.simulate_all_box_moves()
        box_moves, box_moves_opp = blue_planner_help.plan_box_moves(
            prev_red_location, self.env.world.get_goal_location(),
            time_limit = 12 - timestep)
        Q_values_help = blue_planner_help.train_blue(
            box_moves, box_moves_opp, get_Q = True,
            observed_red_location = prev_red_location,
            observed_blue_location = prev_blue_location,
            time_limit = 12 - timestep)
        blue_planning_env.reset()

        # L2 red agent simulates what hindering L1 blue agent would do
        blue_planner_hinder = L1BluePlanner(self.exp,
            blue_planning_env, social_type = "hinder")
        blue_planner_hinder.simulate_all_box_moves()
        box_moves, box_moves_opp = blue_planner_hinder.plan_box_moves(
            prev_red_location, self.env.world.get_goal_location(),
            time_limit = 12 - timestep)
        Q_values_hinder = blue_planner_hinder.train_blue(
            box_moves, box_moves_opp, get_Q = True,
            observed_red_location = prev_red_location,
            observed_blue_location = prev_blue_location,
            time_limit = 12 - timestep)

        # take softmax over helping and hindering Q-values
        help_values = [0.5 * val for val in list(Q_values_help.values())]
        hinder_values = [0.5 * val for val in list(Q_values_hinder.values())]
        softmax_help = list(sp.special.softmax(help_values))
        softmax_hinder = list(sp.special.softmax(hinder_values))
        action_probs_help = dict(zip(list(Q_values_help.keys()), softmax_help))
        action_probs_hinder = dict(zip(list(Q_values_hinder.keys()), softmax_hinder))

        all_blue_paths = blue_planner_help.train_blue(
            box_moves, box_moves_opp,
            observed_red_location = prev_red_location,
            observed_blue_location = prev_blue_location, 
            get_all_blue_paths = True)

        helping_paths = []
        hindering_paths = []
        
        for box_move, path in all_blue_paths.items():
            if action_probs_help[box_move] > action_probs_hinder[box_move]:
                helping_paths.append(path)
            else:
                hindering_paths.append(path)
        
        for path in helping_paths:
            if path == [STAY, STAY]:
                helping_paths = [[STAY]]
                break
                
        for path in hindering_paths:
            if path == [STAY, STAY]:
                hindering_paths = [[STAY]]
                break
        
        # count number of helping vs. hindering paths prev_blue_action aligns with
        help_count = 0
        hinder_count = 0

        for help_path in helping_paths:
            if tuple(prev_blue_action) == help_path[0]:
                help_count += 1

        for hinder_path in hindering_paths:
            if tuple(prev_blue_action) == hinder_path[0]:
                hinder_count += 1

        prob_prev_action_given_help = help_count / (len(helping_paths) + 1e-8)
        prob_prev_action_given_hinder = hinder_count / (len(hindering_paths) + 1e-8)

        # prior probability of either intention is based on the previous timestep's estimate
        prior_prob_help = prev_est_prob if prev_est_blue_intention == "help" else 1 - prev_est_prob
        prior_prob_hinder = 1 - prior_prob_help

        norm_const = (prior_prob_help * prob_prev_action_given_help) + (prior_prob_hinder * prob_prev_action_given_hinder)
        cur_est_prob_help = prior_prob_help * prob_prev_action_given_help / (norm_const + 1e-8)
        cur_est_prob_hinder = prior_prob_hinder * prob_prev_action_given_hinder / (norm_const + 1e-8)
        
        # if blue takes no more actions, preserve the last estimate
        if cur_est_prob_help == 0 and cur_est_prob_hinder == 0:
            self.intention_estimates[timestep] = prev_est_blue_intention
            self.intention_probs[timestep] = prev_est_prob
            return prev_est_blue_intention, prev_est_prob

        cur_intention_estimate = "help" if cur_est_prob_help > cur_est_prob_hinder else "hinder"
        cur_intention_prob = cur_est_prob_help if cur_est_prob_help > cur_est_prob_hinder else cur_est_prob_hinder
        
        self.intention_estimates[timestep] = cur_intention_estimate
        self.intention_probs[timestep] = cur_intention_prob
        
        return cur_intention_estimate, cur_intention_prob


    def estimate_blue_policy(self, timestep, est_blue_intention):
        """ Returns likely box move and next blue action based on red's estimate of blue's intention """

        cur_red_location = self.state_space[timestep, 0]
        cur_blue_location = self.state_space[timestep, 1]

        blue_planning_env = self.env.copy()
        blue_planning_env.reset()

        est_blue_planner = L1BluePlanner(self.exp,
            blue_planning_env, social_type = est_blue_intention)
        est_blue_planner.simulate_all_box_moves()
        
        box_moves, box_moves_opp = est_blue_planner.plan_box_moves(
            cur_red_location, self.env.world.get_goal_location(),
            time_limit = 11 - timestep)
        
        est_Q_blue = est_blue_planner.train_blue(
            box_moves, box_moves_opp, get_Q = True,
            observed_red_location = cur_red_location,
            observed_blue_location = cur_blue_location,
            time_limit = 11 - timestep)

        est_blue_paths = est_blue_planner.train_blue(
            box_moves, box_moves_opp, 
            observed_red_location = cur_red_location,
            observed_blue_location = cur_blue_location,
            get_all_blue_paths = True)

        likely_box_move = max(est_Q_blue, key=est_Q_blue.get)
        box_location, box_action = likely_box_move

        if box_action == STAY and self.action_space[timestep - 1, 1] != STAY:
            est_Q_blue.pop(likely_box_move)
            likely_box_move = max(est_Q_blue, key=est_Q_blue.get)

        # if there are many equally-optimal policies, randomly choose
        rev_dict = {}
        for key, value in est_Q_blue.items():
            rev_dict.setdefault(value, set()).add(key)
        duplicate_moves = set(chain.from_iterable(
            values for key, values in rev_dict.items() if len(values) > 1))

        if likely_box_move in duplicate_moves: 
            all_likely_moves = []
            for move in duplicate_moves:
                if est_Q_blue[move] == est_Q_blue[likely_box_move]:
                    all_likely_moves.append(move)
            
            random.seed()
            likely_box_move = random.sample(all_likely_moves, 1)[0]
        
        return likely_box_move, est_blue_paths[likely_box_move]


    def get_path_rewards(self, timestep, only_shortest_paths, red_physical_reward = 20):
        """ Defines L2 red's reward associated with each path to the star """
        
        self.all_red_paths = {}
        self.red_path_rewards = {}
        
        self.red_agent.location = self.state_space[timestep, 0]
        self.blue_agent.location = self.state_space[timestep, 1]

        self.all_red_paths[timestep] = []
        all_red_paths, all_path_probs = self.plan_red_path(
            get_all_paths = True, only_shortest_paths = only_shortest_paths)

        for locations_in_path in all_red_paths:
            path = []
            for i in range(1, len(locations_in_path)):
                path.append(get_action_from_location(
                    locations_in_path[i - 1], locations_in_path[i]))
            self.all_red_paths[timestep].append(path)

        if self.all_red_paths[timestep] == []: self.all_red_paths[timestep].append([STAY])
        
        # assign reward to each path based on length and number of directional switches
        for i, path in enumerate(self.all_red_paths[timestep]):
            prev_action = path[0]
            num_switches = 0
            for action in path[1:]:
                if action != prev_action: num_switches += 1
                prev_action = action
            direction_penalty = -2 * num_switches
            movement_cost = -1 * len(path)

            self.red_path_rewards[timestep, i] = red_physical_reward + movement_cost + direction_penalty


    def test_rollout(self,
            timestep, red_path, blue_path,
            observed_red_location = (0, 0), observed_blue_location = None):
        """ Simulates the entire game given blue's path and box changes, and returns red's outcome """
        
        running_env = self.env.copy()
        running_env.reset()
        
        # simulate the whole trial with red/blue path, no stalling
        running_env.red_agent.location = observed_red_location
        running_env.red_agent.path = red_path
        running_env.red_agent.level = 0 
        if observed_blue_location:
            running_env.blue_agent.location = observed_blue_location
        else:
            running_env.blue_agent.location = self.blue_agent.start_location
        running_env.blue_agent.path = blue_path
        
        _, outcome = running_env.run_exp2(
            verbose = False,
            no_stall = True,
            time_limit = 10 - timestep + 1,
            copy_trial_red = True,
            copy_trial_blue = True)
        
        final_red_location = running_env.red_agent.location
        red_distance_to_goal = running_env.world.get_gridsquares_between(
            final_red_location, running_env.world.get_goal_location())
        
        return outcome, red_distance_to_goal


    def calculate_red_Q(self,
            timestep, est_box_move = None, est_blue_path = [(0, 0)],
            only_shortest_paths = True, red_physical_reward = 20):
        """ Based on L2 red's estimate of blue's policy, calculates optimality of each path """
        
        Q_red = []

        red_location = self.state_space[timestep, 0]
        blue_location = self.state_space[timestep, 1]
        
        if est_box_move:
            est_box_location, est_box_action = est_box_move
            box_new_location = get_location_from_action(
                self.env.world, est_box_location, est_box_action)
            box = self.env.world.get_box_at_location(est_box_location)
            if box:
                box.location = box_new_location
                self.get_path_rewards(timestep, only_shortest_paths)
                box.location = est_box_location

        for i, red_path in enumerate(self.all_red_paths[timestep]):
            outcome, red_distance_to_goal = self.test_rollout(
                timestep, red_path.copy(), est_blue_path.copy(), red_location, blue_location)
            if outcome == 'success':
                Q_red.append(self.red_path_rewards[timestep, i])
            elif outcome == 'fail':
                Q_red.append(self.red_path_rewards[timestep, i] - red_physical_reward)

        return Q_red