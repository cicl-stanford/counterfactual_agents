from utils import Color, color_to_str

class Agent:
    def __init__(self, 
            color, location, level = None, intention = None, path = [], prob_stall = 0.1):
        self.color = color   # Color.RED or Color.BLUE
        self.name = color_to_str[self.color] + " player"
        self.start_location = location
        self.location = location
        self.level = level
        self.intention = intention
        self.path = path
        self.prob_stall = prob_stall
        self.box = None
        self.holding_box = False
        self.planner = None

    def print_status(self):
        print("\t{} is currently at {}".format(self.name, self.location))
        print("\tpath:", self.path)
	
    def move_to(self, new_location, box_new_location = None):
        self.location = new_location
        if box_new_location:
            self.box.location = box_new_location

    def hold_box(self, box):
        self.box = box
        self.holding_box = True

    def release_box(self, box):
        self.box = None
        self.holding_box = False
