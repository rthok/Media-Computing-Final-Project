# -*- coding: utf-8 -*-
'''
Created on 19 jul 2012

@author: Marco Baxemyr
'''
from math import sqrt
import os
import datetime
import types

import pygame
from pygame.locals import *
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer


def load_image(file_name, convert_alpha=True, colorkey=False):
    """inspired by http://www.linuxjournal.com/article/7694"""
    full_name = os.path.join('images', file_name)
    
    try:
        image = pygame.image.load(full_name)
    except (pygame.error, message):
        print("Couldn't load image:", full_name)
        raise (SystemExit, message)
    
    if convert_alpha:
        image = image.convert_alpha()
    else:
        image = image.convert()
    
    if colorkey:
        colorkey = image.get_at((0,7))
        image.set_colorkey(colorkey, RLEACCEL)
    
    return image

def load_sound(file_name):
    """inspired by http://www.linuxjournal.com/article/7694"""
    class No_Sound:
        def play(self):
            pass
        def set_volume(self, volume):
            pass
    
    if not mixer:
        return No_Sound()
    
    full_name = os.path.join('audio', file_name)
    if os.path.exists(full_name):
        sound = mixer.Sound(full_name)
        return sound
    else:
        print('File not found', full_name)
        return No_Sound()

def load_font(file_name, font_size):
    full_name = os.path.join('fonts', file_name)
    if os.path.exists(full_name):
        return pygame.font.Font(full_name, font_size)

def get_Percentage(Max, Value):
    fraction = float(Value) / Max
    return fraction
def get_Distance(v1, v2):
    x = v1[0] - v2[0]
    y = v1[1] - v2[1]
    return sqrt(x**2 + y**2)

class Timer(object):
    """ A Timer that can periodically call a given callback
        function.

        After creation, you should call update() with the
        amount of time passed since the last call to update()
        in milliseconds.

        The callback calls will result synchronously during these
        calls to update()
    """
    def __init__(self, interval, callback, oneshot=False):
        """ Create a new Timer.

            interval: The timer interval in milliseconds
            callback: Callable, to call when each interval expires
            oneshot: True for a timer that only acts once
        """
        self.interval = interval
        self.callback = callback
        self.oneshot = oneshot
        self.time = 0
        self.alive = True

    def update(self, time_passed):
        if not self.alive:
            return

        self.time += time_passed
        if self.time > self.interval:
            self.time -= self.interval
            self.callback()

            if self.oneshot:
                self.alive = False


def is_instance_method(obj):
    """Checks if an object is a bound method on an instance."""
    if not isinstance(obj, types.MethodType):
        return False # Not a method
    if obj.im_self is None:
        return False # Method is not bound
    if issubclass(obj.im_class, type) or obj.im_class is types.ClassType:
        return False # Method is a classmethod
    return True
