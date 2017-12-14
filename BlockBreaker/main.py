# -*- coding: utf-8 -*-
'''
Created on 14 July 2012

@author: Marco Baxemyr
'''

import sys
import datetime
import operator
import random
import math
import pickle
from collections import defaultdict

import pygame
from pygame.locals import *
try:
    import android
except ImportError:
    android = None
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer

from ball import *
from block import Block
from paddle import Paddle
from vector import Vector
from powerups import *
from ResourceManager import *
from ResourceCapsule import *
from utils import *
import widgets
from constants import *

class Game(object):
    MUSIC = 'coherence.ogg'
    WAIT_NEW_LEVEL = USEREVENT+5
    TIME_DISTORTION_FIELD = USEREVENT+6
    ORANGE = (230, 40, 0)
    
    def __init__(self, screen):
        random.seed()
        self.resource_manager = ResourceManager(self)
        self.resource_manager['surface_screen'] = screen
        self.screen_getter = ResourceCapsule(self.resource_manager, "surface_screen")        
        self.clock_getter = ResourceCapsule(self.resource_manager, "clock_0")
        self.background_getter = ResourceCapsule(self.resource_manager, 'image_background-hd2.png')
        self.heart_getter = ResourceCapsule(self.resource_manager, 'image_heart.png')
        self.ball_image_getter = ResourceCapsule(self.resource_manager, "image_ball.png")
        self.extraball_image_getter = ResourceCapsule(self.resource_manager, 'image_extraball_powerup.png')
        self.extralife_image_getter = ResourceCapsule(self.resource_manager, 'image_extralife_powerup.png')
        self.extrapoint_image_getter = ResourceCapsule(self.resource_manager, 'image_extrapoint_powerup.png')
        self.double_damage_image_getter = ResourceCapsule(self.resource_manager, 'image_double_damage_powerup.png')
        self.time_distortion_powerup_image_getter = ResourceCapsule(self.resource_manager, 'image_time_distortion_field_powerup.png')
        self.time_distortion_field_image_getter = ResourceCapsule(self.resource_manager, 'image_time_distortion_field.png')
        self.paddles = pygame.sprite.RenderUpdates()
        self.paddle = Paddle(ResourceCapsule(self.resource_manager, "image_paddle.png"), (390, PADDLE_HEIGHT_POS))
        self.paddles.add(self.paddle)
        self.balls = pygame.sprite.RenderUpdates()
        self.powerups = pygame.sprite.RenderUpdates()
        self.blocks = pygame.sprite.RenderUpdates()
        self.invulnerable_blocks = pygame.sprite.RenderUpdates()
        
        self.balls_on_paddle = 0
        self.time_distortion_field_active = False
        self.time_passed_this_level = 0

        self.lives = 3
        self.livesfont_getter = ResourceCapsule(self.resource_manager, "font_audiowide.ttf/28")
        self.lives_surface_getter = ResourceCapsule(self.resource_manager, "livesfont_  " + str(self.lives))
        self.game_over = False
        
        self.score = 0
        self.combo = 0
        self.combo_hits = 0
        
        self.scorefont_getter = ResourceCapsule(self.resource_manager, "font_audiowide.ttf/17")
        self.scorelabelfont_getter = ResourceCapsule(self.resource_manager, "font_audiowide.ttf/17")
        self.score_label_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_Score Board:")
        
        self.combo_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_"+str(self.combo))
        self.combo_hits_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_"+str(self.combo_hits)+" Hits Bouns)")
        self.score_combo_plus_sign_surface_getter = ResourceCapsule(self.resource_manager, "comboplussign_+")        
        self.score_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_"+str(self.score))
        
        self.touching = False
        self.lowest_fps = 10000
        
        self.text_messages = []
        
        self.detect_levels()
        self.load_level(1)
        self.waiting_for_level = False
        
        self.loading_init()
    
    def loading_init(self):
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True) #required to capture mouse input outside of the window
        self.background_getter().blit(self.heart_getter(), (30,0))
        self.background_getter().blit(self.score_label_surface_getter(), (45, 60))
        self.screen_getter().blit(self.background_getter(), (0,0))
        pygame.display.update()

    def detect_levels(self):
        self.available_levels = 0
        while True:
            if os.path.isfile(os.path.join('levels', str(self.available_levels+1) + ".lvl")):
                self.available_levels += 1
            else:
                break
        
    def load_level(self, level):
        self.time_passed_this_level = 0
        b = len(self.balls)
        if b > 0:
            remaining_balls = b
        else:
            remaining_balls = 1
        self.balls.empty()
        self.powerups.empty()
        self.blocks.empty()
        self.invulnerable_blocks.empty()
        self.balls_on_paddle = 0
        for ball in range(remaining_balls):
            self.add_ball()
        if android:
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Touch to begin level " + str(level), Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=2800, size=24, initialdelay=1200))
        else:
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Press SPACE to begin level " + str(level), Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=2800, size=24, initialdelay=1200))
        if level <= self.available_levels:
            self.level = level
            level_data = open(os.path.join('levels', str(level)+".lvl"), 'r')
            i = 0
            for row in level_data:
                row = row.split()
                for j in range(25):
                    if self.is_int(row[j]):
                        if int(row[j]) != 0:
                            self.blocks.add(Block((LEFT_BOUND+BLOCK_SIZE[0]*j,BLOCK_SIZE[1]*i),abs(int(row[j])), ResourceCapsule(self.resource_manager, "fn_create_powerup"), self.resource_manager, invisible=int(row[j]) < 0))
                    elif row[j] == "*" or row[j] == "-*": #invulnerable block!
                        self.invulnerable_blocks.add(Block((LEFT_BOUND+BLOCK_SIZE[0]*j,BLOCK_SIZE[1]*i),1, ResourceCapsule(self.resource_manager, "fn_create_powerup"), self.resource_manager, invulnerable=True, invisible=row[j][0] == "-"))
                i += 1
            level_data.close()
        else:
            self.load_level(level-1)

    def is_int(self, txt):
        try:
            int(txt)
            return True
        except ValueError:
            return False
            
    def run(self):
        self.play_music()
        self.total_time_passed = 0
        fps_limit = 60
        if android:
            fps_limit = 40
        while True: #main game loop
            if android:
                if android.check_pause():
                    self.pause()
                    #self.pause_music()
                    self.save()
                    print ("Block Breaker progress saved!")
                    self.stop_music()
                    android.wait_for_resume()
                    self.pause(resume=True)
                    self.play_music()
                    #self.pause_music(resume=True)
            time_passed = self.clock_getter().tick(fps_limit) / 1000.0
            # If too long has passed between two frames, lie and tell the game it's still at more than 21 FPS (0.046 seconds since last frame)
            # (either the game must have suspended for some reason, in which case we don't want it to "jump forward" suddenly -
            # or the game is running on too weak hardware (single core < 1GHz android phones for example), in which case we'd rather have the game be slow than messing up collision detection)
            if time_passed > 0.046:
                time_passed = 0.046
                #continue
            self.total_time_passed += time_passed
            input = self.process_input()
            
            self.update(time_passed, input, moveToPos = android)
            
            self.draw()
    
    def release_a_ball(self):
        rightmost_ball = None
        for ball in self.balls:
            if ball.attached_to_paddle:
                if rightmost_ball:
                    if rightmost_ball.attach_pos < ball.attach_pos:
                        rightmost_ball = ball
                else:
                    rightmost_ball = ball
        if rightmost_ball:
            rightmost_ball.release_from_paddle()
            self.balls_on_paddle -= 1

    def process_input(self):
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_SPACE:
                        self.release_a_ball()
                    elif event.key == pygame.K_a:
                        if DEBUGGING:
                            self.load_level(self.level+1)
                    elif event.key == pygame.K_f:
                        if DEBUGGING:
                            self.create_powerup((480,0))
                    elif event.key == pygame.K_y and self.game_over:
                        if android:
                            android.hide_keyboard()
                        self.restart()
                    elif event.key == pygame.K_n and self.game_over:
                        if android:
                            android.hide_keyboard()
                        self.force_quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.touching = True
                    if not android:
                        self.release_a_ball()
                elif event.type == pygame.MOUSEBUTTONUP:
                    if android:
                        self.release_a_ball()
                    self.touching = False
                elif event.type == self.WAIT_NEW_LEVEL:
                    self.waiting_for_level = False
                    self.powerups.empty()
                    self.load_level(self.level+1)
                    pygame.time.set_timer(self.WAIT_NEW_LEVEL, 0)
                elif event.type == self.TIME_DISTORTION_FIELD:
                    self.disable_time_distortion_field()
        if android:
            if self.touching:
                return pygame.mouse.get_pos()[0]
            else:
                return 0
        return pygame.mouse.get_rel()[0]
    
    def update(self, time_passed, input, moveToPos=False):
        self.time_passed_this_level += time_passed
        self.balls.update(time_passed, self.paddle, self.balls, self.blocks, self.invulnerable_blocks)
        self.powerups.update(time_passed, self.paddle)
        for paddle in self.paddles:
            paddle.update(input, moveToPos=moveToPos)
        
        for text_message in self.text_messages:
            text_message.update(time_passed * 1000) #convert to ms
        
        if len(self.blocks) == 0 and not self.waiting_for_level and not self.game_over:
            self.level_complete()
        if len(self.balls) == 0 and not self.game_over and not self.waiting_for_level:
            self.dropped_balls()
        
        self.update_score()
        if DEBUGGING:
            fps = self.clock_getter().get_fps()
            if fps > 0:
                self.lowest_fps = min(fps, self.lowest_fps)
            if android:
                print ("fps: " + str(fps) + "   Lowest fps: " + str(self.lowest_fps))
            else:
                pygame.display.set_caption(TITLE + "   %.0f fps" % fps + ", lowest: %0.f fps" % self.lowest_fps)
        
    def play_music(self):
        music_file_name = os.path.join('audio', self.MUSIC)
        if not mixer:
            print("mixer not enabled! Skipping music.")
            return
        elif not os.path.exists(music_file_name):
            print("Music file not found: "), music_file_name
            return
        
        mixer.music.load(music_file_name)
        mixer.music.set_volume(0.8)
        mixer.music.play(-1)

    def stop_music(self):
        mixer.music.stop()
    
    def pause_music(self, resume=False):
        if not resume:
            mixer.music.pause()
        else:
            mixer.music.unpause()

    def erase_rect(self, surface, rect):
        surface.blit(self.background_getter(), rect, rect)

    def draw(self, update=True):
        self.screen_getter().blit(self.background_getter(), (0,0))
        for ball in self.balls:
            self.screen_getter().blit(ball.image_getter(), ball.rect);
        if self.game_over:
            self.screen_getter().blit(self.lives_surface_getter(), (10, 10))
        else:
            self.screen_getter().blit(self.lives_surface_getter(), (66, 10))
        self.screen_getter().blit(self.combo_surface_getter(), (58 - self.combo_surface_getter().get_width() // 10, 92))
        self.screen_getter().blit(self.combo_hits_surface_getter(), (58 - self.combo_hits_surface_getter().get_width() // 10, 122))
        self.screen_getter().blit(self.score_surface_getter(), (58 - self.score_surface_getter().get_width() // 10, 152))
        for block in self.blocks:
            self.screen_getter().blit(block.image_getter(), block.rect)
            if block.health < block.orig_health:
                self.screen_getter().blit(block.shatter_image_getter(), block.rect)
        for block in self.invulnerable_blocks:
            self.screen_getter().blit(block.image_getter(), block.rect)
        for powerup in self.powerups:
            self.screen_getter().blit(powerup.image_getter(), powerup.rect)
        for paddle in self.paddles:
            self.screen_getter().blit(paddle.image_getter(), paddle.rect)
        if self.time_distortion_field_active:
            self.screen_getter().blit(self.time_distortion_field_image_getter(), (232,520))
        
        
        for text_message in self.text_messages:
            if not text_message.timealive > text_message.duration or text_message.duration == 0:
                text_message.draw()
            else:
                self.text_messages.remove(text_message)
        if update:
            pygame.display.update()
    
    def clear(self, surface, rectlist, background):
        for rect in rectlist:
            surface.blit(background, rect, rect)
        
    def update_score(self):
        highest_combo = 0
        combo_length = 0 
        for ball in self.balls:
            if ball.score != 0:
                self.erase_rect(self.screen_getter(), Rect((730, 83, self.scorefont_getter().size(str(self.score))[0], self.scorefont_getter().size(str(self.score))[1])))
                self.score += ball.score
                ball.score = 0
            if ball.combo_length > 0:
                if ball.combo > highest_combo:
                    highest_combo = ball.combo
                    combo_length = ball.combo_length
        self.erase_rect(self.screen_getter(), Rect((730, 120, self.scorefont_getter().size(str(self.combo))[0], self.scorefont_getter().size(str(self.combo))[1])))
        self.combo = highest_combo
        self.combo_hits = combo_length

        self.combo_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_Points: "+str(self.combo))
        self.combo_hits_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_"+str(self.combo_hits)+" Hits XP")
        self.score_surface_getter = ResourceCapsule(self.resource_manager, "scorefont_Total: "+str(self.score))
    
    def collect_all_score(self):
        for ball in self.balls:
                self.score += ball.combo
    
    def create_powerup(self, pos):
        available_powerups = [ExtraLife(self.extralife_image_getter, pos, ResourceCapsule(self.resource_manager, "fn_add_life")),
                              ExtraPoint(self.extrapoint_image_getter, pos, ResourceCapsule(self.resource_manager, "fn_add_extrapoint")),
                              ExtraBall(self.extraball_image_getter, pos, ResourceCapsule(self.resource_manager, "fn_add_ball")),
                              TimeDistortionField(self.time_distortion_powerup_image_getter, pos, ResourceCapsule(self.resource_manager, "fn_activate_time_distortion_field")),
                              DoubleDamage(self.double_damage_image_getter, pos, ResourceCapsule(self.resource_manager, "fn_double_damage"))]
        chosen_powerup = random.choice(available_powerups)
        
        self.powerups.add(chosen_powerup)
        self.text_messages.append(widgets.TextMessage(self.screen_getter(), chosen_powerup.name + " spawned!", Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=1200, size=32, initialdelay=1100))

    def add_ball(self, release_instantly=False):
        ball = Ball(self.ball_image_getter, (230+82, 625), Vector(-3,-5), ResourceCapsule(self.resource_manager, "fn_is_time_distortion_field_active"), self.resource_manager, attached=True, attach_pos=self.balls_on_paddle)
        self.balls.add(ball)
        self.balls_on_paddle += 1
        if release_instantly:
            ball.update(1, self.paddle, self.balls, self.blocks, self.invulnerable_blocks)
            self.release_a_ball()

    def add_life(self):
        if(self.lives < 5):
            self.lives += 1
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Extra Life Added!",
                                                      Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2),
                                                      duration=1800, size=32,
                                                      initialdelay=800))
            self.lives_surface_getter = ResourceCapsule(self.resource_manager, "livesfont_" + str(self.lives))
        else:
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Max Lives Allowed!",
                                                      Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2),
                                                      duration=1800, size=32,initialdelay=800))
    
    def activate_time_distortion_field(self, duration):
        pygame.time.set_timer(self.TIME_DISTORTION_FIELD, 0)
        self.time_distortion_field_active = True
        pygame.time.set_timer(self.TIME_DISTORTION_FIELD, duration)

    def disable_time_distortion_field(self):
        self.time_distortion_field_active = False
        pygame.time.set_timer(self.TIME_DISTORTION_FIELD, 0)
        
    def is_time_distortion_field_active(self):
        return self.time_distortion_field_active
    
    def add_extrapoint(self):
        for ball in self.balls:
            ball.combo += 100
        self.text_messages.append(widgets.TextMessage(self.screen_getter(), "You got 100 XP!",
                                                      Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2),
                                                      duration=1800, size=32,initialdelay=800))
                           
    def double_damage(self):
        for ball in self.balls:
            ball.damage = 2
            ball.image_getter = ResourceCapsule(self.resource_manager, "image_large_ball.png")
    
    def level_complete(self):
        self.waiting_for_level = True
        self.collect_all_score()
        if self.level < self.available_levels:
            pygame.time.set_timer(self.WAIT_NEW_LEVEL, 1800)
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Level Complete!", Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=1800, size=32, initialdelay=800))
        else:
            if android:
                self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Congratulations! You beat all " + str(self.available_levels) + " levels. Play again? Y/n", Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2 - 120), duration=9999999, size=24, initialdelay=9999990))
                android.show_keyboard()
            else:
                self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Congratulations! You beat all " + str(self.available_levels) + " levels. Play again? Y/n", Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=9999999, size=24, initialdelay=9999990))
            self.add_to_highscore()
            self.game_over = True
    
    def dropped_balls(self):
        self.erase_rect(self.screen_getter(), Rect((168, 88, self.livesfont_getter().size(str(self.lives))[0], self.livesfont_getter().size(str(self.lives))[1])))
        self.lives -= 1
        if self.lives > 0:
            self.add_ball()
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "Press SPACE to begin",
                                                          Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=1800, size=32, initialdelay=800))
        else:
            self.lost()
        self.lives_surface_getter = ResourceCapsule(self.resource_manager, "livesfont_" + str(self.lives))
    
    def lost(self):
        self.game_over = True
        self.lives = "      NO LIVES"
        if android:
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "           Play again? Y/n", Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2 - 120), duration=9999999, size=32, initialdelay=9999990))
            android.show_keyboard()
        else:
            self.text_messages.append(widgets.TextMessage(self.screen_getter(), "           Play again? Y/n", Vector(self.screen_getter().get_width() / 2, self.screen_getter().get_height() / 2), duration=9999999, size=32, initialdelay=9999990))
        self.add_to_highscore()

    def add_to_highscore(self):
        if not os.path.exists('playername.txt'):
            playername_file = open('playername.txt', 'w')
            playername_file.write("Player")
            playername_file.close()
        playername_file = open('playername.txt', 'r')
        playername = playername_file.readline()
        playername.rstrip()
        playername_file.close()
        
        now = datetime.datetime.now()
        
        highscore = open('highscores.txt', 'a')
        highscore.write(str(now.year)+"-" + str(now.month) + "-" + str(now.day) + " " + str(now.hour).zfill(2) + ":" +  str(now.minute) + " " + str(playername) + " scored " + str(self.score) + "\n")
        highscore.close()
    
    def pause(self, resume=False):
        if not resume:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            
        else:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            self.clock_getter().tick() #Tick the clock to discard the passed time

    def restart(self):
        screen = self.screen_getter()
        del self
        game = Game(screen)
        game.run()

    def save(self, fileName=SAVE_FILE_NAME):
        if not self.game_over:
            self.resource_manager.clear()
            self.text_messages = []
            shouldRemoveSaveFile = False
            try:
                saveFile = open(fileName, 'wb')
                try:
                    pickle.dump(self, saveFile, 2);
                except (TypeError):
                    shouldRemoveSaveFile = True
                    print ("Couldn't save: ") + str(e)
                finally:
                    saveFile.close()
            except (IOError):
                 print (str(e))
            if shouldRemoveSaveFile:
                os.remove(fileName)
        

    def quit(self):
        self.pause()
        if widgets.UserConfirm(self.screen_getter, self.resource_manager, message="Return to Main Menu? (Your progress will be saved)", backgroundclass=self):
            self.add_to_highscore()
            self.force_quit()
        self.screen_getter().blit(self.background_getter(), (0,0))
        pygame.display.update()
        self.pause(resume=True)
    
    def force_quit(self):
        self.save()
        self.pause() #Restores mouse state
        self.stop_music()
        del self
        menu = Menu(get_screen())
    
    def __getstate__(self):
        return dict((k, v) for k, v in self.__dict__.iteritems()
                           if not is_instance_method(getattr(self, k))) 

