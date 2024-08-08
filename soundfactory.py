import math
import gensound
from gensound.effects import Stretch
import pygame as pg

class Sprites:
    conveyor = pg.image.load('include/conveyor.png')
    sine_generator = pg.image.load('include/sinegen.png')
    sawtooth_generator = pg.image.load('include/sawtoothgen.png')
    triangle_generator = pg.image.load('include/trianglegen.png')
    square_generator = pg.image.load('include/squaregen.png')
    destroy = pg.image.load('include/destroy.png')
    output = pg.image.load('include/output.png')
    adsr = pg.image.load('include/adsr.png')
    delay = pg.image.load('include/delay.png')
    splitpath = pg.image.load('include/splitpath.png')
    squish = pg.image.load('include/squish.png')
    stretch = pg.image.load('include/stretch.png')

class Compass:
    NORTH = (0,-1)
    EAST = (1,0)
    SOUTH = (0,1)
    WEST = (-1,0)
    STATIONARY = (0,0)
    def rotated_clockwise(direction):
        if direction == Compass.NORTH:
            return Compass.EAST
        elif direction == Compass.EAST:
            return Compass.SOUTH
        elif direction == Compass.SOUTH:
            return Compass.WEST
        elif direction == Compass.WEST:
            return Compass.NORTH
    def rotated_anticlockwise(direction):
        if direction == Compass.NORTH:
            return Compass.WEST
        elif direction == Compass.WEST:
            return Compass.SOUTH
        elif direction == Compass.SOUTH:
            return Compass.EAST
        elif direction == Compass.EAST:
            return Compass.NORTH

class FactoryFloor:
    def __init__(self):
        self.components = {}
        self.soundchunks = {}
        self.chunk_length = 1 # length in seconds of a chunk
        self.viewscale = 50
        self.viewlocation = (0,0)
    def create_component(self, kind, location, direction):
        self.components[location] = kind(self, location, direction)
    def create_soundchunk(self, signal, location):
        self.soundchunks[location] = SoundChunk(self, location, signal)
    def floorlocation_to_screenlocation(self, position):
        return ((position[0]-self.viewlocation[0])*self.viewscale, (position[1]-self.viewlocation[1])*self.viewscale)
    def draw(self, screen, scale, topleft):
        w,h = screen.get_size()
        pg.draw.rect(screen, (200,200,200), (0,0,w,h))
        for x in range(math.ceil(w/scale)):
            for y in range(math.ceil(h/scale)):
                x += topleft[0]
                y += topleft[1]
                if (x,y) in self.components and self.components[(x,y)].opentop:
                    self.components[(x,y)].draw(screen)
        for x in range(math.ceil(w/scale)):
            for y in range(math.ceil(h/scale)):
                x += topleft[0]
                y += topleft[1]
                if (x,y) in self.soundchunks:
                    self.soundchunks[(x,y)].draw(screen)
        for x in range(math.ceil(w/scale)):
            for y in range(math.ceil(h/scale)):
                x += topleft[0]
                y += topleft[1]
                if (x,y) in self.components and not self.components[(x,y)].opentop:
                    self.components[(x,y)].draw(screen)
    def step(self):
        for component in self.components.values():
            component.operate()
        for soundchunk in list(self.soundchunks.values()):
            soundchunk.move()
        for soundchunk in self.soundchunks.values():
            soundchunk.moved_this_tick = False
    def move_soundchunk(self, location, direction):
        if location in self.soundchunks:
            chunk = self.soundchunks.pop(location)
            new_location = (location[0] + direction[0], location[1] + direction[1])
            self.soundchunks[new_location] = chunk
            self.soundchunks[new_location].location = new_location
    def remove_component(self, location):
        if location in self.components:
            self.components.pop(location)
        if location in self.soundchunks:
            self.soundchunks.pop(location)


