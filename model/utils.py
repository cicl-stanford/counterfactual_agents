import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import json
import csv
import numpy as np
from numpy.random import rand
from scipy.stats import binom
import shutil
import pygame
from collections import defaultdict


class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    FLOOR = (255, 255, 255)  # white
    LINE = (200, 200, 200)   # light grey
    WALL = (0, 0, 0)         # black
    #DOOR = (165, 42, 42)     # brown
    BOX = (0, 0, 0)
    RED = (255, 60, 60)
    LIGHT_RED = (255, 190, 190)
    BLUE = (0, 170, 255)
    LIGHT_BLUE = (180, 230, 255)

str_to_color = {'black': Color.BLACK,
                'white': Color.WHITE,
                'red': Color.RED,
                'blue': Color.BLUE}

color_to_str = {Color.RED: 'red',
                Color.BLUE: 'blue'}

opp_color = {'red': 'blue',
             'blue': 'red'}

DOWN, UP, LEFT, RIGHT, STAY = (0, 1), (0, -1), (-1, 0), (1, 0), (0, 0)
HOLD_DOWN, HOLD_UP, HOLD_LEFT, HOLD_RIGHT = (0, 2), (0, -2), (-2, 0), (2, 0)
RELEASE_DOWN, RELEASE_UP, RELEASE_LEFT, RELEASE_RIGHT = (0, 3), (0, -3), (-3, 0), (3, 0)

ACTIONS = [DOWN, UP, LEFT, RIGHT, STAY]
HOLD_ACTIONS = [HOLD_DOWN, HOLD_UP, HOLD_LEFT, HOLD_RIGHT]
RELEASE_ACTIONS = [RELEASE_DOWN, RELEASE_UP, RELEASE_LEFT, RELEASE_RIGHT]


def bernoulli(p):
    if rand() < p:
        return True
    return False


def get_action_from_location(location_one, location_two):
    return tuple(map(lambda i, j: i - j, location_two, location_one))


def get_location_from_action(gridworld, location, action):
    return gridworld.inbounds([sum(x) for x in zip(location, action)])


def make_gif(image_dir, file_path, one_agent = False):
    import imageio
    images = []
    for f in sorted(os.listdir(image_dir)):
        if 'blank' in f and (not one_agent or int(f[:2]) % 2 == 0):
           images.append(imageio.imread(os.path.join(image_dir, f)))
    # hold first and last frame a little longer
    images = [images[0]]*3 + images
    images += [images[-1]]*3
    imageio.mimsave(file_path + '.gif', images, fps=1.75)


# read in trial information from json
def read_trials(filename):
    return json.load(open('trials/{}/{}.json'.format(filename, filename), 'r'))


# clear directory or create if doesn't exist
def make_dir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        for f in os.listdir(path):
            full_f = os.path.join(path, f)
            if os.path.isfile(full_f):
                os.remove(full_f)
            elif os.path.isdir(full_f):
                shutil.rmtree(full_f)


