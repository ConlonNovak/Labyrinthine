## Introduction
For my Fundamentals of Programming and Computer Science (15-112) term project, I created a maze exploration game where the player must navigate a randomly generated labyrinth of walls, find the key to unlock the single escape door, and work against the clock to escape with their lives. To do this, I created a ray-casting program that takes a 2D list of wall placements and uses image textures for the walls and turns them into 3D environments by “propping up” these flat objects at different distances from the player, simulated by drawing larger or smaller slices of the textures on the screen. PyGame allows textures to sliced (blitted) onto the screen in smaller parts, in my program represented by rays. Ray are “cast” from the player/camera object (a specific point) at a certain angle and return the location and distance of the first object they encounter. Using the distance to determine the size of the object slice on the screen and the screen resolution to determine the width of the slice of the object, the scene can be drawn in simulated 3D (termed 2.5D) as a collection of textured rectangles that approximate how the player would actually perceive the world. 

## Inspiration and Design
Inspired by Greek myths, Labyrinthine is a twisting maze of identical, confusing corridors determined to keep its sacrificed victims from escaping. You’ve been banished to the seemingly endless underground maze as a sacrifice to the gods, and now you’re running out of time. You need to escape, but the exit will only unlock itself if you acquire the key hidden elsewhere. Win states include exiting the maze and completing a campaign (a series of 10 increasingly challenging randomly generated but always solvable mazes). The fail state is running out of time and being trapped in the maze forever. A results screen after ending the level displays the current level in the campaign, the time of the current run, the win/fail status, the complexity of the previous maze, and the ability to either proceed to the next maze in the game (to continue the campaign if you escaped) or return to the menu (you didn’t escape the current level).

## How it works
The mazes are recursively generated using a “wall adding algorithm,” where a level is first generated to be a chamber, an open room with bordering walls on all sides (maze complexity 0). Then the algorithm adds a random row and a random column of walls, resulting in four distinct quadrants of the chamber. Three of these walls will randomly have protected hallways carved through them in order to allow the player to navigate it that cannot be overwritten by future walls. This is a maze with complexity 1. This algorithm can be called to an arbitrary depth, limited only by the size of the original chamber that calls it. These mazes can be solved from any two points because of the nature of the figure – the interior of the shape is one continuous space without pockets or entrapments because of the use of the three hallways through the dividing walls.

## What I learned
Early design choices had much larger repercussions than I had believed at the time. For example, with the way I designed the game engine, drawing enemies, items, and other entities in the world proved to be much more difficult than I had foreseen at the time. Optimization issues plagued early builds of the project due to my initial unfamiliarity with Visual Studio, most of which were solved by a few simple tweaks to how the program was running my code, bumping my game's frame rate up from a shaky 5-15 to a solid 45-60 FPS. PyGame was also not optimized for raycasting, instead faring better with moving blocks of 2D pixels and sprites that don't need to be redrawn tens of times per second. Also, it's tough to plan for unexpected version releases - Pygame upgraded from 1.9.1 to 1.9.2, which added pip as well as Python 3 support a week before the project was due and several weeks after I had a nightmarish time trying to install the package properly on Windows.

## What's next?
With my first foray into game development complete, I'm looking forward to applying my newfound PyGame skills to a more traditional 2D game in the future. While building my own game engine was certainly revealing, I'm happy to leave most of that work to software like Unity in the future.
