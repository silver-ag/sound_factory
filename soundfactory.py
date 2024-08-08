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
    noise_generator = pg.image.load('include/noisegen.png')
    silence_generator = pg.image.load('include/silencegen.png')
    combine = pg.image.load('include/combine.png')
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
    name = "<component>"
    opentop = False
    opengates = True
    characteristic_colour = (255,255,255)
    settings = {}
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
    def settings_changed(self):
        pass
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

class ComponentSetting:
    rect = pg.Rect(0,0,0,0)
    default = 0
    def get_value(self):
        return self.value
    def set_value(self, new_v):
        self.value = new_v
    def mousedown(self, pos):
        pass
    def mouseup(self, pos):
        pass
    def mousedrag(self, pos):
        pass

class MultipleChoice(ComponentSetting):
    def __init__(self, name, location, options):
        self.options = options
        self.options_text = None
        self.value = options[0]
        self.rect = pg.Rect(*location, 0, 0)
        self.name = name
    def set_value(self, new_v):
        if new_v in self.options:
            self.value = new_v
    def draw(self, screen, font):
        if self.options_text is None:
            self.options_text = [font.render(option, True, (255,255,255)) for option in self.options]
            self.rect.w = max([font.size(option)[0] for option in self.options])
            self.rect.h = sum([font.size(option)[1] for option in self.options])
            if isinstance(self.name, str):
                self.name = font.render(self.name, True, (255,255,255))
            self.rect.w = max(self.rect.w, self.name.get_size()[0])
        pg.draw.rect(screen, (50,50,50), self.rect)
        screen.blit(self.name, (self.rect.x, self.rect.y - self.name.get_size()[1]))
        y = self.rect.y
        for i in range(len(self.options)):
            screen.blit(self.options_text[i], (self.rect.x, y))
            if self.value == self.options[i]:
                pg.draw.rect(screen, (255,255,255), (self.rect.x, y, self.rect.w, self.options_text[i].get_size()[1]), width=3)
            y += self.options_text[i].get_size()[1]
    def mouseup(self, pos):
        y = self.rect.y
        for i in range(len(self.options)):
            if pos[1] >= y and pos[1] < y + self.options_text[i].get_size()[1]:
                self.set_value(self.options[i])
            y += self.options_text[i].get_size()[1]
            

