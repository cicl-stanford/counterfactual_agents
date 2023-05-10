from game import *
from blue_planner import *
from red_planner import *
from utils import get_action_from_location

import os#; root_dir = os.getcwd()
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import sys
sys.setrecursionlimit(10000)
from collections import defaultdict
from datetime import datetime
import operator
import numpy as np


class Environment:
    def __init__(self,
            exp, gridworld, agents, generating_trials = False, trial_dir = 'trials'):
        """ Initiates environment """

        self.exp = exp
        self.world = gridworld
        self.agents = agents
        self.red_agent = agents[0]
        self.blue_agent = agents[1]
        self.generating_trials = generating_trials
        self.trial_dir = trial_dir
        self.game = None


    def reached_goal(self):
        """ Checks if red agent has reached the star """

        if self.red_agent is None:
            return False
        return self.world.get_goal_location() == self.red_agent.location


    def setup_planners(self, 
            observed_red_location = None, observed_blue_location = None, intention = None):
        """ Initiates planners for red and blue agent """

        if self.blue_agent:
            blue_intention = intention if intention else self.blue_agent.intention
            if self.blue_agent.level == 1:
                self.blue_agent.planner = L1BluePlanner(
                    self.exp, self, social_type = blue_intention)
            else:
                self.blue_agent.planner = L3BluePlanner(
                    self.exp, self, social_type = blue_intention)

        if self.red_agent:
            if self.red_agent.level == 0:
                self.red_agent.planner = L0RedPlanner(self.exp, self)

            if self.red_agent.level == 2:
                self.red_agent.planner = L2RedPlanner(self.exp, self)
                
                if observed_red_location: 
                    self.red_agent.planner.state_space[1, 0] = observed_red_location
                else:
                    self.red_agent.planner.state_space[1, 0] = self.red_agent.start_location
                
                if observed_blue_location:
                    self.red_agent.planner.state_space[1, 1] = observed_blue_location
                else:
                    self.red_agent.planner.state_space[1, 1] = self.blue_agent.start_location


    def execute_exp1(self,
            agent, path, verbose, stalling,
            cf_neutral, copy_trial = False):
        """ Executes a single action from agent's path, accounting for obstacles;
            Returns whether the red agent needs to replan due to obstacle """
                
        # imperfect execution (only for cf models, after blue's first impact)
        if (not self.generating_trials and stalling
            and bernoulli(agent.prob_stall) 
            and agent.color == Color.RED):
            if verbose: print('\t{} stalled'.format(agent.name))
            return False
        
        # for blue agent only: terminate if no path
        if len(path) == 0: return False
            
        action = tuple(path.pop(0))
        
        # for red agent only: check if obstacle ahead
        if agent.color == Color.RED and not copy_trial:
            if (action != STAY
                and not self.world.is_valid_action(
                    agent.location, action, self.blue_agent.location)):
                    return True
                
        new_location = self.world.get_new_location(agent.location, action)
        agent.move_to(new_location)
        
        # for blue agent only: move held boxes too
        if agent.color == Color.BLUE and not cf_neutral:
            self.world.move_held_boxes(action)

        return False


    def run_exp1(self,
            paths = [[], []], box_changes = defaultdict(lambda : []), 
            original_runtime = 0, verbose = False, visualize = False, 
            no_sidebar = False, cf_opposite = False, cf_neutral = False, 
            no_stall = False, intention = False, time_limit = 10, copy_trial = False):
        """ Simulates agent interacting with environment
            (for experiment 1: agents move simultaneously) """
        
        # initialize game visualization
        if visualize:
            self.game = Game(self.world, self.agents)
            self.game.on_init(no_sidebar = no_sidebar)
            
            make_dir(self.trial_dir)
                
            # make first slide with initial positions
            self.game.on_render(time = self.world.time_limit)
            self.game.screenshot(
                        time = time_limit,
                        file_name = '{}/00'.format(
                            self.trial_dir))

        self.outcome = 'fail'
        timestep = 0
        replanning = False
        last_box_moved_at = -1
        first_impact_at = 10
        
        for timestep in range(1, time_limit + 1):
            if verbose: print('\n   timestep {}'.format(timestep))
            
            stalling = False if no_stall else True
            
            # for cf model: only add simulation noise
            # once blue would've had impact on red
            if cf_opposite or cf_neutral:
                if timestep < first_impact_at:
                    stalling = False
                if timestep == 1:
                    paths[0].clear()

            change_red_path = False
            
            for i, a in reversed(list(enumerate(self.agents))):
                # use None to show one agent for instruction trials
                if a is not None:
                    # have planner generate initial path for red if needed
                    if len(paths[0]) == 0 and not copy_trial:
                        paths[0] = self.red_agent.planner.plan_red_path(count_boxes = replanning)

                    if verbose: print('{} path: {}'.format(a.name, paths[i]))
                
                    red_obstacle = self.execute_exp1(a, paths[i], verbose, stalling, cf_neutral, copy_trial)
                    if a.color == Color.RED: change_red_path = red_obstacle
            
            # change boxes
            for b in self.world.get_boxes():
                if (str(timestep) in box_changes and list(b.location) in box_changes[str(timestep)]):
                    b.held = not b.held
                    if verbose: print('\tbox at {} changed'.format(b.location))
                    if b.held: last_box_moved_at = timestep + 1
                    if b.held and first_impact_at == 10: 
                        first_impact_at = timestep + 1
            
            if visualize and not change_red_path:
                self.game.on_render(time = (self.world.time_limit - timestep))
                self.game.screenshot(
                    time = time_limit - timestep,
                    file_name = '{}/{:02d}'.format(
                        self.trial_dir, timestep))
            
            if self.reached_goal():
                self.outcome = 'success'
                if verbose: print('\treached goal!')
                if not cf_opposite: break
            
            # replan red path if needed and execute first action of new path
            if change_red_path and not copy_trial:
                paths[0].clear()
                replanning = True
                if verbose: print('\treplanning red path...')
                paths[0] = self.red_agent.planner.plan_red_path(count_boxes = replanning)
                
                if verbose: print('new red player path: {}'.format(paths[0]))
    
                self.execute_exp1(self.red_agent, paths[0], verbose, stalling, cf_neutral)
                
                if visualize:
                    self.game.on_render(time = (self.world.time_limit - timestep))
                    self.game.screenshot('{}/{:02d}.png'.format(self.trial_dir, timestep))
                    
        if visualize:
            self.finish_game(timestep, no_sidebar)

        verb_outcome = 'failed' if self.outcome == 'fail' else 'succeeded'
        return timestep, verb_outcome


    def execute_exp2(self, 
            agent, verbose, stalling, cf_neutral = False):
        """ Executes a single action from agent's path, accounting for obstacles;
            Returns whether agent needs to replan due to obstacle, and if stalled """

        # imperfect execution (only for cf models, after blue's first impact)
        if (stalling and bernoulli(agent.prob_stall) 
            and agent.color == Color.RED):
            if verbose: print('\t{} stalled'.format(agent.name))
            return False, True
        
        if len(agent.path) == 0: return False, False
        action = tuple(agent.path.pop(0))
        
        # for red agent: check for obstacles
        if agent.color == Color.RED:
            if (action != STAY 
                and not self.world.is_valid_action(
                    agent.location, action, self.blue_agent.location)):
                return True, False
        
        # for blue agent: check for obstacles, handle moving boxes
        if not cf_neutral:
            if agent.color == Color.BLUE:
                if action in HOLD_ACTIONS:
                    box_side = tuple([num / 2 for num in action])
                    box_location = self.world.get_new_location(agent.location, box_side)
                    box = self.world.get_box_at_location(box_location)
                    if not box:
                        return True, False
                    agent.hold_box(box)
                    return False, False
            
                if action in RELEASE_ACTIONS:
                    box_side = tuple([num / 3 for num in action])
                    box_location = self.world.get_new_location(agent.location, box_side)
                    box = self.world.get_box_at_location(box_location)
                    if not box:
                        return True, False
                    agent.release_box(box)
                    return False, False

                moving_box = agent.holding_box
                held_box_location = agent.box.location if agent.holding_box else None
                
                if (action != STAY
                    and not self.world.is_valid_action(
                        agent.location, action, self.red_agent.location,
                        moving_box = moving_box, box_location = held_box_location)):
                    return True, False

        # move agent (and held box if applicable) to new location
        new_location = self.world.get_new_location(agent.location, action)
        if agent.holding_box:
            box_new_location = self.world.get_new_location(agent.box.location, action)
        else:
            box_new_location = None
        agent.move_to(new_location, box_new_location)

        return False, False
        

    def run_exp2(self,
            original_runtime = 0, verbose = False, visualize = False,
            no_sidebar = False, cf_opposite = False, cf_neutral = False,
            no_stall = False, time_limit = 10, first_impact_at = 10,
            copy_trial_red = False, copy_trial_blue = False):
        """ Simulates red and blue agents interacting with environment
            (for experiment 2: agents move sequentially) """

        # initialize game visualization
        if visualize:
            self.game = Game(self.world, self.agents)
            self.game.on_init(no_sidebar = no_sidebar)
            
            # make first slide with initial positions
            make_dir(self.trial_dir)
            self.game.screenshot(
                time = time_limit, whose_turn = 'red',
                file_name = '{}/00'.format(self.trial_dir))

        self.outcome = 'fail'
        timestep = 0
        red_path = []
        blue_path = []

        # alternate between red and blue agent (red moves first)
        for long_timestep in range(1, (2 * time_limit) + 1):
            if long_timestep % 2 == 0:
                timestep = int(long_timestep / 2)
                if verbose: print("\n\n(blue) timestep: {}".format(timestep))
                blue_moving = True
                red_moving = False
                color = "blue"
            else:
                timestep = int(long_timestep / 2) + 1
                if verbose: print("\n\n(red) timestep: {}".format(timestep))
                blue_moving = False
                red_moving = True
                color = "red"

            stalling = False if no_stall else True

            # for cf model: only add simulation noise
            # once blue would've had impact on red
            if cf_opposite or cf_neutral:
                if timestep < first_impact_at:
                    stalling = False
            
            change_red_path = False
            change_blue_path = False

            # run red agent on this timestep
            if red_moving:
                if verbose: self.red_agent.print_status()              

                if self.red_agent.level == 0 or cf_neutral:
                    if len(self.red_agent.path) == 0:
                        self.red_agent.path = self.red_agent.planner.plan_red_path(
                            only_shortest_paths = False, time_limit = 11 - timestep)
                    
                    planned_action = self.red_agent.path[0]
                    is_red_obstacle, did_red_stall = self.execute_exp2(
                        self.red_agent, verbose, stalling, cf_neutral)
                    change_red_path = is_red_obstacle

                    if (not is_red_obstacle) and (not did_red_stall):
                        self.red_agent.planner.action_space[timestep, 0] = planned_action
                    else:
                        self.red_agent.planner.action_space[timestep, 0] = STAY
                    self.red_agent.planner.state_space[timestep + 1, 0] = self.red_agent.location

                if self.red_agent.level == 2 and not cf_neutral:
                    blue_changed = True
                    
                    if timestep >= 2:
                        if timestep > 2:
                            prev_est_blue_intention = self.red_agent.planner.intention_estimates[timestep - 1]
                            prev_est_prob = self.red_agent.planner.intention_probs[timestep - 1]
                        else:
                            # begin with uniform prior over help and hinder
                            prev_est_blue_intention = "help"
                            prev_est_prob = 0.5
                            self.red_agent.planner.intention_estimates[timestep] = "help"
                            self.red_agent.planner.intention_probs[timestep] = 0.5
                        
                        # get new estimate of L1 blue's intention based on blue's previous action
                        cur_est_blue_intention, cur_est_prob = self.red_agent.planner.estimate_blue_intention(
                            timestep, prev_est_blue_intention, prev_est_prob, verbose)

                        prev_blue_action = self.red_agent.planner.action_space[timestep - 1, 1]
                        stored_location = self.red_agent.planner.state_space[timestep, 1]
                            
                        if verbose:
                            print(("\nprevious blue intention estimate: "
                                  "{} with {} probability").format(
                                  prev_est_blue_intention, prev_est_prob))
                            print(("\nnew blue intention estimate: "
                                   "{} with {} probability").format(
                                   cur_est_blue_intention, cur_est_prob))
                        
                        if (prev_est_blue_intention == cur_est_blue_intention
                                and timestep >= 3 and not cf_neutral):
                            blue_changed = False
                            if verbose: print("\nblue intention estimate didn't change")
                        
                        # based on new blue intention estimate, estimate blue's likely policy
                        if blue_changed:
                            est_box_move, est_blue_path = self.red_agent.planner.estimate_blue_policy(
                                timestep, cur_est_blue_intention)
                            self.red_agent.planner.est_box_move = est_box_move
                            self.red_agent.planner.est_blue_path = est_blue_path
                            
                            # based on L1 blue's likely policy, calculate optimality of possible paths
                            self.red_agent.planner.get_path_rewards(timestep, only_shortest_paths = True)
                            Q_red = self.red_agent.planner.calculate_red_Q(
                                timestep, est_box_move, est_blue_path,
                                only_shortest_paths = True)
                        
                            exists_successful_path = any([q > 0 for q in Q_red])
                        
                            # if there are no paths <= 10 in length, sample longer paths
                            if not exists_successful_path:
                                self.red_agent.planner.get_path_rewards(
                                    timestep, only_shortest_paths = False)
                                Q_red = self.red_agent.planner.calculate_red_Q(
                                    timestep, est_box_move, est_blue_path,
                                    only_shortest_paths = False)
                                exists_successful_path = any([q > 0 for q in Q_red])
                    
                    else:
                        self.red_agent.planner.get_path_rewards(
                            timestep, only_shortest_paths = True)
                        Q_red = self.red_agent.planner.calculate_red_Q(timestep)
                        exists_successful_path = any([q > 0 for q in Q_red])
                        
                        # if there are no paths <= 10 in length, sample longer paths
                        if not exists_successful_path:
                            self.red_agent.planner.get_path_rewards(
                                timestep, only_shortest_paths = False)
                            Q_red = self.red_agent.planner.calculate_red_Q(
                                timestep, only_shortest_paths = False)
                            exists_successful_path = any([q > 0 for q in Q_red])
                    
                    if copy_trial_red:  
                        optimal_red_path = self.red_agent.path.copy()   
                        self.red_agent.planner.optimal_red_path = self.red_agent.path.copy()    
                    else:   
                        # red should update its path if its estimate of blue's intention changed
                        if blue_changed:  
                            if Q_red != []: 
                                optimal_choice = np.argmax(Q_red)   
                                optimal_red_path = self.red_agent.planner.all_red_paths[timestep][optimal_choice]   
                            else:   
                                optimal_red_path = [STAY]   
                            self.red_agent.planner.optimal_red_path = optimal_red_path.copy()   
                            if verbose: print("\nnew optimal red path: {}".format(optimal_red_path))   

                        # otherwise, red should proceed with its already-established path   
                        else:   
                            optimal_red_path = self.red_agent.planner.optimal_red_path[:].copy()    
                            if self.red_agent.planner.action_space[timestep - 1, 0] != STAY:    
                                optimal_red_path.pop(0) 
            
                            if len(optimal_red_path) > 0:   
                                self.red_agent.planner.optimal_red_path = optimal_red_path  
                            else:   
                                self.red_agent.planner.optimal_red_path = [STAY]    
                            
                        self.red_agent.path = optimal_red_path.copy()

                    is_red_obstacle, did_red_stall = self.execute_exp2(
                        self.red_agent, verbose, stalling, cf_neutral)
                    
                    change_red_path = (timestep > 1
                                        and is_red_obstacle
                                        and self.red_agent.planner.action_space[timestep - 1, 1] == STAY)

                    if (not is_red_obstacle) and (not did_red_stall):
                        if optimal_red_path == []: optimal_red_path = [STAY]
                        self.red_agent.planner.action_space[timestep, 0] = optimal_red_path[0]
                    else:
                        self.red_agent.planner.action_space[timestep, 0] = STAY
                    self.red_agent.planner.state_space[timestep + 1, 0] = self.red_agent.location
                
            # run blue agent on this timestep
            if blue_moving:
                if len(self.blue_agent.path) == 0 and timestep == 1:
                    self.blue_agent.planner.simulate_all_box_moves()
                    box_moves, box_moves_opp = self.blue_agent.planner.plan_box_moves(
                        cur_red_location, self.world.get_goal_location())
                    
                    Q_blue = self.blue_agent.planner.train_blue(
                        box_moves, box_moves_opp, get_Q = True,
                        observed_red_location = cur_red_location,
                        observed_blue_location = cur_blue_location)

                    blue_paths = self.blue_agent.planner.train_blue(
                        box_moves, box_moves_opp,
                        observed_blue_location = cur_blue_location,
                        get_all_blue_paths = True)
                    
                    best_box_move = max(Q_blue, key=Q_blue.get)
                    self.blue_agent.path = blue_paths[best_box_move]
                    
                    self.red_agent.location = cur_red_location
                    self.blue_agent.location = cur_blue_location

                if verbose: self.blue_agent.print_status()

                if len(self.blue_agent.path) >= 1:
                    planned_blue_action = tuple(self.blue_agent.path[0])
                else:
                    planned_blue_action = STAY

                change_blue_path, _ = self.execute_exp2(self.blue_agent, verbose, stalling, cf_neutral)

                if not change_blue_path:
                    self.red_agent.planner.action_space[timestep, 1] = planned_blue_action
                else:
                    self.red_agent.planner.action_space[timestep, 1] = STAY
                self.red_agent.planner.state_space[timestep + 1, 1] = self.blue_agent.location
                        
            # change boxes only if blue is moving on this timestep
            if blue_moving:
                if self.blue_agent.holding_box:
                    if verbose: print('\tbox is at {}'.format(self.blue_agent.box.location))

            if visualize and not change_red_path and not change_blue_path:
                self.game.screenshot(
                    time = time_limit - timestep,
                    whose_turn = opp_color[color],
                    file_name = '{}/{:02d}'.format(
                        self.trial_dir, long_timestep))
            
            if self.reached_goal():
                self.outcome = 'success'
                if verbose: print('\treached goal!')
                if not cf_opposite: break
            
            # replan red path if necessary
            if change_red_path and red_moving and not copy_trial_red:
                if verbose: print('\treplanning red path...')
                
                self.red_agent.path = self.red_agent.planner.plan_red_path(
                    only_shortest_paths = False)
                all_red_paths, _ = self.red_agent.planner.plan_red_path(
                    only_shortest_paths = False, get_all_paths = True)
                
                red_action = self.red_agent.path[0]
                self.execute_exp2(self.red_agent, verbose, stalling = False, cf_neutral = cf_neutral)
                self.red_agent.planner.action_space[timestep, 0] = red_action
                self.red_agent.planner.state_space[timestep + 1, 0] = self.red_agent.location

                if verbose: self.red_agent.print_status()

                if visualize:
                    self.game.screenshot(
                        time = time_limit - timestep,
                        whose_turn = opp_color[color],
                        file_name = '{}/{:02d}'.format(
                            self.trial_dir, long_timestep))
            
            # replan blue path if necessary
            if change_blue_path and blue_moving and not copy_trial_blue:
                if verbose: print('\nreplanning blue path...')
                
                self.blue_agent.path.insert(0, planned_blue_action)
                
                if verbose: self.blue_agent.print_status()
                
                if visualize:
                    self.game.screenshot(
                        time = time_limit - timestep,
                        whose_turn = opp_color[color],
                        file_name = '{}/{:02d}'.format(
                            self.trial_dir, long_timestep))

        if visualize:
            self.finish_game(timestep, no_sidebar, long_timestep, alternating = True)

        return timestep, self.outcome
    
    
    def finish_game(self, timestep, no_sidebar,
                    long_timestep = None, alternating = False):
        """ Takes final screenshots and makes gif """

        if not no_sidebar:
            screen_time = long_timestep if long_timestep else timestep
            self.game.screenshot(
                time = self.world.time_limit - timestep,
                outcome = self.outcome,
                file_name = '{}/{:02d}'.format(
                    self.trial_dir, screen_time + 1))
        
        make_gif(self.trial_dir, self.trial_dir + '/full',
            one_agent = any([a.level == -1 for a in self.agents]))
        self.game.on_cleanup()

    
    def reset(self):
        """ Resets state of all boxes in the gridworld and location of the agent """
    
        for b in self.world.get_boxes():
            b.location = b.start_location
        for a in self.agents:
            a.location = a.start_location
            if a.box:
                a.box = None
                a.holding_box = False


    def copy(self):
        """ Makes a copy of the environment """

        stored_game = self.game
        self.game = None
        copied_env = copy.deepcopy(self)
        self.game = stored_game
        return copied_env