from gridworld import *
from utils import Color

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
import numpy as np
import random
from datetime import datetime


save_dir = 'screenshots'

_image_library = {}
def get_image(filename):
    global _image_library
    path = '../graphics/{}.png'.format(filename)
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path)
        _image_library[path] = image
    return image


class Game:
    def __init__(self, gridworld, agents = []):
        self._running = True
        self.world = gridworld
        self.agents = agents
        
        self.small_fsize = 18
        self.large_fsize = 28
        self.text_vspacing = 10

        self.scale = 80   # number of pixels per tile
        self.tile_size = (self.scale, self.scale)
        self.agent_r = 25
        self.eye_size = (16, 22)
        self.eye_offsets = [(-16, -18), (1, -18)]
        self.star_width = 60
        self.star_offset = ((self.scale - self.star_width)//2,
                            (self.scale - self.star_width)//2)
        self.sidebar_width = self.scale * 2
        self.wall_width = 7  # odd so it can be centered
        self.handle_width = 10
        self.box_width = self.scale*3//4
        self.start_locations = {}
        self.width = self.scale * self.world.width + self.wall_width
        self.screen_width = self.width + self.sidebar_width
        self.height = self.scale * self.world.height + self.wall_width


    def on_init(self, no_sidebar = False):
        pygame.init()
        self.no_sidebar = no_sidebar
        if self.no_sidebar:
            self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.height))
            self.small_font = pygame.font.SysFont('Arial', self.small_fsize)
            self.large_font = pygame.font.SysFont('Arial', self.large_fsize)
        self._running = True


    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            # press enter to save
            if event.key == pygame.K_RETURN:
                image_name = '{}_{}.png'.format(self.world.name,
                             datetime.now().strftime('%m-%d-%y_%H-%M-%S'))
                self.screenshot('{}/{}'.format(save_dir, image_name))


    def on_render(self, spin = True, time = 0, whose_turn = '', outcome = ''):
        self.draw_gridsquares()
        self.draw_agents()
        if not self.no_sidebar:
            self.draw_timer(time)
            self.draw_turn(whose_turn)
            self.draw_outcome(outcome)
        pygame.display.flip()
        pygame.display.update()


    def draw_gridsquares(self):
        self.screen.fill(Color.WHITE)

        for location in self.world.get_all_locations():
            tl = self.top_left(location)
            fill = pygame.Rect(tl[0], tl[1], self.scale, self.scale)
            self.screen.fill(Color.FLOOR, fill)
            pygame.draw.rect(self.screen, Color.LINE, fill, 1)
            
        for o in self.world.objects:
            tl = self.top_left(o.location)
            fill = pygame.Rect(tl[0], tl[1], self.scale, self.scale)
            if o.name == 'Box':
                box_tl = self.offset_top_left(tl, self.box_width)
                fill_box = pygame.Rect(box_tl[0], box_tl[1],
                                       self.box_width, self.box_width)
                
                # draw handle (exp1)
                if o.held:
                    pygame.draw.line(self.screen, Color.BLUE,
                        start_pos = self.center(o.location),
                        end_pos = self.center(self.agents[1].location),
                        width = self.handle_width)
                    w = self.box_width + self.handle_width
                    border_tl = self.offset_top_left(tl, w)
                    border = pygame.Rect(border_tl[0], border_tl[1], w, w)
                    pygame.draw.rect(self.screen, Color.BLUE, border,
                        width = self.handle_width,
                        border_radius = self.handle_width//3)
                
                # draw handle (exp2)
                if any([a.box == o for a in self.agents]):
                    holder = [a for a in self.agents if a.box == o][0]
                    pygame.draw.line(self.screen, Color.BLUE,
                        start_pos = self.center(o.location),
                        end_pos = self.center(holder.location),
                        width = self.handle_width)
                    w = self.box_width + self.handle_width
                    border_tl = self.offset_top_left(tl, w)
                    border = pygame.Rect(border_tl[0], border_tl[1], w, w)
                    pygame.draw.rect(self.screen, Color.BLUE, border,
                        width = self.handle_width,
                        border_radius = self.handle_width//3)

                self.screen.fill(Color.BOX, fill_box)
            elif o.name == 'BlueStart':
                self.start_locations[Color.BLUE] = o.location
            elif o.name == 'RedStart':
                self.start_locations[Color.RED] = o.location
            elif o.name == 'Goal':
                star = pygame.transform.scale(get_image('goal'),
                        (self.star_width, self.star_width))
                self.screen.blit(star, np.add(tl, self.star_offset))
            elif o.name == 'WallLeft':
                self.draw_wall(start = tl, diff = (0, self.scale))
            elif o.name == 'WallDown':
                self.draw_wall(start = (tl[0], tl[1] + self.scale),
                               diff = (self.scale, 0))

        self.draw_perimeter()
    

    def draw_wall(self, start, diff):
        pygame.draw.line(self.screen, Color.WALL, start_pos = start,
            end_pos = np.add(start, diff), width = self.wall_width)


    def draw_perimeter(self):
        self.draw_wall(self.top_left((0, 0)),
                       (self.scale * self.world.width, 0))
        self.draw_wall(self.top_left((self.world.width, 0)),
                       (0, self.scale * self.world.height))
        self.draw_wall(self.top_left((0, self.world.height)),
                       (self.scale * self.world.width, 0))


    def draw_agents(self):
        for a in self.agents:
            if a is not None: self.draw_agent(a.color, a.location)


    def draw_agent(self, color, location):
        center = self.center(location)
        pygame.draw.circle(self.screen, color, center, self.agent_r)
        pygame.draw.circle(self.screen, Color.WHITE, center, self.agent_r, 2)
        eye = pygame.transform.scale(get_image('eye'), self.eye_size)
        self.screen.blit(eye, np.add(center, self.eye_offsets[0]))   # left eye
        self.screen.blit(eye, np.add(center, self.eye_offsets[1]))   # right eye


    def draw_timer(self, time):
        text_surface = self.small_font.render('time left:', True, Color.BLACK)
        text_w, text_h = text_surface.get_size()
        text_w_margin = (self.sidebar_width - text_w)//2
        self.screen.blit(text_surface, (self.width + text_w_margin,
                                        self.text_vspacing * 4))
        
        surface = self.large_font.render(str(time), True, Color.BLACK)
        w, h = surface.get_size()
        w_margin = (self.sidebar_width - w)//2
        self.screen.blit(surface, (self.width + w_margin,
                                   self.text_vspacing * 5 + text_h))


    def draw_turn(self, whose_turn):
        if whose_turn == '': return
        text_surface = self.small_font.render("{}'s turn".format(whose_turn),
                                              True, str_to_color[whose_turn])
        text_w, text_h = text_surface.get_size()
        text_w_margin = (self.sidebar_width - text_w)//2
        h = self.height//2
        if self.world.height > 4:
            h -= self.text_vspacing * 4
        self.screen.blit(text_surface, (self.width + text_w_margin, h))
        
    
    def draw_outcome(self, outcome):
        text_surface = self.small_font.render('result:', True, Color.BLACK)
        text_w, text_h = text_surface.get_size()
        text_w_margin = (self.sidebar_width - text_w)//2
        self.screen.blit(text_surface, (self.width + text_w_margin,
                                        self.height*2//3))
        if outcome != '':
            surface = self.large_font.render(outcome.upper(), True, Color.BLACK)
            w, h = surface.get_size()
            w_margin = (self.sidebar_width - w)//2
            self.screen.blit(surface, (self.width + w_margin,
                                       self.height*2//3 + self.text_vspacing + text_h))
        

    def save_image(self, file_name):
        pygame.image.save(self.screen, file_name + '.png')


    def screenshot(self, time, file_name, whose_turn = '', outcome = ''):
        self.on_render(time = time, whose_turn = whose_turn, outcome = outcome)
        self.save_image(file_name)
        self.on_render(time = time, outcome = outcome)
        self.save_image(file_name + '_blank')


    def top_left(self, loc):
        tl = (self.scale * loc[0] + self.wall_width//2,
              self.scale * loc[1] + self.wall_width//2)
        return tl

    
    def center(self, loc):
        c = (self.scale * loc[0] + self.wall_width//2 + self.scale//2,
             self.scale * loc[1] + self.wall_width//2 + self.scale//2)
        return c


    def offset_top_left(self, tl, width):
        return (tl[0] + (self.scale - width)//2,
                tl[1] + (self.scale - width)//2)

    def on_cleanup(self):
        pygame.display.quit()
        pygame.quit()


    def on_execute(self, no_sidebar = False):
        if self.on_init(no_sidebar) == False:
            self._running = False

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
        self.on_cleanup()

