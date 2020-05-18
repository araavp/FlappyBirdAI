# Imports
import pygame
import neat
import time
import os
import random
import pickle
pygame.font.init()

# Game width and height
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 800

# Records the generations of neural networks
GENERATION = 0

# Records number of birds left in the generation
NUM_BIRDS = 0

# Loads in all the images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png"))),
            pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "base.png")))
BACKGROUND_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bg.png")))

# Loads font used in the game
STAT_FONT = pygame.font.SysFont("comicsans", 50)


# Bird Class
class Bird:
    # Gets the image of the bird
    IMGS = BIRD_IMGS

    # Rotates the bird to look like its jumping
    MAX_ROTATION = 25
    ROTATION_VELOCITY = 20

    # How long the animation will last
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        # Position of the bird
        self.x = x
        self.y = y

        # Used to make it look like the bird is flying
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0

        # How much it has jumped up
        self.height = self.y

        # Rotates through the images of the bird to animate it so it looks like its flying
        self.image_count = 0
        self.image = self.IMGS[0]

    # For the bird to tilt when jumping
    def jump(self):
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    # Vertical movement
    def move(self):
        self.tick_count += 1

        # Position variable
        d = (self.velocity * self.tick_count) + (1.5 * self.tick_count**2)

        # Prevents the bird from falling too fast
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        # Adjust position of bird
        self.y = self.y + d

        # Adjusts the tilt for the bird for vertical direction
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            # Prevents the bird from tilting too much
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    # Drawing the bird
    def draw(self, window):
        self.image_count += 1

        # Different images of the bird flapping wings to make it look realistic
        if self.image_count < self.ANIMATION_TIME:
            self.image = self.IMGS[0]
        elif self.image_count < self.ANIMATION_TIME * 2:
            self.image = self.IMGS[1]
        elif self.image_count < self.ANIMATION_TIME * 3:
            self.image = self.IMGS[2]
        elif self.image_count < self.ANIMATION_TIME * 4:
            self.image = self.IMGS[1]
        elif self.image_count == self.ANIMATION_TIME * 4 + 1:
            self.image = self.IMGS[0]
            self.image_count = 0

        if self.tilt <= -80:
            self.image = self.IMGS[1]
            self.image_count = self.ANIMATION_TIME * 2

        # Rotating the image to make it look like the bird is flying
        rotated_image = pygame.transform.rotate(self.image, self.tilt)
        new_rect = rotated_image.get_rect(center=self.image.get_rect(topleft= (self.x, self.y)).center)

        # Draws the rotated bird in the window
        window.blit(rotated_image, new_rect.topleft)

    # Finds the pixels of the bird (to later use during collision)
    def get_mask(self):
        return pygame.mask.from_surface(self.image)


# Pipe Class
class Pipe:
    # Defines the gap between the top and bottom pipe
    GAP = 200

    # Speed at which the pipe moves to the left in the game
    ## Should be the same as the other moving parts of the window
    VELOCITY = 5

    def __init__(self, x):
        # Position of the pipe
        self.x = x

        # Where the pipe rests in the y position
        self.height = 0

        # Top and bottom of pipe
        self.top = 0
        self.bottom = 0

        # There are two pipes for the bird to pass through
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        # Becomes true if the bird has passed the pipe
        self.passed = False

        # Sets the height of the pipe
        self.set_height()

    # Set a random position for the top and bottom pipes
    def set_height(self):
        # Gets a random height so the pipes are not in the same position every time
        self.height = random.randrange(50, 450)

        # Sets the top and bottom pipe based on the height
        ## Maintains a constant GAP between the top and bottom pipe
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # The pipes will move in the horizontal direction because the bird remains constant in place
    def move(self):
        # Moves the pipe to the left based on a constant velocity
        self.x -= self.VELOCITY

    # Draws the pipes
    def draw(self, win):
        # Draws the top and bottom pipes in the window
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Determines whether there has been a collision between the bird and either pipe
    def collide(self, bird, win):
        # Gets the pixels (mask) of the bird
        bird_mask = bird.get_mask()

        # Gets the pixels (mask) of the top and bottom pipe
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # See how far the bird is from the top and bottom pipes
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Checks to see if any of the pixels overlap and whether there has been a collision
        ## If no collision: returns none
        top_point = bird_mask.overlap(top_mask, top_offset)
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)

        # Returns whether or not there is a collision between the bird and one of the pipes
        if top_point or bottom_point:
            return True
        return False


