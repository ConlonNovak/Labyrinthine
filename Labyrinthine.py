#################################################################################
#Labyrinthine (TP3)
#15-112 Term Project Deliverable
#TP3 (Final Product)
#By Conlon Novak (AndrewID: conlonn)
#Section CC
#Mentor: Arman Hezarkhani
#################################################################################
#Made using:
    #PyGame framework from optional lecture by Lukas Peraza
'''     pygamegame.py
        created by Lukas Peraza
            for 15-112 F15 Pygame Optional Lecture, 11/11/15
        - you should remove the print calls from any function you aren't using
        - you might want to move the pygame.display.flip() to your redrawAll function,
            in case you don't need to update the entire display every frame (then you
            should use pygame.display.update(Rect) instead)'''
    #PlayfulJS Raycasting tutorial and accompanying materials
"""     http://www.playfuljs.com/a-first-person-engine-in-265-lines/"""
    #Helper functions from 15-112 notes
"""     2DList functions, elements of maze solving algorithm, etc"""
    #Textures
        #Minecraft door texture copyright Mojang, Microsoft
        #Zelda dungeon key texture copyright Nintendo
        #Help Screen Icons
            #Mouse Icon http://simpleicon.com/wp-content/uploads/mouse.png
            #Shift Icon https://pixabay.com/p-37762/?no_redirect
            #WASD Icon http://virtual.mhel-project.eu/client/app/img/wasd_icon.png
        #Nicholas S: wall texture http://shadowh3.deviantart.com/art/Wall-Texture-73682375
        #Dan Duriscoe: Death Valley skybox http://apod.nasa.gov/apod/ap070508.html
    #Music
        #Menu music https://www.youtube.com/watch?v=itPtO4EaEXU
        #Walking sfx https://www.freesound.org/people/Fantozzi/sounds/166289/
        #Running sfx https://www.freesound.org/people/Fantozzi/sounds/166290/
        #door close sfx https://www.youtube.com/watch?v=eXZd094EYus
        #doo open sfx https://www.youtube.com/watch?v=VLMbtJCiOG4
#################################################################################

import os, pygame, sys, random, math, decimal, random, time

# helper functions from 15-112 course notes
def make2dList(rows, cols, value = (0,0)):
    a=[]
    for row in range(rows): a += [[value]*cols]
    return a

def memoized(f):
    import functools
    cachedResults = dict()
    @functools.wraps(f)
    def wrapper(*args):
        if args not in cachedResults:
            cachedResults[args] = f(*args)
        return cachedResults[args]
    return wrapper

def maxItemLength(a):
    maxLen = 0
    rows = len(a)
    cols = len(a[0])
    for row in range(rows):
        for col in range(cols):
            maxLen = max(maxLen, len(str(a[row][col])))
    return maxLen

def print2dList(a):
    if (a == []):
        print([])
        return
    rows = len(a)
    cols = len(a[0])
    fieldWidth = maxItemLength(a)
    print("[ ", end="")
    for row in range(rows):
        if (row > 0): print("\n  ", end="")
        print("[ ", end="")
        for col in range(cols):
            if (col > 0): print(", ", end="")
            formatSpec = "%" + str(fieldWidth) + "s"
            print(formatSpec % str(a[row][col]), end="")
        print(" ]", end="")
    print("]")

def almostEqual(d1, d2, epsilon=10**-7):
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

def roundHalfUp(d):
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    # See other rounding options here:
    # https://docs.python.org/3/library/decimal.html#rounding-modes
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

##########################################################################

#Helper functions
def perpAngle(angle): #returns angle perpendicular to a given radian angle, used for strafing
    return (angle + (3*math.pi/2)) % (2*math.pi)

#pyinstaller code
def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

#Memoized trig calls, made 100s of times per second
@memoized
def memoizedSin(angle):
    return math.sin(angle)

@memoized
def memoizedCos(angle):
    return math.cos(angle)

@memoized
def memoizedHyp(dx, dy):
    return math.hypot(dx, dy)

##########################################################################

#Player class, responsible for movement and loction within maze
class Player(object):
    def __init__(self, x = 1.5, y = 1.5, direction = 0):
        self.x = x
        self.y = y
        self.v = 0                                      #velocity
        self.strafev = 0                                #strafe velocity
        self.direction = direction
        self.hasKey = False
        self.delta = 0                                  #menu camera rate of rotation
        self.menuLeft = True                            #menu camera state

    def rotate(self, angle):                            #user-controlled mouse turning function
        self.direction = (self.direction + angle) % (2*math.pi)

    def menuRotate(self, angle):                        #designed for menuPlayer on splash screen
        self.rotate(angle)

    def walk(self, gameMap):                            #responsible for walking and strafing
        perpendicAngle = perpAngle(self.direction)
        dx = math.cos(self.direction)*self.v + math.cos(perpendicAngle)*self.strafev
        dy = math.sin(self.direction)*self.v + math.sin(perpendicAngle)*self.strafev
        if gameMap.get(self.x+dx, self.y) <= 0:         #wall collision detection
            self.x += dx
        if gameMap.get(self.x, self.y+dy) <= 0:
            self.y += dy