class FactoryComponent:
    opentop = False
    opengates = True
    characteristic_colour = (255,255,255)
    def __init__(self, factory, location, direction):
        self.factory = factory
        self.location = location
        self.direction = direction
    def rotate(self):
        self.direction = Compass.rotated_clockwise(self.direction)
    def stamp_colour(self, chunk):
        chunk.colour = ((chunk.colour[0]+self.characteristic_colour[0])/2,
                        (chunk.colour[1]+self.characteristic_colour[1])/2,
                        (chunk.colour[2]+self.characteristic_colour[2])/2)
    def draw(self, screen):
        location = self.factory.floorlocation_to_screenlocation(self.location)
        if self.direction == Compass.NORTH:
            screen.blit(pg.transform.scale(self.sprite, (self.factory.viewscale, self.factory.viewscale)), location)
        elif self.direction == Compass.SOUTH:
            screen.blit(pg.transform.scale(pg.transform.rotate(self.sprite, 180), (self.factory.viewscale, self.factory.viewscale)), location)
        elif self.direction == Compass.EAST:
            screen.blit(pg.transform.scale(pg.transform.rotate(self.sprite, 270), (self.factory.viewscale, self.factory.viewscale)), location)
        elif self.direction == Compass.WEST:
            screen.blit(pg.transform.scale(pg.transform.rotate(self.sprite, 90), (self.factory.viewscale, self.factory.viewscale)), location)

class Conveyor(FactoryComponent):
    sprite = Sprites.conveyor
    opentop = True
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks[self.location].velocity = self.direction

class SineGenerator(FactoryComponent):
    sprite = Sprites.sine_generator
    characteristic_colour = (0,0,255)
    def operate(self):
        if self.location not in self.factory.soundchunks:
            self.factory.create_soundchunk(gensound.Sine(frequency=440, duration=1e3 * self.factory.chunk_length), self.location)
            self.stamp_colour(self.factory.soundchunks[self.location])
        self.factory.soundchunks[self.location].velocity = self.direction
class SquareGenerator(FactoryComponent):
    sprite = Sprites.square_generator
    characteristic_colour = (0,255,0)
    def operate(self):
        if self.location not in self.factory.soundchunks:
            self.factory.create_soundchunk(gensound.Square(frequency=440, duration=1e3 * self.factory.chunk_length), self.location)
            self.stamp_colour(self.factory.soundchunks[self.location])
        self.factory.soundchunks[self.location].velocity = self.direction
class SawtoothGenerator(FactoryComponent):
    sprite = Sprites.sawtooth_generator
    characteristic_colour = (255,0,0)
    def operate(self):
        if self.location not in self.factory.soundchunks:
            self.factory.create_soundchunk(gensound.Sawtooth(frequency=440, duration=1e3 * self.factory.chunk_length), self.location)
            self.stamp_colour(self.factory.soundchunks[self.location])
        self.factory.soundchunks[self.location].velocity = self.direction
class TriangleGenerator(FactoryComponent):
    sprite = Sprites.triangle_generator
    characteristic_colour = (255,255,0)
    def operate(self):
        if self.location not in self.factory.soundchunks:
            self.factory.create_soundchunk(gensound.Triangle(frequency=440, duration=1e3 * self.factory.chunk_length), self.location)
            self.stamp_colour(self.factory.soundchunks[self.location])
        self.factory.soundchunks[self.location].velocity = self.direction


class ADSR(FactoryComponent):
    sprite = Sprites.adsr
    characteristic_colour = (255,0,255)
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks[self.location].signal *= gensound.transforms.ADSR(attack = 0.2e3  * self.factory.chunk_length, decay = 0.2e3  * self.factory.chunk_length, sustain = 0.75, release = 0.2e3  * self.factory.chunk_length)
            self.factory.soundchunks[self.location].velocity = self.direction
            self.stamp_colour(self.factory.soundchunks[self.location])