# Base Class
class Base:
    # Speed at which the pipe moves to the left in the game
    ## Should be the same as the other moving parts of the window
    VELOCITY = 5

    # Gets the width of the base image
    WIDTH = BASE_IMG.get_width()

    # Gets the image of the base
    IMAGE = BASE_IMG

    def __init__(self, y):
        # Y position of the image
        self.y = y

        # Position of the left of the image
        self.x1 = 0

        # Position of the right of the image
        self.x2 = self.WIDTH

    # The base moves at the same speed as the pipe
    def move(self):
        # Moves the base based on the constant velocity
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        # Makes sure that the base is always visible on screen and there are no blank spaces
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        # Makes sure that the base is always visible on screen and there are no blank spaces
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # Draws the base in the game
    def draw(self, window):
        window.blit(self.IMAGE, (self.x1, self.y))
        window.blit(self.IMAGE, (self.x2, self.y))


# Background Class
class Background:
    # Speed at which the pipe moves to the left in the game
    ## Should be the same as the other moving parts of the window
    VELOCITY = 5

    # Gets the width of the background image
    WIDTH = BACKGROUND_IMG.get_width()

    # Gets the width of the background image
    IMAGE = BACKGROUND_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    # The background moves at the same speed as the pipe
    def move(self):
        # Moves the background based on the constant velocity
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        # Makes sure that the background is always visible on screen and there are no blank spaces
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        # Makes sure that the background is always visible on screen and there are no blank spaces
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # Draws the background in the game
    def draw(self, window):
        window.blit(self.IMAGE, (self.x1, self.y))
        window.blit(self.IMAGE, (self.x2, self.y))


class Score:
    

# Draws all the images in the window
def draw_window(window, birds, pipes, base, background, score, generation, num_birds):
    # Draws the background on the window
    background.draw(window)

    # Draws all the pipes on the window
    for pipe in pipes:
        pipe.draw(window)

    # Has a score counter that increments each time the bird passes through a pipe
    score_counter = STAT_FONT.render("Score: {0}".format(str(score)), 1, (255,255,255))

    # Displays the score counter in the top right
    window.blit(score_counter, (WINDOW_WIDTH - 10 - score_counter.get_width(), 10))

    # Has a generation counter that increments once all the birds of the previous generation died and the birds of the
    # new generation spawn
    generation_counter = STAT_FONT.render("Generation: {0}".format(str(generation)), 1, (255,255,255))

    # Displays the generation counter in the top left
    window.blit(generation_counter, (10, 10))

    # Has a bird counter that shows the number of remaining birds in the given generation
    bird_counter = STAT_FONT.render("Birds Left: {0}".format(str(num_birds)), 1, (255,255,255))

    # Displays the bird counter in the top left, under the generation counter
    window.blit(bird_counter, (10, 50))

    # Draws the base on the window
    base.draw(window)

    # Draws all the birder on the window
    for bird in birds:
        bird.draw(window)

    # Updates display with drawn images
    pygame.display.update()


