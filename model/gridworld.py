from utils import *

import networkx as nx
from scipy.special import softmax


class Rep:
    FLOOR = ' ' # empty square
    START_RED = 'r' # start square
    START_BLUE = 'b'
    GOAL = 'g'  # goal square (*)
    GOAL_ABOVE_WALL = 'G'
    WALL_LEFT = '|'
    WALL_DOWN = '_'
    BOX = 'x'
    BOX_ABOVE_WALL = 'X'

rep_to_name = {
    Rep.FLOOR: 'Floor',
    Rep.START_RED: 'RedStart',
    Rep.START_BLUE: 'BlueStart',
    Rep.GOAL: 'Goal',
    Rep.GOAL_ABOVE_WALL: 'Goal',
    Rep.WALL_LEFT: 'WallLeft',
    Rep.WALL_DOWN: 'WallDown',
    Rep.BOX: 'Box',
    Rep.BOX_ABOVE_WALL: 'Box'
}



# ------------------------------
class GridElement:
    def __init__(self, rep, location):
        self.rep = rep
        self.name = rep_to_name[rep]
        self.location = location
        self.start_location = location
        self.held = False  # technically only boxes can be held

    def __str__(self):
        return '{} at {}'.format(self.name, self.location)


# ------------------------------
class GridWorld():
    def __init__(self, exp, time_limit = 10):
        self.exp = exp
        self.width = 0
        self.height = 0
        self.time_limit = time_limit
        self.objects = []
        self.reachability_graph = nx.Graph()

    def read_world(self, filename):
        x = 0
        y = 0
        with open('grids/experiment{}/{}.txt'.format(self.exp, filename), 'r') as file:
            for line in file:
                line = line.strip('\n')
                for x, rep in enumerate(line):
                    if rep == '.':
                        continue
                    location = (x//2 + 1, y) if rep == '|' else (x//2, y)
                    if rep == 'G' or rep == 'X':
                        self.objects.append(GridElement('_', location))
                    elif rep == '_' or rep == 'x':
                        self.objects.append(GridElement(' ', location))

                    if rep in rep_to_name:
                        newobj = GridElement(rep, location)
                        self.objects.append(newobj)
                y += 1

        self.width = x//2 + 1
        self.height = y
        

    def print(self):
        for o in self.objects:
            print(o)


    def get_gridsquare_at(self, location):
        gridsquares = list(filter(lambda o: o.location == location, self.objects))
        not_floors_or_walls = list(filter(lambda o: (o.name != 'Floor' and o.name != 'WallDown'), gridsquares))
        if len(not_floors_or_walls) > 0:
            return not_floors_or_walls[0]
        if len(gridsquares) > 0:
            return gridsquares[0]
        return None


    def inbounds(self, location):
        x, y = location
        return min(max(x, 0), self.width-1), min(max(y, 0), self.height-1)

    
    def get_all_locations(self):
        return [(x, y) for x in range(self.width) for y in range(self.height)]


    def get_new_location(self, location, action):
        return self.inbounds([sum(x) for x in zip(location, action)])

    
    def get_start_location(self, color):
        if color == Color.RED:
            starts = list(filter(lambda o: o.name == 'RedStart', self.objects))
        elif color == Color.BLUE:
            starts = list(filter(lambda o: o.name == 'BlueStart', self.objects))
        else:
            starts = []
        
        if len(starts) > 0: return starts[0].location
        return (0, 0)
            

    def get_goal_location(self):
        goals = list(filter(lambda o: o.name == 'Goal', self.objects))
        if len(goals) > 0: return goals[0].location
        return None


    def get_boxes(self):
        return list(filter(lambda o: o.name == 'Box', self.objects))


    def move_held_boxes(self, action):
        held_boxes = list(filter(lambda o: o.name == 'Box' and o.held, self.objects))
        for box in held_boxes:
            box.location = tuple(np.add(box.location, action))


    def get_box_at_location(self, location):
        boxes = self.get_boxes()
        for box in boxes:
            if box.location == location:
                return box
        return None


    def get_object_list(self):
        all_obs = []
        for o in self.objects:
            all_obs.append(o)
        return all_obs
        

    def get_divider_left_at(self, location):
        dividers = list(filter(lambda o: o.location == location and
                   o.name == 'WallLeft', self.get_object_list()))
        if len(dividers) > 0:
            return dividers[0]
        return None


    def get_divider_down_at(self, location):
        dividers = list(filter(lambda o: o.location == location and
                  o.name == 'WallDown', self.get_object_list()))
        if len(dividers) > 0:
            return dividers[0]
        return None
    
    
    def avoids_walls(self, location, new_location, action):
        """ Checks if given action avoids walls """

        cur_divider_left, cur_divider_down, new_divider_left, new_divider_down = None, None, None, None
    
        if location[0] != 0:
            cur_divider_left = self.get_divider_left_at(location)
        if location[1] != self.height - 1:
            cur_divider_down = self.get_divider_down_at(location)
            
        if new_location[0] != 0:
            new_divider_left = self.get_divider_left_at(new_location)
        if new_location[1] != self.height - 1:
            new_divider_down = self.get_divider_down_at(new_location)
        
        if ((cur_divider_down and cur_divider_down.name == 'WallDown' and action == DOWN) 
            or (new_divider_down and new_divider_down.name == 'WallDown' and action == UP)):
            return False
            
        if ((cur_divider_left and cur_divider_left.name == 'WallLeft' and action == LEFT) 
            or (new_divider_left and new_divider_left.name == 'WallLeft' and action == RIGHT)):
            return False

        return True
    
    
    def is_valid_action(self, red_location, action, blue_location, moving_box = False, box_location = None, count_boxes = True):
        """ Checks if given action avoids boxes, walls, and stays within the bounds of the grid """

        red_new_location = self.get_new_location(red_location, action)
        if moving_box: box_new_location = self.get_new_location(box_location, action)
        
        if moving_box:
            if (action != STAY 
                and (red_location == red_new_location or red_new_location == box_new_location)):
                return False
            if red_new_location == blue_location or box_new_location == blue_location:
                return False
        else:
            if action != STAY and red_location == red_new_location:
                return False
            if red_new_location == blue_location:
                return False
        
        cur_gridsquare = self.get_gridsquare_at(red_location)
        new_gridsquare = self.get_gridsquare_at(red_new_location)

        if count_boxes:
            if cur_gridsquare and cur_gridsquare.name == 'Box':
                return False
            if new_gridsquare and new_gridsquare.name == 'Box' and not moving_box:
                return False
            
        return self.avoids_walls(red_location, red_new_location, action)


    def make_reachability_graph(self, blue_location = (-1, -1), count_boxes = True):
        self.reachability_graph.clear()

        for red_location in self.get_all_locations():
            self.reachability_graph.add_node(red_location)
            actions = [DOWN, UP, LEFT, RIGHT]
            for action in actions:
                if self.is_valid_action(red_location, action, blue_location, count_boxes = count_boxes):
                    red_new_location = self.get_new_location(red_location, action)
                    if red_new_location in self.reachability_graph:
                        self.reachability_graph.add_edge(red_location, red_new_location)
            

    def get_shortest_path(self, red_location_start, red_location_end, blue_location): 
        self.reachability_graph.clear()

        self.make_reachability_graph(blue_location)
        try:
            return nx.shortest_path(self.reachability_graph, red_location_start, red_location_end)
        except nx.NetworkXNoPath:
            pass
    

    def get_gridsquares_between(self, location_one, location_two):
        self.reachability_graph.clear()

        self.make_reachability_graph(count_boxes = False)
        try:
            return nx.shortest_path_length(self.reachability_graph, location_one, location_two)
        except nx.NetworkXNoPath:
            return 10
            pass
    

    def get_distribution_over_paths(self, red_location_start, red_location_end, blue_location, 
                                    only_shortest_paths = True, count_boxes = True, time_limit = 10):
        """ Finds all possible paths to star and returns probability distribution over them """
        
        self.reachability_graph.clear()
        self.make_reachability_graph(blue_location = blue_location, count_boxes = count_boxes)
        
        try:
            if only_shortest_paths: # only sample shortest paths
                all_shortest_paths = list(nx.all_shortest_paths(
                    self.reachability_graph, red_location_start, red_location_end))
                shortest_path_probs = []

                for path in all_shortest_paths:
                    if len(path) > time_limit + 1: return None, None
                    shortest_path_probs.append(1 / len(all_shortest_paths))
                return all_shortest_paths, shortest_path_probs
            
            # sample red path from softmaxed distribution over all possible paths
            all_paths = list(nx.all_simple_paths(
                self.reachability_graph, red_location_start, 
                red_location_end, cutoff = time_limit + 6))
            all_path_lengths = []
            path_probs = [0 for path in all_paths]

            # favor paths that minimize length as well as directional switches
            for path in all_paths:
                prev_action = path[0]
                num_switches = 0

                for action in path[1:]:
                    if action != prev_action: num_switches += 1
                    prev_action = action

                length_penalty = 11 - len(path)
                direction_penalty = -2 * num_switches
                softmax_beta = 8
                all_path_lengths.append(softmax_beta * (direction_penalty + length_penalty))
                    
            try:
                path_probs = softmax(all_path_lengths)
            except ValueError:
                return None, None

            path_distribution = { tuple(all_paths[i]) : path_probs[i] for i in range(len(all_paths)) }
            return all_paths, path_probs
            
        except nx.NetworkXNoPath:
            return None, None