class Output(FactoryComponent):
    sprite = Sprites.output
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction = Compass.NORTH
    def operate(self):
        if self.location in self.factory.soundchunks:
            chunk = self.factory.soundchunks.pop(self.location)
            chunk.signal.play()

class Destroyer(FactoryComponent):
    sprite = Sprites.destroy
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks.pop(self.location)

class Squisher(FactoryComponent):
    sprite = Sprites.squish
    stored_chunk = None
    def operate(self):
        if self.location in self.factory.soundchunks:
            if self.stored_chunk is not None:
                self.characteristic_colour = self.factory.soundchunks[self.location].colour
                self.factory.create_soundchunk((self.stored_chunk.signal * Stretch(rate=2)) | (self.factory.soundchunks[self.location].signal * Stretch(rate=2)),
                                               self.location)
                self.factory.soundchunks[self.location].colour = self.stored_chunk.colour
                self.stamp_colour(self.factory.soundchunks[self.location])
                self.factory.soundchunks[self.location].velocity = self.direction
                self.stored_chunk = None
            else:
                self.stored_chunk = self.factory.soundchunks.pop(self.location)

class Stretcher(FactoryComponent):
    sprite = Sprites.stretch
    stored_chunk = None
    characteristic_colour = (255,255,255)
    def operate(self):
        if self.stored_chunk is not None:
            self.factory.create_soundchunk((self.stored_chunk.signal * Stretch(rate=0.5))[1e3 * self.factory.chunk_length:], self.location)
            self.factory.soundchunks[self.location].colour = self.stored_chunk.colour
            self.stored_chunk = None
            self.opengates = True
        elif self.location in self.factory.soundchunks:
            self.stored_chunk = self.factory.soundchunks.pop(self.location)
            self.opengates = False
            self.factory.create_soundchunk((self.stored_chunk.signal * Stretch(rate=0.5))[:1e3 * self.factory.chunk_length], self.location)
            self.factory.soundchunks[self.location].colour = self.stored_chunk.colour
        if self.location in self.factory.soundchunks:
            self.stamp_colour(self.factory.soundchunks[self.location])
            self.factory.soundchunks[self.location].velocity = self.direction

class Delay(FactoryComponent):
    sprite = Sprites.delay
    def operate(self):
        if not self.opengates:
            self.opengates = True
            self.factory.soundchunks[self.location].velocity = self.direction
        elif self.location in self.factory.soundchunks:
            self.opengates = False

class SplitPath(FactoryComponent):
    sprite = Sprites.splitpath
    tick = True
    def operate(self):
        if self.location in self.factory.soundchunks:
            if self.tick:
                self.factory.soundchunks[self.location].velocity = Compass.rotated_clockwise(self.direction)
                self.tick = False
            else:
                self.factory.soundchunks[self.location].velocity = Compass.rotated_anticlockwise(self.direction)
                self.tick = True