class GameMap(object):                                  #Class to create 2D array maps and mazes
    def __init__(self, width=10, height=10, complexity=1):
        self.wallGrid = []
        self.width = width
        self.height = height
        self.EMPTY = (0,0)
        self.WALL = (1,1)
        self.SAFE = 2                                   #Cells that will eventually be empty, but cannot be walled over
        self.complexity = complexity                    #number of recursive divisions of the maze by random walls

        #                  |   small maze   |   large maze    |
        #                  ------------------------------------
        #    low complexity|   very easy    | large spaces lag| 
        #                  ------------------------------------
        #   high complexity| relatively open|  very difficult |
        #                  ------------------------------------
        
    def generateMaze(self):                             #wrapper function for recursive maze generation
        self.wallGrid = make2dList(self.height, self.width)
        for row in range(self.height):
            self.wallGrid[row][0] = self.WALL                           #left border walls
            self.wallGrid[row][self.width-1] = self.WALL                #right border walls
        for col in range(self.width):
            self.wallGrid[0][col] = self.WALL                           #top border walls
            self.wallGrid[self.height-1][col] = self.WALL               #bot border walls
        self.wallGrid[1][self.width-2] = self.SAFE                      #door in upper right
        self.wallGrid[self.height-2][1] = self.SAFE                     #key in bottom left
        self.spawnX, self.spawnY = random.randint(1,self.height-2), random.randint(1,self.width-2)      #generate random spawn point
        while self.wallGrid[self.spawnY][self.spawnX] == self.WALL:
            self.spawnX, self.spawnY = random.randint(1,self.height-2), random.randint(1,self.width-2)  #generate non-wall spawn point
        self.wallGrid[self.spawnX][self.spawnY] = self.SAFE                                             #ensure that spawn is protected
        self.randomizeChamber(0,0,self.width, self.height)              #randomize maze
        for row in range(self.height):
            for col in range(self.width):
                val = self.wallGrid[row][col]
                if val == self.SAFE: 
                    self.wallGrid[row][col] = (0,0)                     #replace temp protected squares with hallways
        self.wallGrid[1][self.width-1] = (1,5)          #door texture
        self.wallGrid[2][self.width-1] = (1,3)          #door instructions texture (find the key)
        self.wallGrid[self.height-1][1] = (1,4)         #key texture
        self.wallGrid[self.height-1][2] = (1,8)         #key instructions texture
        #print2dList(self.wallGrid)
        for row in range(len(self.wallGrid)):
            for col in range(len(self.wallGrid[0])):
                if self.wallGrid[row][col][1] == 5:
                    self.doorPosX, self.doorPosY = col, row              #find and record position of the door, key
                elif self.wallGrid[row][col][1] == 4:
                    self.keyPosX, self.keyPosY = col, row
        
    def randomizeChamber(self, row, col, width, height, depth = 0): #recursively and randomly place dividing walls across a quadrant
        if width <= 4 or height <= 4 or depth==self.complexity: #don't divide 2x2 spaces, don't recurse if at maximum depth (complexity)
            return None
        randRow = random.randint(row+2, row + height-3)         #pick a random row and col in the quadrant
        randCol = random.randint(col+2, col + width-3)
        randCompleteWall = random.randint(1,4)                  #only place one solid wall, place hallways in the rest
        wall1hole = random.randint(row+1, randRow-1)            #generate location of the hallways
        wall2hole = random.randint(col+1, randCol-1)
        wall3hole = random.randint(randRow+1, row + height-2)
        wall4hole = random.randint(randCol+1, col + width-2)        
        for x in range(row+1, row + height-1):
            if self.wallGrid[x][randCol] == self.EMPTY:         #replace empty tiles in randRow and randCol with walls
                self.wallGrid[x][randCol] = self.WALL 
        for y in range(col+1, col + width-1):
            if self.wallGrid[randRow][y] == self.EMPTY:
                self.wallGrid[randRow][y] = self.WALL
        if randCompleteWall != 1:
            self.wallGrid[wall1hole][randCol] = self.SAFE       #protect hallway through incomplete walls
            self.wallGrid[wall1hole][randCol-1] = self.SAFE
            self.wallGrid[wall1hole][randCol+1] = self.SAFE
        if randCompleteWall != 2:
            self.wallGrid[randRow][wall2hole] = self.SAFE
            self.wallGrid[randRow+1][wall2hole] = self.SAFE
            self.wallGrid[randRow-1][wall2hole] = self.SAFE
        if randCompleteWall != 3:
            self.wallGrid[wall3hole][randCol] = self.SAFE
            self.wallGrid[wall3hole][randCol+1] = self.SAFE
            self.wallGrid[wall3hole][randCol-1] = self.SAFE
        if randCompleteWall != 4:
            self.wallGrid[randRow][wall4hole] = self.SAFE
            self.wallGrid[randRow+1][wall4hole] = self.SAFE
            self.wallGrid[randRow-1][wall4hole] = self.SAFE
            
        self.randomizeChamber(0, 0, randCol, randRow, depth+1)                                      #randomize top-left quadrant
        self.randomizeChamber(0, randCol, self.width-randCol, randRow+1, depth+1)                   #randomize top-right quadrant
        self.randomizeChamber(randRow, 0, randCol+1, self.height-randRow, depth+1)                  #randomize bottom-left quadrant
        self.randomizeChamber(randRow, randCol, self.width-randCol, self.height-randRow, depth+1)   #randomize bottom-right quadrant

    def setDimensions(self, width, height):             #set dimensions of the maze
        self.width = width
        self.height = height

    def get(self, y, x):                                #returns 1 if there's a wall at (x,y), 0 otherwise. Takes floats
        x = math.floor(x)
        y = math.floor(y)
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return -1
        return self.wallGrid[x][y][0]

    def getTexture(self, y, x):                         #returns texture of wall at (x,y), 0 if there isn't one. Takes floats
        x = math.floor(x)
        y = math.floor(y)
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return -1
        return self.wallGrid[x][y][1]

    def setValue(self, x, y, value):                    #cell value modifier
        self.wallGrid[x][y] = value

    def menuRoom(self):                                 #splash screen menu scene
        height = 7
        width = 7
        self.wallGrid = make2dList(height, width)
        self.wallGrid = [[(1,1),(1,1),(1,1),(1,1),(1,1),(1,1),(1,1)],
                         [(1,1),(0,0),(0,0),(0,0),(0,0),(0,0),(1,1)],
                         [(1,1),(0,0),(0,0),(0,0),(0,0),(0,0),(1,6)],
                         [(1,1),(0,0),(0,0),(0,0),(0,0),(0,0),(1,5)],
                         [(1,1),(0,0),(0,0),(0,0),(0,0),(0,0),(1,4)],
                         [(1,1),(0,0),(0,0),(0,0),(0,0),(0,0),(1,18)],
                         [(1,1),(1,1),(1,19),(1,7),(1,2),(1,1),(1,1)]]
        for row in range(len(self.wallGrid)):
            for col in range(len(self.wallGrid[0])):
                if self.wallGrid[row][col][1] == 5:
                    self.doorPosX, self.doorPosY = col, row
                elif self.wallGrid[row][col][1] == 4:
                    self.keyPosX, self.keyPosY = col, row

    def testGrid(self):
        self.wallGrid = [[(1,1),(1,1),(1,1),(1,1),(1,1),(1,1),(1,1)],
                         [(1,1),(0,0),(0,0),(0,0),(0,0),(0,0),(1,1)],
                         [(1,1),(0,0),(1,1),(1,1),(1,1),(1,1),(1,1)],
                         [(1,1),(0,0),(1,1),(0,0),(0,0),(0,0),(1,1)],
                         [(1,1),(0,0),(1,5),(0,0),(1,1),(0,0),(1,1)],
                         [(1,1),(0,0),(0,0),(0,0),(1,1),(0,0),(1,4)],
                         [(1,1),(1,1),(1,1),(1,1),(1,1),(1,1),(1,1)]]
        for row in range(len(self.wallGrid)):
            for col in range(len(self.wallGrid[0])):
                if self.wallGrid[row][col][1] == 5:
                    self.doorPosX, self.doorPosY = col, row
                elif self.wallGrid[row][col][1] == 4:
                    self.keyPosX, self.keyPosY = col, row

    def updateKey(self, player):                        #checks to see if the player is close enough to pick up the key
        if abs(player.y-self.keyPosY) <=1 and abs(player.x-self.keyPosX) <= 1 and not player.hasKey:
            player.hasKey = True
            player.keyTone = True                       #audio cue flag (sound of opening door)
            self.wallGrid[self.keyPosY][self.keyPosX] = (1,1)
            self.wallGrid[self.doorPosY][self.doorPosX] = (1,7)

    def checkEscape(self, player):                      #checks to see if the player is close enough escape through the unlocked door
        if abs(player.y-self.doorPosY) <=1 and abs(player.x-self.doorPosX) <= 1 and player.hasKey:
            return True
        return False

    """def cast(self, point, angle, range):             #WIP Recursive raycasting algorithm
        sin = memoizedSin(angle)
        cos = memoizedCos(angle)
        origin = Point(point)
        self.recursiveCast(origin, angle, range, sin, cos)

    def recursiveCast(self, origin, angle, range, sin, cos):
        if origin.height < 0 or origin.distance > range:
            return origin
        else:
            dist = origin.distance
            stepX = origin.step(sin, cos)
            stepY = origin.step(cos, sin, invert = True)
            if stepX.length < stepY.length:
                nextStep = stepX.inspect(sin, cos, self, 1, 0, dist, stepX.y)
            else:
                nextStep = stepY.inspect(sin, cos, self, 0, 1, dist, stepY.x)
            temp = self.cast(nextStep, angle, range)
            if temp != None:
                return temp
        return None"""

    def cast(self, point, angle, range):                #based on PlayJS Tutorial
        sin = memoizedSin(angle)                        #adj side of triangle
        cos = memoizedCos(angle)                        #opp side of tirangle
        origin = Point(point)                           #starting point
        ray = origin
        while origin.height <= 0 and origin.distance <= range:  #while there's not a wall and the ray hasn't gone too far:
            dist = origin.distance
            stepX = origin.step(sin, cos)               #find the next x intercept
            stepY = origin.step(cos, sin, invert = True)#find the next y intercept
            if stepX.length < stepY.length:             #depending on which is closer, use that for the next point to check
                nextStep = stepX.inspect(sin, cos, self, 1, 0, dist, stepX.y)
            else:
                nextStep = stepY.inspect(sin, cos, self, 0, 1, dist, stepY.x)
            ray = nextStep
            origin = nextStep
        return ray

