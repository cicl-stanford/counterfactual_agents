from collections import defaultdict
import numpy as np
import scipy as sp
import functools
import copy
import itertools

from agent import *
from environment import *
from gridworld import *
from utils import *

class L1BluePlanner:
    def __init__(self, exp, env, social_type):
        """ Initiates level-1 blue planner """
        
        self.exp = exp
        self.env = env # agents and gridworld
        self.red_agent, self.blue_agent = self.env.agents
        self.social_type = social_type # help or hinder
        self.social_param = 0.5 if self.social_type == 'help' else -0.5
        self.discount = 0.99
        self.alpha = 0.9

        self.goal_location = self.env.world.get_goal_location()
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


    def simulate_multiple_box_moves(self):
        """ Simulate all possible two-box movements """

        red_paths_multiple = {}

        box_location_one = self.box_locations[0]
        code_one = self.box_location_to_code[box_location_one]
        box_one = self.boxes[code_one]
            
        for box_location_two in self.box_locations:
            code_two = self.box_location_to_code[box_location_two]
            box_two = self.boxes[code_two]
            if (box_location_one == box_location_two): continue
            
            for (box_action_one, box_action_two) in itertools.product(self.actions, repeat=2):
                # check if both box moves are valid on their own
                if ((box_location_one, box_action_one) in self.all_red_paths.keys() 
                    and (box_location_two, box_action_two) in self.all_red_paths.keys()):
                    
                    box_one_new_location = get_location_from_action(
                        self.env.world, box_one.start_location, box_action_one)
                    box_one.location = box_one_new_location
                    
                    box_two_new_location = get_location_from_action(
                        self.env.world, box_two.start_location, box_action_two)
                    box_two.location = box_two_new_location

                    # move boxes and blue agent accordingly (if the box move is valid)
                    if box_action_two == UP or box_action_two == DOWN:
                        self.blue_agent.location = get_location_from_action(
                            self.env.world, box_two.location, DOWN)
                    if self.blue_agent.location == box_two.location:
                        self.blue_agent.location = get_location_from_action(
                            self.env.world, box_two.location, UP)
                    if box_action_two == LEFT or box_action_two == RIGHT:
                        self.blue_agent.location = get_location_from_action(
                            self.env.world, box_two.location, LEFT)
                    if self.blue_agent.location == box_two.location:
                        self.blue_agent.location = get_location_from_action(
                            self.env.world, box_two.location, RIGHT)
                    if box_action_two == STAY: 
                        self.blue_agent.location = self.blue_agent.start_location
                    
                    # detect if box move is invalid (would move through wall or out of grid)
                    if ((self.blue_agent.location not in self.locations) 
                        or (box_one.location == box_one.start_location and box_action_one != STAY) 
                        or (box_two.location == box_two.start_location and box_action_two != STAY)):
                        self.env.reset()
                        continue

                    # get all red paths for this configuration of boxes
                    all_red_paths, _ = self.env.red_agent.planner.plan_red_path(
                        get_all_paths = True, only_shortest_paths = True)
                    multiple_box_move = ((box_location_one, box_action_one), (box_location_two, box_action_two))
                    red_paths_multiple[multiple_box_move] = all_red_paths
                    
                    self.env.reset()

        return red_paths_multiple

    def simulate_all_box_moves(self, multiple = False):
        """ Tests out all possible box movements and stores associated red paths """
    
        red_paths = {}

        for box in self.boxes:
            box_start_location = box.location
            for box_action in self.actions:

                # check that box move is valid
                box_new_location = get_location_from_action(
                    self.env.world, box_start_location, box_action)

                if (self.env.world.get_gridsquare_at(box_new_location) 
                    and self.env.world.get_gridsquare_at(box_new_location).name == 'Box'
                    and box_action != STAY) or (not self.env.world.avoids_walls(
                        box_start_location, box_new_location, box_action)):
                    self.env.reset()
                    continue

                box.location = box_new_location

                # move the blue agent accordingly (if the box move is valid)
                if box_action == UP or box_action == DOWN:
                    blue_hold_location = get_location_from_action(
                        self.env.world, box_start_location, DOWN)
                    blue_release_location = get_location_from_action(
                        self.env.world, box_new_location, DOWN)

                    if self.blue_agent.location == box.location:
                        blue_hold_location = get_location_from_action(
                            self.env.world, box_start_location, UP)
                        blue_release_location = get_location_from_action(
                            self.env.world, box_new_location, UP)

                if box_action == LEFT or box_action == RIGHT:
                    blue_hold_location = get_location_from_action(
                        self.env.world, box_start_location, LEFT)
                    blue_release_location = get_location_from_action(
                        self.env.world, box_new_location, LEFT)

                    if self.blue_agent.location == box.location:
                        blue_hold_location = get_location_from_action(
                            self.env.world, box_start_location, RIGHT)
                        blue_release_location = get_location_from_action(
                            self.env.world, box_new_location, RIGHT)

                if box_action == STAY:
                    blue_hold_location = self.blue_agent.start_location
                    blue_release_location = self.blue_agent.start_location

                self.blue_agent.move_to(blue_release_location)

                # detect if box move and blue agent move are both valid 
                # (if it'd move through wall, on another box, out of grid)
                if ((not self.env.world.avoids_walls(blue_hold_location, blue_release_location, box_action)) 
                    or (self.blue_agent.location not in self.locations) 
                    or (box.location not in self.locations) 
                    or (box.location == box.start_location and box_action != STAY)):
                    self.env.reset()
                    continue
            
                # get all red paths for this configuration of boxes
                all_red_paths, _ = self.env.red_agent.planner.plan_red_path(get_all_paths = True)
                red_paths[(box_start_location, box_action)] = all_red_paths

                self.env.reset()

        self.all_red_paths = red_paths
        if multiple: 
            self.all_red_paths = {**self.all_red_paths, **self.simulate_multiple_box_moves()}


    def plan_box_moves(self, start_location, goal_location, 
            try_multiple = False, time_limit = 10):
        """ Returns box location/action pairs that enable the intended red outcome """

        box_moves = [] # moves to take for blue's intention
        box_moves_opp = [] # moves for the opposite intention

        for box_move, red_paths in self.all_red_paths.items():
            if red_paths != []: shortest_path_len = len(min(red_paths, key=len)) - 1
            
            if self.social_type == "help":
                if len(red_paths) != 0 and shortest_path_len <= time_limit:
                    box_moves.append(box_move)
                else:
                    box_moves_opp.append(box_move)
            
            if self.social_type == "hinder":
                if len(red_paths) == 0:
                    box_moves.append(box_move)
                elif shortest_path_len > time_limit:
                    box_moves.append(box_move)
                else:
                    box_moves_opp.append(box_move)

        if len(box_moves) == 0 and try_multiple:
            self.simulate_all_box_moves(multiple = True)
            box_moves = self.plan_box_moves_multiple(
                start_location, goal_location)
        
        return box_moves, box_moves_opp


    def plan_box_moves_multiple(self, start_location, goal_location, 
            try_multiple = False, time_limit = 10):
        """ Returns box location/action pairs that enable the intended red outcome """

        box_moves = [] # moves to take for blue's intention
        box_moves_opp = [] # moves for the opposite intention

        for box_move, red_paths in self.all_red_paths.items():
            if red_paths != []: shortest_path_len = len(min(red_paths, key=len)) - 1
            
            if self.social_type == "help":
                if len(red_paths) != 0 and shortest_path_len <= time_limit:
                    box_moves.append(box_move)
                else:
                    box_moves_opp.append(box_move)
            
            if self.social_type == "hinder":
                if len(red_paths) == 0:
                    box_moves.append(box_move)
                elif shortest_path_len > time_limit:
                    box_moves.append(box_move)
                else:
                    box_moves_opp.append(box_move)
        
        return box_moves


    def rollout_game_exp1(self, 
            blue_path, box_changes, observed_red_location = (0, 0),
            observed_red_path = [], time_limit = 10,
            copy_trial = False, mod_box_location = None):
        """ Simulates entire game given blue's path and returns red's outcome """
        
        self.env.reset()

        # count all paths that red agent has before box change
        all_red_paths_before, _ = self.env.red_agent.planner.plan_red_path(get_all_paths = True)

        # simulate the whole trial with blue path and box changes
        self.red_agent.location = observed_red_location
        if mod_box_location: self.boxes[0].location = mod_box_location

        _, outcome = self.env.run_exp1(
            paths = [observed_red_path.copy(), blue_path.copy()], 
            box_changes = box_changes, verbose = False, 
            no_stall = True, intention = True, copy_trial = True)
        
        final_red_location = self.red_agent.location
        red_distance_to_goal = self.env.world.get_gridsquares_between(
            final_red_location, self.env.world.get_goal_location())

        # count all paths that red agent has after box change
        self.red_agent.location = self.red_agent.start_location
        all_red_paths_after, _ = self.env.red_agent.planner.plan_red_path(get_all_paths = True)
        
        self.env.reset()
        return outcome, all_red_paths_before, all_red_paths_after, red_distance_to_goal
        

    def rollout_game_exp2(self,
            blue_path, observed_red_location, observed_red_path,
            observed_blue_location, copy_trial, time_limit):
        """ Simulates entire game given blue's path and returns red's outcome """
        
        self.env.reset()
        self.red_agent.level = 0
        self.red_agent.location = observed_red_location
        self.blue_agent.location = observed_blue_location
        self.red_agent.path = observed_red_path
        self.blue_agent.path = blue_path

        # count all paths that red agent has before box change
        all_red_paths_before, _ = self.env.red_agent.planner.plan_red_path(
            get_all_paths = True, time_limit = time_limit)

        # simulate the whole trial with blue path and box changes
        _, outcome = self.env.run_exp2(
            verbose = False, no_stall = True, time_limit = time_limit,
            copy_trial_red = copy_trial, copy_trial_blue = copy_trial)
        
        final_red_location = self.red_agent.location
        red_distance_to_goal = self.env.world.get_gridsquares_between(
            final_red_location, self.env.world.get_goal_location())

        # count all paths that red agent has after box change
        self.red_agent.location = observed_red_location
        all_red_paths_after, _ = self.env.red_agent.planner.plan_red_path(
            get_all_paths = True, time_limit = time_limit)

        self.env.reset()
        return outcome, all_red_paths_before, all_red_paths_after, red_distance_to_goal
        

    def calculate_blue_Q(self,
            box_moves, box_moves_opp, box_move, blue_path, red_path,
            num_boxes_moved, red_distance_to_goal, all_red_paths_before,
            all_red_paths_after, a, b, c, red_reward, first_box_move = None):
        """ Returns blue's expected total reward from a given box move """
    
        box_location, box_action = box_move
        if blue_path == [STAY, STAY, STAY] or blue_path == [STAY, STAY] or blue_path == [STAY]: blue_path = []
        
        if all_red_paths_before != []:
            num_red_paths_before = len(all_red_paths_before)
            shortest_len_before = len(min(all_red_paths_before, key=len)) - 1
        else:
            num_red_paths_before = 0
            shortest_len_before = 10

        if all_red_paths_after != []:
            num_red_paths_after = len(all_red_paths_after)
            shortest_len_after = len(min(all_red_paths_after, key=len)) - 1
        else:   
            num_red_paths_after = 0
            shortest_len_after = 10
       
        # positive if there are more red paths after box move
        num_red_paths_change = num_red_paths_after - num_red_paths_before
        
        red_movement_cost = -1 * shortest_len_after
        blue_movement_cost = -1 * (len(blue_path) - num_boxes_moved)
        box_cost = 0 if box_action == STAY else -2 * num_boxes_moved
        
        # weights for Q-value features
        if self.social_type == "help":
            w1 = -a # punish helping agent for larger red_distance_to_goal
            w2 = b # reward helping agent for larger num_red_paths_change
            w3 = c # reward helping agent for smaller red_movement_cost
        else:
            w1 = a 
            w2 = -b
            w3 = -c
        
        if first_box_move: box_move = (first_box_move, box_move)

        # blue should get positive or negative reward depending on expected red outcome   
        blue_reward = 0.5 * red_reward if box_move in box_moves else -0.5 * red_reward
        
        total_reward = (blue_reward + blue_movement_cost + box_cost
                        + (w1 * red_distance_to_goal)
                        + (w2 * num_red_paths_change)
                        + (w3 * red_movement_cost))

        return total_reward


    def train_blue(self, box_moves, box_moves_opp = [], get_Q = False, cf_opp = False,
                    observed_red_location = (0, 0), observed_red_path = [],
                    observed_blue_location = None, observed_box_move = None,
                    get_all_blue_paths = False, time_limit = 10, intention = False, 
                    mod_box_location = None, a = 2, b = 0.7, c = 1, red_reward = 20):
        """ Returns blue agent's optimal path and/or Q-values for all possible policies """
        
        if observed_blue_location:
            observed_blue_location = observed_blue_location
        else:
            observed_blue_location = self.blue_agent.start_location

        if len(box_moves) == 0:
            if not get_Q and not cf_opp and not get_all_blue_paths: 
                return [(0, 0)]

        blue_paths = {} # dictionary of blue paths
        box_changes = {} # dictionary of box changes
        Q_blue = {} # expected rewards for blue

        # combination of box moves for blue's intention + opposite intention
        all_box_moves = box_moves + box_moves_opp
        original_all_box_moves = all_box_moves.copy()

        for i in range(len(all_box_moves)):
            if type(all_box_moves[i][0][0]) is tuple:
                all_box_moves[i] = all_box_moves[i][1]

        for i, box_move in enumerate(all_box_moves):
            self.env.reset()
            box_location, box_action = box_move
            num_boxes_moved = 2 if type(original_all_box_moves[i][0][0]) is tuple else 1
            first_box_move = None

            if num_boxes_moved == 2: # move the first box manually
                first_box_location = original_all_box_moves[i][0][0]
                first_box_action = original_all_box_moves[i][0][1]
                first_box_code = self.box_location_to_code[first_box_location]
                first_box = self.boxes[first_box_code]
                first_box.location = get_location_from_action(
                    self.env.world, first_box_location, first_box_action)
                first_box_move = (first_box_location, first_box_action)
            
            move_key = (first_box_move, box_move) if num_boxes_moved == 2 else box_move

            # 1. get blue's target location (adjacent to the box depending on box action)
            if box_action == DOWN or box_action == UP:
                if observed_blue_location[1] >= box_location[1]:
                    target_location = get_location_from_action(self.env.world, box_location, DOWN)
                    box_hold_action, box_release_action = HOLD_UP, RELEASE_UP

                if (observed_blue_location[1] < box_location[1] 
                    or (target_location[1] == self.env.world.height - 1 and box_action == DOWN)):
                    target_location = get_location_from_action(self.env.world, box_location, UP)
                    box_hold_action, box_release_action = HOLD_DOWN, RELEASE_DOWN

            elif box_action == LEFT or box_action == RIGHT:
                if observed_blue_location[0] <= box_location[0]:
                    target_location = get_location_from_action(self.env.world, box_location, LEFT)
                    box_hold_action, box_release_action = HOLD_RIGHT, RELEASE_RIGHT

                if (observed_blue_location[0] > box_location[0] 
                    or target_location[0] == 0 and box_action == LEFT):
                    target_location = get_location_from_action(self.env.world, box_location, RIGHT)
                    box_hold_action, box_release_action = HOLD_LEFT, RELEASE_LEFT

            else:
                target_location = self.blue_agent.start_location
                box_hold_action, box_release_action = None, None

            # 2. generate path for blue to its target location
            blue_path = []
            locations_in_path = self.env.world.get_shortest_path(
                observed_blue_location, target_location, (0, 0))
            if not locations_in_path: 
                blue_path = [STAY]
            else:
                for i in range(1, len(locations_in_path)):
                    blue_path.append(get_action_from_location(
                        locations_in_path[i - 1], locations_in_path[i]))
            
            if self.exp == "exp1":
                if blue_path == [STAY] and box_action != STAY:
                    blue_paths[box_location, box_action] = blue_path
                    box_changes[box_location, box_action] = {}
                else:
                    if len(blue_path) == 0: blue_path.append(STAY)
                    hold_timestep = len(blue_path)
                    release_timestep = hold_timestep + 2
                    box_new_location = get_location_from_action(
                        self.env.world, box_location, box_action)
                    blue_path.append(box_action)
                    blue_path.append(STAY)
                    blue_paths[box_location, box_action] = blue_path
                    box_change = {  str(hold_timestep):     [list(box_location)], 
                                    str(release_timestep):  [list(box_new_location)]}
                    box_changes[box_location, box_action] = box_change
                 
            if self.exp == "exp2":
                if blue_path == [STAY] and box_action != STAY:
                    blue_paths[box_location, box_action] = blue_path
                else:
                    if box_hold_action: blue_path.append(box_hold_action)
                    blue_path.append(box_action)
                    if box_release_action: blue_path.append(box_release_action)
                    if box_action == STAY: blue_path = [STAY, STAY]
                    blue_paths[box_location, box_action] = blue_path
                 
            if get_all_blue_paths: continue
            
            # 3. calculate blue agent's expected Q-value associated with this particular path
            copy_trial = True if intention else False
            
            if self.exp == "exp1":
                outcome, all_red_paths_before, all_red_paths_after, red_distance_to_goal = self.rollout_game_exp1(
                    blue_path, box_changes[box_location, box_action], observed_red_location, observed_red_path, copy_trial, mod_box_location)

            if self.exp == "exp2":
                outcome, all_red_paths_before, all_red_paths_after, red_distance_to_goal = self.rollout_game_exp2(
                    blue_path, observed_red_location, observed_red_path, observed_blue_location, copy_trial, time_limit)
        
            Q_blue[move_key] = self.calculate_blue_Q(box_moves, box_moves_opp, box_move, 
                                blue_path, observed_red_path, num_boxes_moved, red_distance_to_goal, 
                                all_red_paths_before, all_red_paths_after, a, b, c, red_reward, first_box_move)

        if get_Q: return Q_blue
        if blue_paths == {}: blue_paths = []
        if get_all_blue_paths: return blue_paths

        # select optimal blue path and box change
        optimal_move = max(Q_blue, key=Q_blue.get)
        
        if self.exp == "exp1": 
            return blue_paths[optimal_move], box_changes[chosen_move]
        return blue_paths[optimal_move]