class SoundChunk:
    def __init__(self, factory, location, signal):
        self.factory = factory
        self.location = location
        self.signal = signal
        self.moved_this_tick = False
        self.velocity = Compass.STATIONARY
        self.colour = (0,0,0)
        self.moved_at = 0
        self.previous_location = location
    def move(self):
        if self.moved_this_tick:
            return True
        else:
            self.moved_this_tick = True
            target_space = (self.location[0]+self.velocity[0],self.location[1]+self.velocity[1])
            if target_space in self.factory.soundchunks:
                self.factory.soundchunks[target_space].move()
            if target_space not in self.factory.soundchunks and target_space in self.factory.components and self.factory.components[target_space].opengates: # still, ie. the one that was already there isn't blocked and has moved out the way, and the component isn't blocking input
                self.moved_at = pg.time.get_ticks()
                self.previous_location = self.location
                self.factory.move_soundchunk(self.location, self.velocity)
            self.velocity = Compass.STATIONARY
    def draw(self, screen):
        progress = min(1, (pg.time.get_ticks() - self.moved_at) / ((self.factory.chunk_length*1000) / 2))
        moving_location = ((self.location[0]*progress) + (self.previous_location[0]*(1-progress)),
                           (self.location[1]*progress) + (self.previous_location[1]*(1-progress)))
        draw_location = self.factory.floorlocation_to_screenlocation(moving_location)
        pg.draw.rect(screen, self.colour, (draw_location[0]+(self.factory.viewscale//10), draw_location[1]+(self.factory.viewscale//10),
                                           int(self.factory.viewscale*0.8), int(self.factory.viewscale*0.8)))


class FactoryUI:
    def __init__(self, factory, component_menu):
        self.factory = factory
        self.currentcomponent = Conveyor
        self.current_view = 'factory' # or 'component menu' or a specific component's settings
        self.component_menu = component_menu
        self.screen_width = 1
    def draw(self, screen):
        if self.current_view == 'component menu':
            screen.fill((10,10,10))
            w,h = screen.get_size()
            for i in range(len(self.component_menu)):
                screen.blit(pg.transform.scale(self.component_menu[i].sprite, (40,40)), (((i%(w//50))*50)+5,((i//(w//50))*50)+5))
            self.screen_width = w
        elif self.current_view == 'factory':
            self.factory.draw(screen, self.factory.viewscale, self.factory.viewlocation)
            pg.draw.rect(screen, (10,10,10), (5,5,50,50))
            pg.draw.rect(screen, (10,10,10), (60,5,50,50))
            if self.currentcomponent is not None:
                screen.blit(pg.transform.scale(self.currentcomponent.sprite, (40,40)), (65,10))
    def pos_to_square(self, pos):
        return ((pos[0]//self.factory.viewscale) + self.factory.viewlocation[0], (pos[1]//self.factory.viewscale) + self.factory.viewlocation[1])
    def mousedrag(self, pos):
        pass
    def leftbuttondown(self, pos):
        pass
    def leftbuttonup(self, pos):
        if self.current_view == 'component menu':
            square_clicked = ((pos[0]//50), (pos[1]//50))
            item_clicked = square_clicked[0] + (square_clicked[1] * (self.screen_width//50))
            if item_clicked < len(self.component_menu):
                self.currentcomponent = self.component_menu[item_clicked]
                self.current_view = 'factory'
        else:
            if pg.Rect(60,5,50,50).collidepoint(pos):
                self.current_view = 'component menu'
                return True
            position = self.pos_to_square(pos)
            if position in self.factory.components:
                self.factory.components[position].rotate()
            else:
                if self.currentcomponent is not None:
                    self.factory.create_component(self.currentcomponent, position, Compass.NORTH)
    def rightbuttondown(self, pos):
        pass
    def rightbuttonup(self, pos):
        position = self.pos_to_square(pos)
        if position in self.factory.components:
            self.factory.remove_component(position)

def run():
    pg.init()
    screen = pg.display.set_mode((1000,600))
    clock = pg.time.Clock()
    delta_t_ms = 0
    factory = FactoryFloor()
    ui = FactoryUI(factory, [SineGenerator, SquareGenerator, SawtoothGenerator, TriangleGenerator, Conveyor, Output, Destroyer, ADSR, SplitPath, Delay, Squisher, Stretcher])
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return True
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1: # left click
                    ui.leftbuttonup(event.pos)
                elif event.button == 3: # right click
                    ui.rightbuttonup(event.pos)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1: # left click
                    ui.leftbuttondown(event.pos)
                elif event.button == 3: # right click
                    ui.rightbuttondown(event.pos)
            elif event.type == pg.MOUSEMOTION and event.buttons[0] == 1:
                ui.mousedrag(event.pos)
        delta_t_ms += clock.tick(30)
        if delta_t_ms >= 1000 * factory.chunk_length:
            factory.step()
            delta_t_ms -= 1000 * factory.chunk_length
        ui.draw(screen)

        pg.display.flip()