class Point(object):                                    #just a point with a couple of ray attributes
    def __init__(self, point, length = None):
        if isinstance(point, Point):
            self.x = point.x
            self.y = point.y
        elif isinstance(point, tuple):
            self.x = point[0]
            self.y = point[1]
        self.height = 0                                 #these will all be ones for walls and zeros for hallways
        self.distance = 0
        self.length = length                            

    def step(self, rise, run, invert = False):          #steps to the next x (or y if inverted) intercept
        x, y = (self.y,self.x) if invert else (self.x,self.y)
        dx = math.floor(x+1)-x if run > 0 else math.ceil(x-1)-x
        if run == 0:
            nextX = nextY = None
            length = float("inf") #No wall              #length = infinity if you try to divide by zero
        else:
            dy = dx*(rise/run)
            nextX = y+dy if invert else x+dx
            nextY = x+dx if invert else y+dy
            length = memoizedHyp(dx, dy)     
        return Point((nextX,nextY), length)

    def inspect(self, sin, cos, gameMap, shiftX, shiftY, distance, offset): #inspect given point on the maze and give the point its attributes
        dx = shiftX if cos < 0 else 0
        dy = shiftY if sin < 0 else 0
        self.height = gameMap.get(self.x-dx, self.y-dy)
        self.distance = distance + self.length
        self.offset = offset-math.floor(offset)
        return self

    def __repr__(self):
        return "(%f, %f, height = %f, dist = %f)" %(self.x, self.y, self.height, self.distance)

