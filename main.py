import os
import time
import random
import pygame
pygame.init()


class Colours:
    RED = (200,0,0)
    GREEN = (0,200,0)
    BLUE = (0,0,200)
    BLACK = (0,0,0)
    WHITE = (255,255,255)
    GREY = (80,80,80)

class StaticSprite:
    def __init__(self,window,image,x,y,dx,dy):
        self.window = window
        self.image = image
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
    
    def updatePos(self):
        self.x += self.dx
        self.y += self.dy
    
    def draw(self):
        self.window.blit(self.image,(self.x,self.y))
    

class DynamicSprite(StaticSprite):
    def __init__(self,window,x,y,dx,dy,path,animation_time):
        super().__init__(window,None,x,y,dx,dy)
        self.path = path
        self.animation_time = animation_time
        self.index = 0
        self.images = self.getImages(path)
        self.image = self.images[self.index]
        self.mask = pygame.mask.from_surface(self.image)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.last_switch = time.perf_counter()
    
    @staticmethod
    def getImages(path):
        images = []
        for file_name in os.listdir(path):
            path_name = path + os.sep + file_name
            image = pygame.image.load(path_name)
            images.append(image)
        return images
    
    def setNewImage(self):
        if time.perf_counter() - self.last_switch >= self.animation_time:
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]
            self.mask = pygame.mask.from_surface(self.image)
            self.width = self.image.get_width()
            self.height = self.image.get_height()
            self.last_switch = time.perf_counter()
    
    def draw(self):
        self.window.blit(self.image,(self.x,self.y))
        self.setNewImage()

class Dino(DynamicSprite):
    def __init__(self,window,x,y,dx,dy,path,animation_time,max_dy,g,ground_level):
        super().__init__(window,x,y,dx,dy,path,animation_time)
        self.sortImages()
        self.x = 25
        self.y = ground_level - self.height
        self.max_dy = max_dy
        self.g = g #deceleration due to gravity
        self.ground_level = ground_level
        self.jumping = False
        self.jump_start = None #when dino started the jump
        self.jump_sound = pygame.mixer.Sound("sounds/jump_sound.wav")
        self.dead = False
        self.start_time = time.perf_counter()
        self.points = 0
    
    def sortImages(self):
        self.walking_images = []
        self.ducking_images = []
        for file_name in os.listdir(self.path):
            path_name = self.path + os.sep + file_name
            image = pygame.image.load(path_name)
            if "walking" in file_name.lower():
                self.walking_images.append(image)
            
            elif "ducking" in file_name.lower():
                self.ducking_images.append(image)
            
            else:
                self.walking_images.append(image)
    
    def checkJump(self,events):
        if self.jumping:
            return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.dy = self.max_dy
                    self.jumping = True
                    self.jump_start = time.perf_counter()
                    pygame.mixer.Sound.play(self.jump_sound)
        
    def updateSpriteArray(self,keys_pressed):
        old_images = [i for i in self.images]
        if keys_pressed[pygame.K_DOWN] and not self.jumping:
            self.images = self.ducking_images
        else:
            self.images = self.walking_images
        
        if old_images != self.images:
            self.last_switch = 0
    
    def updateVel(self):
        time_elapsed = time.perf_counter() - self.jump_start
        self.dy = self.dy + self.g * time_elapsed
    
    def updatePos(self):
        self.y += self.dy
        if self.y + self.height > self.ground_level:
            self.y = self.ground_level - self.height
            self.dy = 0
            self.jumping = False
            self.jump_start = None
    
    def checkCollision(self,obstacles):
        for obstacle in obstacles:
            obstacle_image = obstacle.image
            obstacle_x = obstacle.x
            obstacle_y = obstacle.y
            obstacle_mask = pygame.mask.from_surface(obstacle_image)
            offset = (int(obstacle_x - self.x), int(obstacle_y - self.y))
            result = self.mask.overlap(obstacle_mask,offset)

            if result:
                self.dead = True
                break
    
    def updatePoints(self):
        if self.dead:
            return
        seconds_elapsed = time.perf_counter() - self.start_time  
        self.points = round(seconds_elapsed * 10)
    
    def reset(self):
        self.jumping = False
        self.jump_start = None #when dino started the jump
        self.dead = False
        self.start_time = time.perf_counter()
        self.points = 0
        self.y = self.ground_level - self.height
    
    def draw(self,events,keys_pressed):
        self.checkJump(events)
        if self.jumping:
            self.updateVel()
        else:
            self.y = self.ground_level - self.height
        self.updateSpriteArray(keys_pressed)
        self.updatePos()
        super().draw()