class Menu(object):
    """Adapted from PyTowerDefense (http://sourceforge.net/projects/pytowerdefense/), an earlier project of mine"""
    BG_IMG = 'background.png'
    NEW_GAME_CLICK = pygame.locals.USEREVENT + 1
    RESUME_CLICK = pygame.locals.USEREVENT + 2
    HELP_CLICK = pygame.locals.USEREVENT + 3
    HIGHSCORES_CLICK = pygame.locals.USEREVENT + 4
    EXIT_CLICK = pygame.locals.USEREVENT + 5
    BACK_CLICK = pygame.locals.USEREVENT + 6
    ORANGE = (130, 40, 0)
    WHITE = (192, 192, 192) #(210, 210, 210)
    def __init__(self, screen, game=None):
        self.bg_img = load_image(self.BG_IMG)
        self.screen = screen
        self.game = game
        self.titlefont = load_font('audiowide.ttf', 56)
        self.title = self.titlefont.render(TITLE, True, self.WHITE)
        # Text Widget lists
        self.main_text_widgets = []
        self.help_text_widgets = []
        self.highscore_text_widgets = []
        self.main()

    def draw_bg(self, rect=None):
        if not rect:
            self.screen.blit(self.bg_img, (0,0))
            self.screen.blit(self.title, (self.screen.get_rect().centerx - self.titlefont.size(TITLE)[0] / 2, self.screen.get_rect().centery - (self.titlefont.size(TITLE)[1] / 2) - 180))
        else:
            self.screen.blit(self.bg_img, rect, rect)
    
    def main(self):
        self.state = "Main"
        self.draw_bg()
        
        

        offset = 0
        newTitle = "New Game"
        if saveFileNotCorrupt():
            offset = 75
            newTitle = "New Game(saved game will be lost)"
            self.resume_text = widgets.TextWidget("Continue", colour=self.WHITE, size=44, highlight_increase=3, event=self.RESUME_CLICK, font_filename='audiowide.ttf', bold=False)
            self.resume_text.rect.center = self.screen.get_rect().center
            self.resume_text.rect.top += 20
            self.main_text_widgets.append(self.resume_text)

        self.new_game_text = widgets.TextWidget(newTitle, colour=self.WHITE, size=44, highlight_increase=3, event=self.NEW_GAME_CLICK, font_filename='audiowide.ttf', bold=False)
        self.new_game_text.rect.center = self.screen.get_rect().center
        self.new_game_text.rect.top -= 55
        self.main_text_widgets.append(self.new_game_text)


        self.help_text = widgets.TextWidget("Help", colour=self.WHITE, size=44, highlight_increase=3, event=self.HELP_CLICK, font_filename='audiowide.ttf', bold=False)
        self.help_text.rect.center = self.screen.get_rect().center
        self.help_text.rect.top += 20 + offset
        self.main_text_widgets.append(self.help_text)

        self.help_text = widgets.TextWidget("Highscores", colour=self.WHITE, size=44, highlight_increase=3, event=self.HIGHSCORES_CLICK, font_filename='audiowide.ttf', bold=False)
        self.help_text.rect.center = self.screen.get_rect().center
        self.help_text.rect.top += 95 + offset
        self.main_text_widgets.append(self.help_text)

        self.exit_text = widgets.TextWidget("Exit Game", colour=self.WHITE, size=44, highlight_increase=3, event=self.EXIT_CLICK, font_filename='audiowide.ttf', bold=False)
        self.exit_text.rect.center = self.screen.get_rect().center
        self.exit_text.rect.top += 170 + offset
        self.main_text_widgets.append(self.exit_text)
        self.loop()

    def help(self):
        self.state = "Help"
        helpstring = "Press SPACE (or left click) to put the ball into motion.\n\nMove the paddle with your right and left arrow to keep the ball in play!\n\nThe ball will go left if it hits the left side of the paddle, and so on.\n\nEliminate all blocks to advance to the next level.\n\nEarn more score through combo-streaks, that is, hit as many bricks as possible without touching the paddle.\n\nWhite blocks are indestructible\n\nYou can pause and resume with ESC"
        menufont = load_font('audiowide.ttf', 21)
        menurect = Rect(270,35,810,630)
        self.draw_bg(self.screen.get_rect())
        textsurface = widgets.render_textrect(helpstring, menufont, menurect, self.WHITE, justification=0, background=self.bg_img)
        self.screen.blit(textsurface, (270,35))#((self.screen.get_width() / 2) - menutext.get_width() / 2, (self.screen.get_height() / 2) - menutext.get_height()))
        
        self.back_text = widgets.TextWidget("Back", colour=self.WHITE, size=44, highlight_increase=3, event=self.BACK_CLICK, font_filename='audiowide.ttf', bold=False)
        self.back_text.rect.center = self.screen.get_rect().center
        self.back_text.rect.top += 250
        self.help_text_widgets.append(self.back_text)
        
        self.loop()
        
    def highscore(self):
        self.state = "Highscore"
        highscores = "Top 20:\n\n\n"
        rank = 1
        highscores_list = self.read_highscores()
        for highscore in highscores_list:
            highscores += str(rank) + ". " + highscore
            rank += 1
        
        if len(highscores_list) == 20:
            highscores += "\n\nFor a full list, see highscores.txt"
        
        self.draw_bg()
        menufont = load_font('audiowide.ttf', 16)
        menurect = Rect(120,35,1045,620)
        textsurface = widgets.render_textrect(highscores, menufont, menurect, self.WHITE, justification=1, background=self.bg_img)
        self.screen.blit(textsurface, (120,35))#((self.screen.get_width() / 2) - menutext.get_width() / 2, (self.screen.get_height() / 2) - menutext.get_height()))
        
        self.back_text = widgets.TextWidget("Back", colour=self.WHITE, size=44, highlight_increase=3, event=self.BACK_CLICK, font_filename='audiowide.ttf', bold=False)
        self.back_text.rect.center = self.screen.get_rect().center
        self.back_text.rect.top += 250
        self.highscore_text_widgets.append(self.back_text)
        
        self.loop()
    
    def read_highscores(self):
        """Loads up to the 20 highest highscores and returns them in a sorted list"""
        highscores_list = []
        highscores_dict = defaultdict(list)
        highscores_file = open('highscores.txt', 'r')
        for highscore_line in highscores_file:
            if highscore_line != "\n":
                score = [int(s) for s in highscore_line.split() if s.isdigit()][-1] #Extract the rightmost integer in the string (safeguard against integer player names)
                highscores_dict[score].append(highscore_line)
        highscores_file.close()
        
        sorted_scores = sorted(highscores_dict.keys(), reverse=True)
        
        for score in sorted_scores:
            all_with_score_as_score = highscores_dict[score]
            all_with_score_as_score.reverse() #Makes newest entries in highscores.txt appear at the top if equal to an older score
            for highscore_line in all_with_score_as_score:
                highscores_list.append(highscore_line)
         
        highscores_list = highscores_list[:20]
        return  highscores_list

    def loop(self):
        while True:
            if android:
                if android.check_pause():
                    android.wait_for_resume()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "Main":
                            self.quit()
                        else:
                            if self.state == "Help":
                                self.main()
                            elif self.state == "Highscore":
                                self.main()
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_BACKSPACE:
                        if self.state == "Help":
                            self.main()
                        elif self.state == "Highscore":
                                self.main()
                    elif event.key== pygame.K_h and self.state == "Main":
                        self.help()
                #TextWidget stuff:
                if self.state == "Main":
                    if (event.type == pygame.ACTIVEEVENT):
                        if (event.gain == 1):
                            for text in self.main_text_widgets:
                                text.dirty = True
                            self.draw()
                        elif (event.state == 2):
                            #We are hidden so wait for the next event
                            pygame.event.post(pygame.event.wait())
                    elif (event.type == pygame.MOUSEMOTION):
                        for text in self.main_text_widgets:
                            orig = text.highlight
                            orig_rect = text.rect
                            text.highlight = text.rect.collidepoint(event.pos)
                            if orig != text.highlight:
                                for t in self.main_text_widgets:
                                    t.dirty = True
                                self.draw_bg(rect=orig_rect) #Redraw background if highlight state changes
                                
                    elif (event.type == pygame.MOUSEBUTTONDOWN):
                        for text in self.main_text_widgets:
                            text.on_mouse_button_down(event)
                    elif (event.type == pygame.MOUSEBUTTONUP):
                        for text in self.main_text_widgets:
                            text.on_mouse_button_up(event)
                    elif (event.type == self.NEW_GAME_CLICK):
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                        self.run_game()
                    elif (event.type == self.RESUME_CLICK):
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                        self.load_game()
                    elif (event.type == self.HELP_CLICK):
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                        self.help()
                    elif (event.type == self.HIGHSCORES_CLICK):
                        pygame.mouse.set_cursor(*pygame.cursors.arrow)
                        self.highscore()
                    elif (event.type == self.EXIT_CLICK):
                        self.quit()
                elif self.state == "Help":
                    if (event.type == pygame.ACTIVEEVENT):
                        if (event.gain == 1):
                            for text in self.help_text_widgets:
                                text.dirty = True
                            self.draw()
                        elif (event.state == 2):
                            #We are hidden so wait for the next event
                            pygame.event.post(pygame.event.wait())
                    elif (event.type == pygame.MOUSEMOTION):
                        for text in self.help_text_widgets:
                            orig = text.highlight
                            orig_rect = text.rect
                            text.highlight = text.rect.collidepoint(event.pos)
                            if orig != text.highlight:
                                for t in self.help_text_widgets:
                                    t.dirty = True
                                self.draw_bg(rect=orig_rect) #Redraw background if highlight state changes
                    elif (event.type == pygame.MOUSEBUTTONDOWN):
                        for text in self.help_text_widgets:
                            text.on_mouse_button_down(event)
                    elif (event.type == pygame.MOUSEBUTTONUP):
                        for text in self.help_text_widgets:
                            text.on_mouse_button_up(event)
                    elif (event.type == self.BACK_CLICK):
                        self.main()
                elif self.state == "Highscore":
                    if (event.type == pygame.ACTIVEEVENT):
                        if (event.gain == 1):
                            for text in self.highscore_text_widgets:
                                text.dirty = True
                            self.draw()
                        elif (event.state == 2):
                            #We are hidden so wait for the next event
                            pygame.event.post(pygame.event.wait())
                    elif (event.type == pygame.MOUSEMOTION):
                        for text in self.highscore_text_widgets:
                            orig = text.highlight
                            orig_rect = text.rect
                            text.highlight = text.rect.collidepoint(event.pos)
                            if orig != text.highlight:
                                for t in self.highscore_text_widgets:
                                    t.dirty = True
                                self.draw_bg(rect=orig_rect) #Redraw background if highlight state changes
                    elif (event.type == pygame.MOUSEBUTTONDOWN):
                        for text in self.highscore_text_widgets:
                            text.on_mouse_button_down(event)
                    elif (event.type == pygame.MOUSEBUTTONUP):
                        for text in self.highscore_text_widgets:
                            text.on_mouse_button_up(event)
                    elif (event.type == self.BACK_CLICK):
                        self.main()
            self.draw()

    def draw(self):
        """Draw everything"""
        for text in self.main_text_widgets:
            text.draw(self.screen)
        for text in self.help_text_widgets:
            text.draw(self.screen)
        for text in self.highscore_text_widgets:
            text.draw(self.screen)
        pygame.display.update()

    def run_game(self):
        self.game = Game(self.screen)
        self.game.run()
        del self
    
    def load_game(self, fileName=SAVE_FILE_NAME):
        if not saveFileExists(fileName):
            self.main()
            return
        shouldRemoveSaveFile = False
        loadFile = open(fileName, 'rb')
        try:
            self.game = pickle.load(loadFile)
        except:
            shouldRemoveSaveFile = True
        finally:
            loadFile.close()
        if shouldRemoveSaveFile:
            os.remove(fileName)
            self.main()
        else:
            self.game.loading_init()
            self.game.run()
            del self
    
    def quit(self):
        pygame.quit()
        sys.exit(0)

def saveFileExists(filePath=SAVE_FILE_NAME):
    return os.path.exists(filePath)

def saveFileNotCorrupt(filePath=SAVE_FILE_NAME):
    valid = os.path.exists(filePath)
    if valid:
        loadFile = open(filePath, 'rb')
        try:
            testLoadedGame = pickle.load(loadFile)
        except:
            valid = False
        finally:
            loadFile.close()
            if not valid:
                os.remove(filePath)
    return valid


def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")


def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))

    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))

def get_screen():
    return pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
def main():
    mixer.pre_init(44100, -16, 2, 1024) #sound effects are delayed on my windows machine without this, I think the buffer is initialized too large by default
    pygame.init()
    screen =  get_screen()
    pygame.display.set_caption(TITLE)
    pygame.display.set_icon(load_image(os.path.join('blocks', 'lightgreen.png')))
    if android:
        android.init()
        android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)
    while True:
        menu(screen)

def menu(screen):
    menu = Menu(screen)

if __name__ == '__main__':
    main()