def main(genomes, config):
    # Global variables to count the number of generations and the number of birds left
    global GENERATION, NUM_BIRDS

    # Generation increases by one each time all the birds in the previous generation die
    GENERATION += 1

    # Defines position of the window and background image
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    background = Background(0)

    # Initialize variables needed for NEAT
    neural_networks = []
    genome_birds = []
    birds = []

    # Loops through the genomes
    for _, genome in genomes:
        # Creates a new neural network for each bird
        neural_network = neat.nn.FeedForwardNetwork.create(genome, config)

        # Adds the neural network to a list of neural networks, creates and appends a new bird
        neural_networks.append(neural_network)
        birds.append(Bird(230, 350))

        # Fitness for each genome starts off as zero
        genome.fitness = 0

        # Append genome to list of genomes
        genome_birds.append(genome)

    # Finds number of total birds in the generation
    NUM_BIRDS = len(birds)

    # Defines position of the base and pipes images
    base = Base(730)
    pipes = [Pipe(600)]

    # Starts the score as 0 at the beginning of the game
    score = 0

    # Starts timer
    clock = pygame.time.Clock()

    # Runs the game given run == True and there are birds alive
    run = True
    while run and len(birds) > 0:
        # 30 frames per second
        clock.tick(30)

        # Allows for the program to quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                # Quits the game and program
                pygame.quit()
                quit()

        # Which pipe to consider
        pipe_index = 0

        # Decides which pipe the bird should look at to train the neural network
        ## Depends on whether the bird has passed a pipe (there will be at most 2 pipes on the screen at one time)
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_index = 1
        else:
            # Quits the program if there are no birds alive
            run = False
            break

        # Loops through all the birds
        for x, bird in enumerate(birds):
            # Tells the bird to move
            bird.move()

            # Rewards the bird for staying alive
            genome_birds[x].fitness += 0.1

            # Runs the bird, distance from the bird to the top pipe, distance from the bird to the bottom pipe through
            # the neural network
            ## The output is the y value of the inverse tan function
            output = neural_networks[x].activate((bird.y, abs(bird.y - pipes[pipe_index].height),
                                                  abs(bird.y - pipes[pipe_index].bottom)))

            # To be sure, we jump only when the output is greater than 0.5 (from -1 to 1)
            if output[0] > 0.5:
                bird.jump()

        # Variable for whether or not to present a new pipe on the screen
        add_pipe = False

        # Variable to remove the pipe once it has exited the window view
        remove = []

        # Loops through all the pipes to check collision
        for pipe in pipes:
            # Loops through all the birds to check collision
            for x, bird in enumerate(birds):

                # Checks to see if the bird and pipe collide
                if pipe.collide(bird, window):

                    # Punishes the neural network for crashing into the pipe
                    genome_birds[x].fitness -= 1

                    # Removes the bird, respective genome, respective neural network because the bird has died
                    birds.pop(x)
                    neural_networks.pop(x)
                    genome_birds.pop(x)

                    # Updates bird counter with how many birds are left
                    NUM_BIRDS -= 1

                # Updates that birds have passed the pipe and creates a new pipe on the window
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # Removes the pipe if it has exited the screen view
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)

            # Moves the pipe to the left
            pipe.move()

        # Effect of bird passing through the pipe and surviving
        if add_pipe:
            # Updates score counter
            score += 1

            # Loops through birds that have passed through the pipe successfully
            for gb in genome_birds:
                # Rewards the birds for passing through the pipe successfully
                gb.fitness += 5

            # Adds a new pipe at a position on the window
            pipes.append(Pipe(600))

        # Removes the pipe that has exited the screen window
        for pipe in remove:
            pipes.remove(pipe)

        # Loops through all the birds to check if they have exited the screen view through the bottom or top
        ## It has died if it flies outside the screen view (either through the top or bottom)
        for x, bird in enumerate(birds):
            # Checks ot see if the bird is above or below the screen view
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                # Removes the bird, respective genome, respective neural network because the bird has died
                birds.pop(x)
                neural_networks.pop(x)
                genome_birds.pop(x)

                # Updates bird counter with how many birds are left
                NUM_BIRDS -= 1

        # Moves the base and background to the left
        base.move()
        background.move()

        # Draws all the objects in the screen view
        draw_window(window, birds, pipes, base, background, score, GENERATION, NUM_BIRDS)

        # Stops the game if the score has surpassed 30 because the neural network has created a perfect bird
        if score > 30:
            # Saves the neural network that performed the best so the user does not have to train the model again
            pickle.dump(neural_networks[0], open("best_flappybird.pickle", "wb"))
            break


# Runs the NEAT file
def run(config_file):
    # Defines config based on the parameters used in text file
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_file)

    # Defines population from config file
    population = neat.Population(config)

    # Adds some stats that console prints out during training model
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())

    # Gets the best genome from the population up to 30 generations
    winner = population.run(main, 30)

    # Prints out the best genome
    print("Best genome is: {0}".format(winner))


if __name__ == "__main__":
    # Finds the directory path so the NEAT model can run
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")

    # Runs the file after it has been located
    run(config_path)