class Bird(DynamicSprite):
    def __init__(self,window,x,y,dx,dy,path,animation_time):
        super().__init__(window,x,y,dx,dy,path,animation_time)
    
    def updatePos(self):
        self.x -= self.dx

class Cacti(StaticSprite):
    def __init__(self,window,image,x,y,dx,dy):
        super().__init__(window,image,x,y,dx,dy)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
    
    def updatePos(self):
        self.x -= self.dx


class Game:
    def __init__(self,win_x,win_y):
        self.win_x = win_x
        self.win_y = win_y
        self.window = pygame.display.set_mode((win_x,win_y))
        self.platform_w = PLATFORM_W
        self.platform_h = PLATFORM_H
        self.platform_y = PLATFORM_Y
        self.platform_dx = PLATFORM_DX
        self.platform1_x = 0
        self.platform2_x = self.platform_w
        self.platform_colour = Colours.BLUE

        self.player_folder = "player_sprites"
        self.dino = Dino(self.window,0,0,0,0,self.player_folder,0.25,MAX_DY,g,self.platform_y)

        self.background_folder = "background_sprites"
        self.setBackGround()

        self.enemies_folder = "enemy_sprites"
        self.obstacles = []
        self.obstacle_frequency = OBSTACLE_FREQUENCY
        self.fps = FPS

        self.gameover_sound = pygame.mixer.Sound("sounds/dead_sound.wav")
    
    def spawnObstacles(self):
        last_x = None
        for i in range(self.obstacle_frequency):
            cacti_image = random.choice(self.cacti_array)
            if last_x == None:
                x = self.platform_w
            else:
                x = last_x + (0.25 * self.platform_w) * random.uniform(0 * self.platform_w, 0.5 * self.platform_w)
            last_x = x
            y = self.platform_y - cacti_image.get_height() 
            cacti_obstacle = Cacti(self.window,cacti_image,x,y,self.platform_dx,0)
            self.obstacles.append(cacti_obstacle)

            bird_prob = 4 * self.obstacle_frequency
            if random.randint(0,bird_prob) == 1 :
                bird_obstacle = Bird(self.window,0,0,self.platform_dx * BIRD_SPEED,0,self.enemies_folder,0.25)
                bird_obstacle.x = random.uniform(self.platform_w, self.platform_w * 2)
                bird_obstacle.y = random.uniform(self.win_y / 2, self.platform_y - bird_obstacle.height)
                self.obstacles.append(bird_obstacle)
    
    def updateObstacles(self):
        for obstacle in self.obstacles:
            obstacle.updatePos()
            if obstacle.x < -obstacle.width:
                self.obstacles.remove(obstacle)
                continue

    def drawObstacles(self):
        for obstacle in self.obstacles:
            obstacle.draw()

    def setBackGround(self):
        file_names = [file_name for file_name in os.listdir(self.background_folder)]
        self.cacti_array = []
        for file_name in file_names:
            image = pygame.image.load(self.background_folder + os.sep + file_name)
            if "background" in file_name.lower():
                self.bg_image = pygame.transform.scale(image,(self.win_x,self.win_y))
            
            elif "platform" in file_name.lower():
                self.platform_image = pygame.transform.scale(image,(self.platform_w * 1.2,self.platform_h))
            
            elif "cacti" in file_name.lower():
                self.cacti_array.append(image) 
    
    def drawBackground(self):
        self.window.blit(self.bg_image,(0,0))
        self.window.blit(self.platform_image,(self.platform1_x,self.platform_y))
        self.window.blit(self.platform_image,(self.platform2_x,self.platform_y))
    
    def displayPoints(self):
        font = pygame.font.SysFont("consolas",20)
        score_str = "Score: {}".format(self.dino.points)
        score_surface = font.render(score_str,False,Colours.GREEN)
        score_surface_rect = score_surface.get_rect()
        score_surface_rect.center = (self.win_x * 0.5, self.win_y * 0.1)
        self.window.blit(score_surface,score_surface_rect)
    
    def displayGameOver(self):
        self.window.fill(Colours.BLACK)
        gameover_str = "Game Over! Score: {}".format(self.dino.points)
        font = pygame.font.SysFont("Consolas",50)
        gameover_surface = font.render(gameover_str,False,Colours.RED)
        gameover_rect = gameover_surface.get_rect()
        gameover_rect.center = (self.win_x / 2, self.win_y / 2)
        self.window.blit(gameover_surface,gameover_rect)
        pygame.display.update()
    
    def updateSpeeds(self):
        maximum = PLATFORM_DX * 2.45
        if self.platform_dx >= maximum:
            self.platform_dx = maximum
            return
        time_elapsed = time.perf_counter() - self.dino.start_time
        increase = 1
        if 20 < time_elapsed < 40:
            increase = 1.25

        elif 40 < time_elapsed < 60:
            increase = 1.56

        elif 60 < time_elapsed < 80:
            increase = 1.95
        
        elif 80 < time_elapsed < 100:
            increase = 2.45
    
        self.platform_dx = PLATFORM_DX * increase
        for obstacle in self.obstacles:
            if isinstance(obstacle,Bird):
                obstacle.dx = self.platform_dx * BIRD_SPEED
            else:
                obstacle.dx = self.platform_dx
        
    
    def reset(self):
        self.dino.reset()
        self.obstacles = []
        self.platform_dx = PLATFORM_DX

    def startGame(self):
        clock = pygame.time.Clock()
        quit_game = False
        while not quit_game:
            clock.tick(self.fps)
            events = pygame.event.get()
            keys_pressed = pygame.key.get_pressed()
            for event in events:
                if event.type == pygame.QUIT:
                    quit_game = True
            
            self.platform1_x -= self.platform_dx
            self.platform2_x -= self.platform_dx

            if self.platform1_x < -self.platform_w:
                self.platform1_x = self.platform_w - 20
                self.spawnObstacles()
            
            if self.platform2_x < -self.platform_w:
                self.platform2_x = self.platform_w - 20
                self.spawnObstacles()
            
            self.drawBackground()
            self.dino.draw(events,keys_pressed)

            self.updateObstacles()
            self.drawObstacles()
            self.dino.checkCollision(self.obstacles)

            self.dino.updatePoints()
            self.displayPoints()

            if self.dino.dead:
                pygame.mixer.Sound.play(self.gameover_sound) 
                self.displayGameOver()
                pygame.time.delay(1000)
                self.reset()
            
            self.updateSpeeds()
            
            pygame.display.update()
            self.window.fill(Colours.GREY)
        
        pygame.quit()
        print("program quit")
    
        

WIN_X = 800
WIN_Y = 500
PLATFORM_W = WIN_X
PLATFORM_H = WIN_Y * 0.15
PLATFORM_Y = WIN_Y * 0.85
PLATFORM_DX = 4.65

BIRD_SPEED = 1.25
        
MAX_DY = -6.35
g = 0.65
OBSTACLE_FREQUENCY = 4

FPS = 60


g = Game(WIN_X,WIN_Y)
g.startGame()
