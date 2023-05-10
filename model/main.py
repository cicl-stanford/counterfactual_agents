from environment import *
from gridworld import *
from agent import *
from models import *
from game import *
from blue_planner import *
from red_planner import *

from collections import defaultdict
import csv
import sys
import os
import argparse
import numpy as np
import random


def parse_arguments():
    parser = argparse.ArgumentParser("counterfactual_agents argument parser")
    
    # General arguments
    parser.add_argument('--experiment', type=int, default=1,
        help='whether to run trials from experiment 1 or 2')
    parser.add_argument('--trial', type=int, default=0,
        help = 'which trial to generate specifically')
    parser.add_argument('--visualize', action='store_true', default=False,
        help='run pygame animations and make gif')
    parser.add_argument('--verbose', action='store_true', default=False,
        help='verbosely print info while simulating or not')
    parser.add_argument('--make-images', action='store_true', default=False,
        help='make images of all grids for specified experiment')

    # Model arguments
    parser.add_argument('--cf', action='store_true', default=False,
        help='run counterfactual model predictions')
    parser.add_argument('--int', action='store_true', default=False,
        help='run intention model predictions')
    parser.add_argument('--effort', action='store_true', default=False,
        help='run effort model predictions')
    parser.add_argument('--n-simulations', type=int, default=500,
        help='number of simulations to run counterfactual model')

    return parser.parse_args()


def fix_seed(seed):
    np.random.seed(seed)
    random.seed(seed)


if __name__ == '__main__':
    arglist = parse_arguments()
    fix_seed(1)

    if arglist.experiment in [1, 2]:
        grid_dir = "grids/experiment{}/{}".format(arglist.experiment, arglist.trial)
        grid_info = json.load(open('trials/experiment{}/experiment{}.json'.format(
            arglist.experiment, arglist.experiment), 'r'))[arglist.trial - 1]
        trials = read_trials("experiment{}".format(arglist.experiment))

        trial_data = []
        js_data = []
        trial_images = []
        
        if arglist.make_images:
            for trial_num in range(1, len(trials) + 1):
                if arglist.trial > 0 and arglist.trial != trial_num:
                    continue
                gw = GridWorld(arglist.experiment, time_limit = 10)
                gw.read_world(filename = trial_num)
                g = Game(gw)
                g.on_init(no_sidebar = True)
                g.on_render()
                g.screenshot(time = None, 
                    file_name = 'grid_images/experiment{}/{}'.format(arglist.experiment, trial_num))
                g.on_cleanup()

        for trial in trials:
            trial_num = trial["num"]
            fix_seed(trial_num)
            if arglist.trial > 0 and arglist.trial != trial_num: continue

            print('----- generating experiment {} trial {} -----'.format(arglist.experiment, trial_num))
            
            # initialize gridworld
            gw = GridWorld(arglist.experiment, time_limit = 10)
            if "grid" in trial.keys():
                gw.read_world(filename = trial["grid"])
            else:   
                gw.read_world(filename = str(trial_num))
            
            trial_dir = "trials/experiment{}/".format(arglist.experiment) + str(trial_num)
            
            exp = "exp1" if arglist.experiment == 1 else "exp2"
            red_level = 0 if arglist.experiment == 1 else trial["red_level"]
            red_path = trial["red_path"] if arglist.experiment == 1 else []
            box_changes = trial["box_changes"] if arglist.experiment == 1 else None

            # initialize red and blue agents
            a_red = Agent(
                color = Color.RED,
                location = tuple(trial["red_start"]),
                level = red_level,
                path = red_path.copy(),
                prob_stall = 0.1)
            
            a_blue = Agent(
                color = Color.BLUE,
                location = tuple(trial["blue_start"]),
                level = 1,
                intention = trial["blue_intention"],
                path = trial["blue_path"].copy(),
                prob_stall = 0.1)

            # run agents within baseline trial environment
            env = Environment(exp, gw, [a_red, a_blue], 
                generating_trials = True, trial_dir = trial_dir)
            env.setup_planners()
            
            if arglist.experiment == 1:
                original_runtime, outcome = env.run_exp1(
                    paths = [trial["red_path"].copy(), 
                    trial["blue_path"].copy()], 
                    box_changes = box_changes.copy(),
                    verbose = arglist.verbose, 
                    visualize = arglist.visualize, 
                    copy_trial = True)

            if arglist.experiment == 2:
                original_runtime, outcome = env.run_exp2(
                    verbose = arglist.verbose,
                    visualize = arglist.visualize,
                    no_stall = True)
                        
            # run additional models (counterfactual, intention, effort)
            if arglist.cf:
                cf_neutral = CounterfactualModel(
                        exp, env,
                        trial["red_path"].copy(), 
                        trial["blue_path"].copy(),
                        box_changes)
                rate = cf_neutral.simulate_all(
                        num_simulations = arglist.n_simulations,
                        verbose = arglist.verbose)

            if arglist.int:
                if arglist.experiment == 1:
                    a, b, c = 0.7, 0.3, 2
                    red_reward = 16
                if arglist.experiment == 2:
                    a, b, c = 1, 0.2, 1.1
                    red_reward = 20

                intention = IntentionModel(
                        exp, env, 
                        trial["red_path"].copy(), 
                        trial["blue_path"].copy(),
                        box_changes,
                        a = a, b = b, c = c, 
                        red_reward = red_reward)

                inferred_intention, numerical_intention = intention.infer_intention()
                
            if arglist.effort:
                effort = EffortModel(
                        exp, env, box_changes, trial["blue_path"])
                computed_effort = effort.compute()       

    else:
        sys.exit(0)