class SliderSetting(ComponentSetting):
    def __init__(self, name, location, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum
        self.range = maximum - minimum
        self.value = (minimum + maximum) / 2
        self.rect = pg.Rect(*location, 0, 0)
        self.labels = None
        self.name = name
    def draw(self, screen, font):
        if self.labels == None:
            self.labels = [font.render(str(round(self.minimum,1)), True, (255,255,255)),
                           font.render(str(round((self.minimum+self.maximum)/2,1)), True, (255,255,255)),
                           font.render(str(round(self.maximum,1)), True, (255,255,255))]
            self.rect.w = max([label.get_size()[0] for label in self.labels]) + 30
            self.rect.h = 320
            if isinstance(self.name, str):
                self.name = font.render(self.name, True, (255,255,255))
            self.rect.w = max(self.rect.w, self.name.get_size()[0])
        pg.draw.rect(screen, (50,50,50), self.rect)
        screen.blit(self.name, (self.rect.x, self.rect.y - self.name.get_size()[1]))
        pg.draw.rect(screen, (150,150,150), (self.rect.x+10, self.rect.y+10, 10, 300))
        pg.draw.rect(screen, (230,230,230), (self.rect.x+10, self.rect.y+(300*(1-((self.value-self.minimum)/self.range))), 10, 20))
        pg.draw.line(screen, (0,0,0),
                     (self.rect.x+10, self.rect.y+10+(300*(1-((self.value-self.minimum)/self.range)))),
                     (self.rect.x+20, self.rect.y+10+(300*(1-((self.value-self.minimum)/self.range)))))
        screen.blit(self.labels[2], (self.rect.x+30, self.rect.y))
        screen.blit(self.labels[1], (self.rect.x+30, self.rect.y+150))
        screen.blit(self.labels[0], (self.rect.x+30, self.rect.y+300))
    def mousedrag(self, pos):
        self.set_value(((1-((pos[1]-self.rect.y)/self.rect.h))*self.range) + self.minimum)
    def set_value(self, new_v):
        self.value = max(self.minimum, min(self.maximum, new_v))


class Conveyor(FactoryComponent):
    name = 'conveyor belt'
    sprite = Sprites.conveyor
    opentop = True
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks[self.location].velocity = self.direction


class Oscillator(FactoryComponent):
    name = 'oscillator'
    sprite = Sprites.sine_generator
    characteristic_colour = (0,0,255)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = {'waveform': MultipleChoice('waveform', (10,50), ['sine', 'square', 'sawtooth', 'triangle', 'noise', 'silence']),
                         'frequency': MultipleChoice('note', (120, 50), ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']),
                         'detune': SliderSetting('detune', (180,50), -20, 20)}
    def operate(self):
        if self.location not in self.factory.soundchunks:
            generator = {'sine': gensound.Sine, 'square': gensound.Square,
                         'sawtooth': gensound.Sawtooth, 'triangle': gensound.Triangle,
                         'noise': gensound.WhiteNoise, 'silence': gensound.Silence}[self.settings['waveform'].get_value()]
            if self.settings['waveform'].get_value() in ['noise', 'silence']: #  these ones choke on 'frequency' input
                self.factory.create_soundchunk(generator(duration=1e3 * self.factory.chunk_length), self.location)
            else:
                self.factory.create_soundchunk(generator(frequency={'A':440, 'A#':466.2, 'B':493.9, 'C':523.3,
                                                                    'C#':554.4, 'D':587.3, 'D#':622.3, 'E':659.3,
                                                                    'F':698.5,'F#':740, 'G':784, 'G#':830.6}[self.settings['frequency'].get_value()] +
                                                         self.settings['detune'].get_value(), duration=1e3 * self.factory.chunk_length),
                                               self.location)
            self.stamp_colour(self.factory.soundchunks[self.location])
        self.factory.soundchunks[self.location].velocity = self.direction
    def settings_changed(self):
        self.sprite, self.characteristic_colour = {'sine': (Sprites.sine_generator, (0,0,255)),
                                                   'square': (Sprites.square_generator, (0,255,0)),
                                                   'sawtooth': (Sprites.sawtooth_generator, (255,0,0)),
                                                   'triangle': (Sprites.triangle_generator, (255,255,0)),
                                                   'noise': (Sprites.noise_generator, (180,180,180)),
                                                   'silence': (Sprites.silence_generator, (0,0,0))}[self.settings['waveform'].get_value()]



class ADSR(FactoryComponent):
    name = 'ADSR envelope'
    sprite = Sprites.adsr
    characteristic_colour = (255,0,255)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = {'attack': SliderSetting('attack time', (10,50), 0, 1),
                         'decay': SliderSetting('decay time', (150,50), 0, 1),
                         'sustain': SliderSetting('sustain level', (270,50), 0, 1),
                         'release': SliderSetting('release time', (420,50), 0, 1)}
        self.settings['attack'].set_value(0.2)
        self.settings['decay'].set_value(0.2)
        self.settings['sustain'].set_value(0.75)
        self.settings['release'].set_value(0.2)
    def operate(self):
        if self.location in self.factory.soundchunks:
            atk = math.floor(self.settings['attack'].get_value() * self.factory.chunk_length * 44100)
            dec = math.floor(self.settings['decay'].get_value() * self.factory.chunk_length * 44100)
            sus = self.settings['sustain'].get_value()
            rel = math.floor(self.settings['release'].get_value() * self.factory.chunk_length * 44100)
            if isinstance(self.factory.soundchunks[self.location].signal, gensound.signals.Mix):
                chunk_length = math.floor((self.factory.soundchunks[self.location].signal.signals[0].duration/1000) * 44100)
            else:
                chunk_length = math.floor((self.factory.soundchunks[self.location].signal.duration/1000) * 44100)
            if atk + dec + rel >= chunk_length:
                difference = (atk + dec + rel - chunk_length) + 3 # three sample safety margin cus we can't have 0-length sections apparently
                if difference < rel:
                    rel -= difference
                else:
                    difference -= rel
                    rel = 1
                    if difference < dec:
                        dec -= difference
                    else:
                        difference -= dec
                        dec = 1
                        atk -= difference
            self.factory.soundchunks[self.location].signal *= gensound.transforms.ADSR(attack = atk, decay = dec, sustain = sus, release = rel)
            self.factory.soundchunks[self.location].velocity = self.direction
            self.stamp_colour(self.factory.soundchunks[self.location])

class Combine(FactoryComponent):
    name = 'combine'
    sprite = Sprites.combine
    stored_chunk = None
    def operate(self):
        if self.location in self.factory.soundchunks:
            if self.stored_chunk is not None:
                self.characteristic_colour = self.factory.soundchunks[self.location].colour
                self.factory.create_soundchunk(self.stored_chunk.signal + self.factory.soundchunks[self.location].signal,
                                               self.location)
                self.factory.soundchunks[self.location].colour = self.stored_chunk.colour
                self.stamp_colour(self.factory.soundchunks[self.location])
                self.factory.soundchunks[self.location].velocity = self.direction
                self.stored_chunk = None
            else:
                self.stored_chunk = self.factory.soundchunks.pop(self.location)
        

class Output(FactoryComponent):
    name = 'output'
    sprite = Sprites.output
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction = Compass.NORTH
    def operate(self):
        if self.location in self.factory.soundchunks:
            chunk = self.factory.soundchunks.pop(self.location)
            chunk.signal.play()

class Destroyer(FactoryComponent):
    name = 'destroyer'
    sprite = Sprites.destroy
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks.pop(self.location)

class Squisher(FactoryComponent):
    name = 'squisher'
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
    name = 'stretcher'
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
    name = 'delay'
    sprite = Sprites.delay
    def operate(self):
        if not self.opengates:
            self.opengates = True
            self.factory.soundchunks[self.location].velocity = self.direction
        elif self.location in self.factory.soundchunks:
            self.opengates = False

class SplitPath(FactoryComponent):
    name = 'split path'
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
        self.font = pg.font.Font(size=30)
    def draw(self, screen):
        w,h = screen.get_size()
        self.screen_width = w
        if self.current_view == 'component menu':
            screen.fill((10,10,10))
            for i in range(len(self.component_menu)):
                screen.blit(pg.transform.scale(self.component_menu[i].sprite, (40,40)), (((i%(w//50))*50)+5,((i//(w//50))*50)+5))
        elif self.current_view == 'factory':
            self.factory.draw(screen, self.factory.viewscale, self.factory.viewlocation)
            pg.draw.rect(screen, (10,10,10), (5,5,50,50))
            pg.draw.rect(screen, (10,10,10), (60,5,50,50))
            if self.currentcomponent is not None:
                screen.blit(pg.transform.scale(self.currentcomponent.sprite, (40,40)), (65,10))
        elif isinstance(self.current_view, FactoryComponent):
            screen.fill((10,10,10))
            title = self.font.render(self.current_view.name, True, (255,255,255))
            screen.blit(title, (0,0))
            pg.draw.rect(screen, (255,0,0), (self.screen_width - 50, 0, 50, 50))
            for setting in self.current_view.settings.values():
                setting.draw(screen, self.font)
    def pos_to_square(self, pos):
        return ((pos[0]//self.factory.viewscale) + self.factory.viewlocation[0], (pos[1]//self.factory.viewscale) + self.factory.viewlocation[1])
    def mousedrag(self, pos):
        if isinstance(self.current_view, FactoryComponent):
            for setting in self.current_view.settings.values():
                if setting.rect.collidepoint(pos):
                    setting.mousedrag(pos)
                    break
    def leftbuttondown(self, pos):
        if isinstance(self.current_view, FactoryComponent):
            for setting in self.current_view.settings.values():
                if setting.rect.collidepoint(pos):
                    setting.mousedown(pos)
                    break
    def leftbuttonup(self, pos):
        if self.current_view == 'component menu':
            square_clicked = ((pos[0]//50), (pos[1]//50))
            item_clicked = square_clicked[0] + (square_clicked[1] * (self.screen_width//50))
            if item_clicked < len(self.component_menu):
                self.currentcomponent = self.component_menu[item_clicked]
                self.current_view = 'factory'
        elif self.current_view == 'factory':
            if pg.Rect(60,5,50,50).collidepoint(pos):
                self.current_view = 'component menu'
                return True
            position = self.pos_to_square(pos)
            if position in self.factory.components:
                if pg.key.get_mods() & pg.KMOD_SHIFT:
                    self.current_view = self.factory.components[position]
                else:
                    self.factory.components[position].rotate()
            else:
                if self.currentcomponent is not None:
                    self.factory.create_component(self.currentcomponent, position, Compass.NORTH)
        elif isinstance(self.current_view, FactoryComponent):
            if pg.Rect(self.screen_width- 50, 0, 50, 50).collidepoint(pos):
                self.current_view.settings_changed()
                self.current_view = 'factory'
            else:
                for setting in self.current_view.settings.values():
                    if setting.rect.collidepoint(pos):
                        setting.mouseup(pos)
                        break
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
    ui = FactoryUI(factory, [Oscillator, Conveyor, Output, Destroyer, ADSR, SplitPath, Delay, Squisher, Stretcher, Combine])
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





run()



