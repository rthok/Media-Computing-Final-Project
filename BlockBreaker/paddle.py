# -*- coding: utf-8 -*-
'''
Created on 14 July 2012

@author: Marco Baxemyr
'''

from pygame import sprite
from pygame import Rect
from constants import *
from utils import *

class Paddle(sprite.Sprite):

    def __init__(self, image_getter, position):
        sprite.Sprite.__init__(self)
        self.image_getter = image_getter
        self.rect = Rect((position[0], position[1]), (self.image_getter().get_width(), self.image_getter().get_height()))
        
        
    def update(self, posX, moveToPos=False):
        image_width_halved = self.image_getter().get_width() / 2
        x = self.rect.centerx
        if moveToPos:
            if posX != 0:
                x = max(LEFT_BOUND+image_width_halved, posX)
        else:
            x = max(LEFT_BOUND+image_width_halved, x + posX)
        x = min(RIGHT_BOUND-image_width_halved, x)
        self.rect.centerx = x

    def __getstate__(self):
        return dict((k, v) for k, v in self.__dict__.iteritems()
                           if not is_instance_method(getattr(self, k))) 