class Camera(object):                                    #renders 2.5D scenes and raycasts
    def __init__(self, screen, resolution, gameMap, focalLength = 0.8, ):
        self.screen = screen
        self.width, self.height = self.screen.get_size()
        self.resolution = float(resolution)              #number of columns per image
        self.spacing = self.width / self.resolution
        self.range =  (gameMap.width**2+gameMap.height**2)**.5 #longest possible distance is hypotanose of maze
        self.fieldOfView = math.pi*0.4
        self.scale = (self.width + self.height) / 1200
        self.textures = dict()
        self.loadTextures()
            
    def loadTextures(self):                             #dictionary of texture files
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        #print(script_dir)
        rel_path = "resources\images"
        full_images_dir_path = os.path.join(script_dir, rel_path)
        #print(full_images_dir_path)
        #print(os.path.join(full_images_dir_path, "deathvalley_panorama.jpg"))
        self.skyImg = pygame.image.load(os.path.join(full_images_dir_path, "deathvalley_panorama.jpg")).convert()
        self.skySize = int(self.width * (2*math.pi)/self.fieldOfView), self.height
        self.sky = pygame.transform.smoothscale(self.skyImg, self.skySize)
        self.wall = pygame.image.load(os.path.join(full_images_dir_path, "wall.jpg")).convert()
        self.wallA = pygame.image.load(os.path.join(full_images_dir_path, "wallA.jpg")).convert()
        self.instr = pygame.image.load(os.path.join(full_images_dir_path, "instr.jpg")).convert()
        self.key = pygame.image.load(os.path.join(full_images_dir_path, "key.jpg")).convert()
        self.exit = pygame.image.load(os.path.join(full_images_dir_path, "exit.jpg")).convert()
        self.run = pygame.image.load(os.path.join(full_images_dir_path, "run.jpg")).convert()
        self.escape = pygame.image.load(os.path.join(full_images_dir_path, "escape.jpg")).convert()
        self.doorinstr = pygame.transform.flip(pygame.image.load(os.path.join(full_images_dir_path, "doorinstr.jpg")).convert(),True, False)
        self.quit = pygame.image.load(os.path.join(full_images_dir_path, "quit.jpg")).convert()
        self.textures[0] = self.wall
        self.textures[1] = self.wall
        self.textures[2] = self.wallA
        self.textures[3] = self.instr
        self.textures[4] = self.key
        self.textures[5] = self.exit
        self.textures[6] = self.run
        self.textures[7] = self.escape
        self.textures[8] = self.doorinstr
        self.textures[9] = self.quit
        self.textures[10] = self.escape                                         #non-functional escape texture for menu scene
        self.textures[12] = pygame.transform.flip(self.wallA,True, False)       #flipped textures
        self.textures[13] = pygame.transform.flip(self.instr,True, False)
        self.textures[16] = pygame.transform.flip(self.run,True, False)
        self.textures[18] = pygame.transform.flip(self.doorinstr,True, False)
        self.textures[19] = pygame.transform.flip(self.quit,True, False)

    def render(self, player, gameMap):                  #draw the game
        self.drawSky(player.direction, self.sky)
        self.drawCols(player, gameMap)

    def drawSky(self, direction, sky):                  #draw the rotating panorama skybox
        skyWidth, skyHeight = sky.get_size()
        self.left = -skyWidth*direction/(2*math.pi)
        self.screen.blit(sky, (self.left,0))
        if self.left<skyWidth-self.width:
            self.screen.blit(sky, (self.left+skyWidth,0))

    def drawCols(self, player, gameMap):                #wrapper function to call drawCol on every col on the screen
        for col in range(int(self.resolution)):
            angle = self.fieldOfView*(col/self.resolution-.5)
            point = player.x, player.y
            ray = gameMap.cast(point, player.direction + angle, self.range)
            self.drawCol(col, ray, angle, gameMap)

    def drawCol(self, col, ray, angle, gameMap):        #draws 1px slices of image files at different sizes based on their distance to the camera
        left = int(math.floor(col*self.spacing))
        step = ray
        if step.height > 0:
            texture = self.textures[gameMap.getTexture(step.x, step.y)]
            textureWidth, textureHeight = texture.get_size()
            width = int(math.ceil(self.spacing))
            texture_x = int(textureWidth*step.offset)
            wall = self.project(step.height, angle, step.distance)
            image_location = pygame.Rect(texture_x, 0, 1, textureHeight)
            image_slice = texture.subsurface(image_location)
            scale_rect = pygame.Rect(left, wall[0], width, wall[1])
            scaled = pygame.transform.scale(image_slice, scale_rect.size)
            self.screen.blit(scaled, scale_rect)

    def project(self, height, angle, distance):         #scales slice to the distance at which it's seen by the player (smaller = further away)
        z = max(distance*math.cos(angle), 0.2)
        wallHeight = self.height*height/float(z)
        bottom = self.height/2.0*(1+1/float(z))
        return (bottom-wallHeight, wallHeight)

