# -*- coding: utf-8 -*-
'''
Created on 14 July 2012

@author: Marco Baxemyr
'''

import random
from copy import deepcopy

from pygame import sprite
from pygame import Rect

from ResourceManager import *
from ResourceCapsule import *
from utils import *

class Block(sprite.Sprite):
    def __init__(self, position, health, create_powerup_method_getter, resource_manager, invulnerable=False, invisible=False):
        sprite.Sprite.__init__(self)
        self.images = [ResourceCapsule(resource_manager, "block_lightblue.png"), ResourceCapsule(resource_manager, "block_babyblue.png"), ResourceCapsule(resource_manager, "block_blue.png"), ResourceCapsule(resource_manager, "block_pink.png"), ResourceCapsule(resource_manager, "block_purple.png"), ResourceCapsule(resource_manager, "block_orange.png"), ResourceCapsule(resource_manager, "block_red.png"), ResourceCapsule(resource_manager, "block_lightgreen.png"), ResourceCapsule(resource_manager, "block_green.png"), ResourceCapsule(resource_manager, "block_yellow.png")]
        self.invulnerable_image_getter = ResourceCapsule(resource_manager, "block_invulnerable.png")
        self.invisible_image_getter = ResourceCapsule(resource_manager, "shatter_0")
        self.orig_health = health
        self.health = health
        self.invulnerable = invulnerable
        self.invisible = invisible
        self.resource_manager = resource_manager
        self.shatter_image_getter = ResourceCapsule(resource_manager, "shatter_0")
        self.select_image()
        self.rect = Rect((position[0], position[1]), (self.image_getter().get_width(), self.image_getter().get_height()))
        self.create_powerup_getter = create_powerup_method_getter
        
    def __getstate__(self):
        return dict((k, v) for k, v in self.__dict__.iteritems()
                           if not is_instance_method(getattr(self, k)))    
    
    def damage(self, damage=1):
        self.invisible = False
        score_for_hit = self.calculate_score_for_hit(damage)
        if not self.invulnerable:
            self.health -= damage
            if self.health <= 0:
                if self.powerup_dropped():
                    self.create_powerup_getter()(self.rect.center) #actually located in game.py
                self.kill() 
            else:
                self.select_image()
        else:
            self.select_image()
        return score_for_hit
    
    def calculate_score_for_hit(self, damage):
        score = 0
        if self.invulnerable:
            return score
        for i in range(damage):
            score += max((self.health - i)* 5, 0)
        return score
    
    def powerup_dropped(self):
        """Whether or not a powerup drop occurs"""
        return self.health == random.randint(0, 10)
    
    def select_image(self):
        if self.invisible:
            self.image_getter = self.invisible_image_getter
        elif self.invulnerable:
            self.image_getter = self.invulnerable_image_getter
        else:
            if self.health <= len(self.images):
                self.image_getter = self.images[self.orig_health - 1]
            else:
                self.image_getter = self.images[-1]
        self.shatter_image_getter = ResourceCapsule(self.resource_manager, "shatter_"+str(int(140 - (float(self.health) / self.orig_health) * 140)))
    
    def set_invulnerable(self):
        self.invulnerable = True
        self.select_image()
    
    def undo_invulnerable(self):
        self.invulnerable = False
        self.select_image()
        
