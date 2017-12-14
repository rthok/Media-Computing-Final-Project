# -*- coding: utf-8 -*-
'''
Created on 14 July 2012

@author: Marco Baxemyr
'''
import math

from pygame import sprite
from pygame import Rect
from vector import Vector
from ball import *

from utils import *
from constants import *

class Powerup(sprite.Sprite):

    
    def __init__(self, image_getter, position):
        sprite.Sprite.__init__(self)
        self.name = "Powerup"
        self.image_getter = image_getter
        self.radius = (self.image_getter().get_width() / 2) - 1
        self.speed = 360.
        self.rect = Rect(0, 0, self.image_getter().get_width(), self.image_getter().get_height())
        self.move(Vector(position[0], position[1]))
        self.direction = Vector(0,1).get_normalized()
        self.has_passed_paddle=False
        
    def update(self, time_passed, paddle):
        """
        Moves the powerup downward and checks for collision with paddle or bottom of game area
        time_passed: the time passed in seconds since last call
        paddle: the paddle sprite
        """
        
        displacement = Vector(self.direction.get_x() * self.speed * time_passed,
                              self.direction.get_y() * self.speed * time_passed)
        new_pos = self.pos+displacement
        old_pos = self.pos
        
        self.keep_within_bounds(new_pos, old_pos, time_passed)
        
        self.check_and_handle_paddle_collision(paddle, new_pos, old_pos, time_passed)

        self.move(new_pos)
    
    def move(self, position):
        self.pos = position
        self.rect.center = (position.get_x(), position.get_y())
    
    def keep_within_bounds(self, new_pos, old_pos, time_passed):
        if new_pos.get_x() - self.radius < LEFT_BOUND:
            self.direction = Vector(abs(self.direction.get_x()), self.direction.get_y())
            displacement = Vector(self.direction.get_x() * self.speed * time_passed,
                              self.direction.get_y() * self.speed * time_passed)
            new_pos = old_pos+displacement
        elif new_pos.get_x() + self.radius > RIGHT_BOUND:
            self.direction = Vector(-abs(self.direction.get_x()), self.direction.get_y())
            displacement = Vector(self.direction.get_x() * self.speed * time_passed,
                              self.direction.get_y() * self.speed * time_passed)
            new_pos = old_pos+displacement
        elif new_pos.get_y() - self.radius < 0:
            self.direction = Vector(self.direction.get_x(), abs(self.direction.get_y()))
            displacement = Vector(self.direction.get_x() * self.speed * time_passed,
                              self.direction.get_y() * self.speed * time_passed)
            new_pos = old_pos+displacement
        elif new_pos.get_y() - self.radius > SCREEN_HEIGHT:
            self.kill()
    
    def check_and_handle_paddle_collision(self, paddle, new_pos, old_pos, time_passed):
        if new_pos.get_y() + self.radius >= PADDLE_HEIGHT_POS and (new_pos.get_x() + self.radius > paddle.rect.left and new_pos.get_x() - self.radius < paddle.rect.right) and not self.has_passed_paddle:
            self.activate()
        if new_pos.get_y() >= paddle.rect.bottom - (paddle.rect.height / 2.5):
            self.has_passed_paddle = True
    
    def activate(self):
        print ("Powerup activated!")
        self.kill()

    def __getstate__(self):
        return dict((k, v) for k, v in self.__dict__.iteritems()
                           if not is_instance_method(getattr(self, k))) 


class ExtraBall(Powerup):
    
    def __init__(self, image_surface, position, addBall_getter):
        super(ExtraBall, self).__init__(image_surface, position)
        self.name = "Extra Ball"
        self.addBall_getter = addBall_getter
    
    def activate(self):
        self.addBall_getter()(release_instantly=True)
        self.kill()

class ExtraLife(Powerup):
    
    def __init__(self, image_surface, position, addLife_getter):
        super(ExtraLife, self).__init__(image_surface, position)
        self.name = "Extra Life"
        self.addLife_getter = addLife_getter
    
    def activate(self):
        self.addLife_getter()()
        self.kill()

class ExtraPoint(Powerup):
    
    def __init__(self, image_surface, position, addExtrapoint_getter):
        super(ExtraPoint, self).__init__(image_surface, position)
        self.name = "Extra Point"
        self.addExtrapoint_getter = addExtrapoint_getter
    
    def activate(self):
        self.addExtrapoint_getter()()
        self.kill()
        
class TimeDistortionField(Powerup):
    
    def __init__(self, image_surface, position, time_distortion_field_getter):
        super(TimeDistortionField, self).__init__(image_surface, position)
        self.name = "Time Distortion Field"
        self.time_distortion_field_getter = time_distortion_field_getter
        
    
    def activate(self):
        self.time_distortion_field_getter()(8000)
        self.kill()

        
class DoubleDamage(Powerup):
    
    def __init__(self, image_surface, position, double_damage_getter):
        super(DoubleDamage, self).__init__(image_surface, position)
        self.name = "Double Damage"
        self.double_damage_getter = double_damage_getter
    
    def activate(self):
        self.double_damage_getter()()
        self.kill()