class PygameGame(object):                               #The skeleton of the game, heavily modified framework from mini-lecture
    def init(self):
        self.screen = pygame.display.get_surface()
        self.SPLASH = 0
        self.GAME = 1
        self.END = 2
        self.HELP = 3
        self.SETTINGS = 4
        self.state = self.SPLASH                        #self.state handles the switching between 'modes' - splash screen, game, end screen, help screen
        self.TIMEREVENT = 1                             
        pygame.time.set_timer(self.TIMEREVENT,10)       #custom-made event that fires the countdown timer every .01 seconds
        self.hPressed = False
        self.initSplashGrid()                           #menu room
        self.initMusic()                                

    def initMusic(self):                                #imports music
        pygame.mixer.init(channels=3)
        self.music = 0                                  #sets individual channels so multiple layers of sounds can play at once
        self.movement = 1
        self.sfx = 2
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        rel_path = "resources\sounds"
        full_sound_dir_path = os.path.join(script_dir, rel_path)
        #print(script_dir)
        #print(full_sound_dir_path)
        #print(os.path.join(full_sound_dir_path, "walkingLoop.wav"))
        self.dooropen  = pygame.mixer.Sound(os.path.join(full_sound_dir_path, "dooropen.wav"))
        self.doorclose = pygame.mixer.Sound(os.path.join(full_sound_dir_path, "doorclose.wav"))
        self.menumusic = pygame.mixer.Sound(os.path.join(full_sound_dir_path, "menumusic.wav"))
        self.walking   = pygame.mixer.Sound(os.path.join(full_sound_dir_path, "walkingLoop.wav"))
        self.running   = pygame.mixer.Sound(os.path.join(full_sound_dir_path, "runningLoop.wav"))
        self.inMotion  = False                          #flag to play walking sounds when moving and not sprinting
        self.sprinting = False                          #flag to play running sounds when moving and sprinting
        pygame.mixer.Channel(self.music).play(self.menumusic, -1) #start background music

    def initGame(self, width=10, height=10, complexity=1, timer=152.0): #initializes a level with a maze, player, camera, and timer
        self.gameMap = GameMap(width, height, complexity)
        self.gameMap.generateMaze()
        #print2dList(self.gameMap.wallGrid)
        self.player = Player(x = self.gameMap.spawnY+.5, y = self.gameMap.spawnX+.5, direction = random.randint(0,359)*math.pi/180.0)
        self.camera = Camera(self.screen, 300, self.gameMap)
        self.hasEscaped = False
        self.countdown = timer

    def initCampaign(self):                             #creates a list of initialization values for a series of levels
        self.mapList = []
        self.currMap = 0
        self.mapList.append((7, 7, 0, 122))             #tutorial - open room
        for i in range(0,3):                            #mazes increase in difficulty over time
            size = (i*3)+10
            complexity = 1+i
            timer = 62.0 + i*10
            self.mapList.append((size, size, complexity, timer))
        for i in range(0,3):
            size = (i*3)+15
            complexity = 2+i
            timer = 92.0 + i*30
            self.mapList.append((size, size, complexity, timer))
        for i in range(0,3):
            size = (i*3)+20
            complexity = 3+i
            timer = 152.0 + i*90
            self.mapList.append((size, size, complexity, timer))

    def initSplashGrid(self):                           #initializes menu room with room, camera, and stationary player
        self.hPressed = False
        self.menuRoom = GameMap()
        self.menuRoom.menuRoom()
        self.menuCamera = Camera(self.screen, 300, self.menuRoom)
        self.menuPlayer = Player(x = 3.5, y = 3.5)
        self.menuPlayer.direction = 0

    def mousePressed(self, x, y):
        pass

    def mouseReleased(self, x, y):
        pass

    def mouseMotion(self, x, y):                        #relative mouse movement controls, needs to be fullscreen
        if self.state == self.GAME:
            angle = pygame.mouse.get_rel()[0]
            angle /= 300                                #mouse sensitivity
            self.player.rotate(angle)

    def mouseDrag(self, x, y):
        pass

    def keyPressed(self, keyCode, modifier):
        #if (keyCode == pygame.K_ESCAPE):               #debugging: quits the game
            #self.playing = False
        if self.state == self.GAME:
            if (keyCode == pygame.K_a):                 #sets movement to strafe left
                if not self.inMotion:
                    pygame.mixer.Channel(self.movement).play(self.walking, -1)
                    self.inMotion = True
                    self.sprinting = False
                self.player.strafev = .15                
            if (keyCode == pygame.K_d):                 #sets movemtn to strafe right
                if not self.inMotion:
                    pygame.mixer.Channel(self.movement).play(self.walking, -1)
                    self.inMotion = True
                    self.sprinting = False
                self.player.strafev = -.15 
            if (keyCode == pygame.K_w):                 #sets movement to move forward
                if not self.inMotion:
                    pygame.mixer.Channel(self.movement).play(self.walking, -1)
                    self.inMotion = True
                    self.sprinting = False
                self.player.v = .15 
            if (keyCode == pygame.K_s):                 #sets movement to move backward
                if not self.inMotion:
                    pygame.mixer.Channel(self.movement).play(self.walking, -1)
                    self.inMotion = True
                    self.sprinting = False
                self.player.v = -.15 
            if (keyCode == pygame.K_LSHIFT):            #sprinting triples all active movement
                if (not self.inMotion or self.inMotion and not self.sprinting):
                    pygame.mixer.Channel(self.movement).play(self.running, -1)
                    self.inMotion = True
                    self.sprinting = True
                self.player.v *= 3
                self.player.strafev *= 3
            #if (keyCode == pygame.K_LCTRL): self.countdown = 0  #debugging: instantly end countdown
        if self.state == self.SPLASH:
            if (keyCode == pygame.K_a):
                self.menuPlayer.delta = -.1
            if (keyCode == pygame.K_d):
                self.menuPlayer.delta = .1
            if (keyCode == pygame.K_SPACE or keyCode == pygame.K_RETURN):
                if self.menuPlayer.menuLeft:
                    self.menuRoom.setValue(3,6,(1,10))  #open closed door after having played the game from the menu once
                    self.initCampaign()                 #creates a new campaign
                    self.initGame(self.mapList[0][0],   #initializes the first map of the campaign
                                  self.mapList[0][1],
                                  self.mapList[0][2],
                                  self.mapList[0][3])
                    pygame.mixer.Channel(self.sfx).play(self.dooropen)  
                    time.sleep(pygame.mixer.Sound.get_length(self.dooropen))    #play door open effect as the player loads in
                    self.state = self.GAME
                else:
                    pygame.mixer.Channel(self.sfx).play(self.doorclose) #play door close effect as the user quits
                    time.sleep(pygame.mixer.Sound.get_length(self.doorclose))
                    self.playing = False
            if (keyCode == pygame.K_h):                 #displays help screen
                self.hPressed = True
                self.state = self.HELP
        if self.state == self.END:                      #end screen displays win/loss based on boolean 'escaped'
            if (keyCode == pygame.K_SPACE or keyCode == pygame.K_RETURN):
                if self.hasEscaped:
                    self.currMap += 1                   #if win, space/return transition to next map
                    if self.currMap < len(self.mapList):
                        self.initGame(self.mapList[self.currMap][0],
                                      self.mapList[self.currMap][1],
                                      self.mapList[self.currMap][2],
                                      self.mapList[self.currMap][3])
                        self.state = self.GAME
                    else: self.state = self.SPLASH      #if lose, return to menu
                else:
                    self.state = self.SPLASH
        if self.state == self.HELP and self.hPressed == False:
            self.state = self.SPLASH                    #press any key to return from help

    def keyReleased(self, keyCode, modifier):
        if self.state == self.GAME:
            if (keyCode == pygame.K_w): 
                self.player.v = 0                       #stop forward momentum
            if (keyCode == pygame.K_s): 
                self.player.v = 0                       #stop backward momentum
            if (keyCode == pygame.K_a): 
                self.player.strafev = 0                 #stop left strafe momentum
            if (keyCode == pygame.K_d): 
                self.player.strafev = 0                 #stop right strafe momentum
            if (keyCode == pygame.K_LSHIFT):            #slow down all movements by sprinting values
                self.player.v /= 3
                self.player.strafev /= 3
                self.sprinting = False
                if self.inMotion:                       #play appropriate walking/running sound effects
                    pygame.mixer.Channel(self.movement).stop()
                    pygame.mixer.Channel(self.movement).play(self.walking, -1)
                else:
                    pygame.mixer.Channel(self.movement).stop()
        if self.state == self.SPLASH or self.state == self.HELP:    #reset help screen flag bool
            if (keyCode == pygame.K_h):
                self.hPressed = False

    def timerFired(self, dt):
        if self.state == self.GAME:
            if self.player.v ==0 and self.player.strafev == 0:
                pygame.mixer.Channel(self.movement).stop()          #stop walking/running sounds if player isn't moving
                self.inMotion = False
                self.sprinting = False
            self.player.walk(self.gameMap)                          #player is always walking, even if velocity is zero
            if self.player.v != 0:
                self.gameMap.updateKey(self.player)                 #if player is moving, check for keys and unlocked doors nearby
                if self.player.hasKey and self.player.keyTone:
                    pygame.mixer.Channel(self.sfx).play(self.dooropen)
                    self.player.keyTone = False
                if self.gameMap.checkEscape(self.player):
                    self.hasEscaped = True
                    pygame.mixer.Channel(self.movement).stop()
                    self.state = self.END            
        if self.state == self.SPLASH:                               #menu is rotation locked between 0 and 90 degrees, rotates by delta between the two
            if self.menuPlayer.delta < 0 and self.menuPlayer.direction >= 0 and self.menuPlayer.menuLeft == False:
                self.menuPlayer.menuRotate(self.menuPlayer.delta)
                if self.menuPlayer.direction <= 0.2:
                    self.menuPlayer.delta = 0
                    self.menuPlayer.direction = 0
                    self.menuPlayer.menuLeft = True

            elif self.menuPlayer.delta > 0 and self.menuPlayer.direction <= math.pi/2 and self.menuPlayer.menuLeft == True:
                self.menuPlayer.menuRotate(self.menuPlayer.delta)
                if self.menuPlayer.direction >= math.pi/2:
                    self.menuPlayer.direction = math.pi/2
                    self.menuPlayer.delta = 0
                    self.menuPlayer.menuLeft = False

    def redrawAll(self, screen):                                    #draws everything. The real MVP of this program.
        if self.state == self.GAME:
            self.camera.render(self.player, self.gameMap)           #render game
            self.drawCountdown()                                    #draw timer as HUD
            if self.player.hasKey:
                self.drawKey()                                      #key in inventory once aquired
        if self.state == self.SPLASH:
            self.drawSplashScreen()
        if self.state == self.END:
            self.drawEndScreen(self.hasEscaped)                     #escaped determines win/loss
        if self.state == self.HELP:
            self.drawHelpScreen()

    def gameTimer(self):                                            #called by self-made time even to decrement countdown timer
        if self.state == self.GAME:
            self.countdown-=.01
            if self.countdown <= 0:
                self.countdown = 0
                self.hasEscaped = False                             #lose if countdown hits 0
                pygame.mixer.Channel(self.movement).stop()          #stop movement sounds once time is up
                self.state = self.END

    def drawCountdown(self):                                        #countdown timer displays 'MM:SS' when > 1min else 'S'
        currTime = "%d:%0.2d" % (self.countdown//60, int(self.countdown % 60)) if self.countdown >= 60 else "%d" % int(self.countdown)
        pygame.font.init()
        font = pygame.font.SysFont("Goudy Old Style", 100)          #boy, do I love this font
        timer = font.render(currTime, True, (255,255,255))
        self.timerWidth, self.timerHeight = timer.get_size()
        self.screen.blit(timer,(0,0))

    def drawKey(self):                                              #draw the key in the inventory
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        rel_path = "resources\images"
        full_images_dir_path = os.path.join(script_dir, rel_path)
        key = pygame.image.load(os.path.join(full_images_dir_path, "hasKey.png")).convert_alpha()
        scaled = pygame.transform.scale(key, (self.timerHeight, self.timerHeight))
        self.screen.blit(scaled, (0, self.timerHeight))

    def drawSplashScreen(self):                                     #draws pngs, text, menu room
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        rel_path = "resources\images"
        full_images_dir_path = os.path.join(script_dir, rel_path)
        self.menuCamera.render(self.menuPlayer, self.menuRoom)
        title = pygame.image.load(os.path.join(full_images_dir_path, "title.png")).convert_alpha()
        titleW, titleH = title.get_size()
        self.screen.blit(title,(self.width/2-titleW/2, self.height/5-titleH/2+50))
        instrFont = pygame.font.SysFont("Goudy Old Style", 35)
        instrText = "Use 'A' and 'D' to navigate. Press 'H' for help. Press Space or Enter to select."
        instr = instrFont.render(instrText, True, (255,255,255))
        instrW, instrH = instrFont.size(instrText)
        self.screen.blit(instr,(self.width/2-instrW/2, 6*self.height/7-instrH/2))

    def drawEndScreen(self, escaped):                               #draws win/lose screen
        self.screen.fill((0,0,0))
        titleFont = pygame.font.SysFont("Goudy Old Style", 120, True)
        titleText = "Escaped Level %d of %d" %(self.currMap+1, len(self.mapList)) if escaped else "Trapped on Level %d of %d" %(self.currMap+1, len(self.mapList))
        title = titleFont.render(titleText, True, (150,0,0))
        titleW, titleH = titleFont.size(titleText)
        self.screen.blit(title,(self.width/2-titleW/2, self.height/8-titleH/2))
        timerFont = pygame.font.SysFont("Goudy Old Style", 100)
        timerText = "%d seconds remained" %self.countdown if self.countdown > 0 else "Your time ran out."
        timer = timerFont.render(timerText, True, (255,255,255))
        timerW, timerH = timerFont.size(timerText)
        self.screen.blit(timer,(self.width/2-timerW/2, self.height/2-timerH/2))
        infoFont = pygame.font.SysFont("Goudy Old Style", 100)
        complexity = self.mapList[self.currMap][2]
        if complexity <= 1: difficulty = "Novice"                   #difficulty adjectives by complexity/number of subdivisions per quadrant
        elif complexity <= 2: difficulty = "Moderate"
        elif complexity <= 3: difficulty = "Difficult"
        elif complexity > 3: difficulty = "Insane"
        infoText = "%s %d by %d Labyrinth" %(difficulty,            #i.e. Insane 20 by 20 Labyrinth, 7 by 7 Open Chamber...
                                             self.mapList[self.currMap][0], 
                                             self.mapList[self.currMap][1]
        ) if complexity > 0 else "%d by %d Open Chamber" %(self.mapList[self.currMap][0],
                                                        self.mapList[self.currMap][1])
        info = infoFont.render(infoText, True, (255,255,255))
        infoW, infoH = infoFont.size(infoText)
        self.screen.blit(info,(self.width/2-infoW/2, self.height/3-infoH/2))
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        rel_path = "resources\images"
        full_images_dir_path = os.path.join(script_dir, rel_path)
        key = pygame.image.load(os.path.join(full_images_dir_path, "hasKey.png")).convert_alpha()
        scaled = pygame.transform.scale(key, (250, 250))
        keyW, keyH = key.get_size()
        if escaped:                                                 #show key on win screen
            self.screen.blit(scaled, (self.width/4-keyW/2, 5*self.height/6-keyH/2))
        subtitleFont = pygame.font.SysFont("Goudy Old Style", 50)
        instrText = "Press Space or Enter to proceed."
        instr = subtitleFont.render(instrText, True, (255,255,255))
        instrW, instrH = subtitleFont.size(instrText)
        self.screen.blit(instr,(self.width-instrW, self.height-instrH))

    def drawHelpScreen(self):                                       #loads my wonderfully helpful PNG of instructions
        rel_path = "resources\images"
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        full_images_dir_path = os.path.join(script_dir, rel_path)
        self.menuCamera.render(self.menuPlayer, self.menuRoom)
        help = pygame.image.load(os.path.join(full_images_dir_path, "intstructions.png")).convert_alpha()
        helpW, helpH = help.get_size()
        self.screen.blit(help,(self.width/2-helpW/2,0))
        instrFont = pygame.font.SysFont("Goudy Old Style", 35)
        instrText = "Press any key to return."
        instr = instrFont.render(instrText, True, (255,255,255))
        instrW, instrH = instrFont.size(instrText)
        self.screen.blit(instr,(self.width-instrW, self.height-instrH))

    def isKeyPressed(self, key):
        ''' return whether a specific key is being held '''
        return self._keys.get(key, False)

    def __init__(self, width=1280, height=720, fps=60, title="Labyrinthine"):
        self.width = width
        self.height = height
        self.fps = fps
        self.fpsCounter = 0
        self.title = title
        self.bgColor = (255, 255, 255)
        pygame.init()

    def run(self):

        clock = pygame.time.Clock()
        screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        # set the title of the window
        #pygame.display.set_caption("%f" %self.fpsCounter)
        pygame.display.set_caption(self.title)
        pygame.mouse.set_visible(False)

        # stores all the keys currently being held down
        self._keys = dict()

        # call game-specific initialization
        self.init()
        self.playing = True
        while self.playing:
            time = clock.tick(self.fps)
            self.fpsCounter = clock.get_fps()
            pygame.display.set_caption("%f" %self.fpsCounter)
            self.timerFired(time)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.mousePressed(*(event.pos))
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouseReleased(*(event.pos))
                elif (event.type == pygame.MOUSEMOTION and
                      event.buttons == (0, 0, 0)):
                    self.mouseMotion(*(event.pos))
                elif (event.type == pygame.MOUSEMOTION and
                      event.buttons[0] == 1):
                    self.mouseDrag(*(event.pos))
                elif (event.type == self.TIMEREVENT): #self-made timer event
                    self.gameTimer()
                elif event.type == pygame.KEYDOWN:
                    self._keys[event.key] = True
                    self.keyPressed(event.key, event.mod)
                elif event.type == pygame.KEYUP:
                    self._keys[event.key] = False
                    self.keyReleased(event.key, event.mod)
                elif event.type == pygame.QUIT:
                    self.playing = False
            screen.fill(self.bgColor)
            self.redrawAll(screen)
            pygame.display.flip()

        pygame.quit()


def main():
    game = PygameGame()
    game.run()

if __name__ == '__main__':
    main()