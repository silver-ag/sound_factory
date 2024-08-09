import math
import gensound
from gensound.effects import Stretch
import pygame as pg
import tkinter as tk
from tkinter import filedialog, messagebox
import pickle

class Sprites:
    font = None
    unknown = pg.image.load('include/unknown.png')
    component_sprites = {
            'conveyor': pg.image.load('include/conveyor.png'),
            'sine_generator': pg.image.load('include/sinegen.png'),
            'sawtooth_generator': pg.image.load('include/sawtoothgen.png'),
            'triangle_generator': pg.image.load('include/trianglegen.png'),
            'square_generator': pg.image.load('include/squaregen.png'),
            'noise_generator': pg.image.load('include/noisegen.png'),
            'silence_generator': pg.image.load('include/silencegen.png'),
            'combine': pg.image.load('include/combine.png'),
            'destroy': pg.image.load('include/destroy.png'),
            'output': pg.image.load('include/output.png'),
            'adsr': pg.image.load('include/adsr.png'),
            'delay': pg.image.load('include/delay.png'),
            'splitpath': pg.image.load('include/splitpath.png'),
            'squish': pg.image.load('include/squish.png'),
            'stretch': pg.image.load('include/stretch.png')}
    icon_sprites = {
        'settings': pg.image.load('include/settings.png'),
        'pause': pg.image.load('include/pause.png'),
        'play': pg.image.load('include/play.png')}
    text_sprites = {} # place to put text sprites because we can't pickle surfaces
    def get_sprite(kind, name):
        if kind == 'component':
            if name in Sprites.component_sprites:
                return Sprites.component_sprites[name]
            else:
                return Sprites.unknown
        elif kind == 'icon':
            if name in Sprites.icon_sprites:
                return Sprites.icon_sprites[name]
            else:
                return Sprites.unknown
        elif kind == 'text':
            if name not in Sprites.text_sprites:
                Sprites.text_sprites[name] = Sprites.font.render(name, True, (255,255,255))
            return Sprites.text_sprites[name]
        else:
            raise Exception(f'unknown kind of sprite: {kind}')
    
    

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
        self.viewlocation = [0,0]
        self.outputs_this_step = []
        self.settings = {'bpm': SliderSetting('bpm', (10,50), 0, 200)}
        self.settings['bpm'].set_value(60)
    def create_component(self, kind, location, direction):
        self.components[location] = kind(self, location, direction)
    def create_soundchunk(self, signal, location):
        self.soundchunks[location] = SoundChunk(self, location, signal)
    def floorlocation_to_screenlocation(self, position):
        return ((position[0]-self.viewlocation[0])*self.viewscale, (position[1]-self.viewlocation[1])*self.viewscale)
    def screenlocation_to_floorlocation(self, position):
        return ((position[0]//self.viewscale) + self.viewlocation[0], (position[1]//self.viewscale) + self.viewlocation[1])
    def draw(self, screen):
        w,h = screen.get_size()
        pg.draw.rect(screen, (200,200,200), (0,0,w,h))
        for x in range(math.ceil(w/self.viewscale)):
            for y in range(math.ceil(h/self.viewscale)):
                x_off = x + self.viewlocation[0]
                y_off = y + self.viewlocation[1]
                if (x_off,y_off) in self.components and self.components[(x_off,y_off)].opentop:
                    self.components[(x_off,y_off)].draw(screen)
        for x in range(math.ceil(w/self.viewscale)):
            for y in range(math.ceil(h/self.viewscale)):
                x_off = x + self.viewlocation[0]
                y_off = y + self.viewlocation[1]
                if (x_off,y_off) in self.soundchunks:
                    self.soundchunks[(x_off,y_off)].draw(screen)
        for x in range(math.ceil(w/self.viewscale)):
            for y in range(math.ceil(h/self.viewscale)):
                x_off = x + self.viewlocation[0]
                y_off = y + self.viewlocation[1]
                if (x_off,y_off) in self.components and not self.components[(x_off,y_off)].opentop:
                    self.components[(x_off,y_off)].draw(screen)
    def step(self):
        for component in self.components.values():
            component.operate()
        for soundchunk in list(self.soundchunks.values()):
            soundchunk.move()
        for soundchunk in self.soundchunks.values():
            soundchunk.moved_this_tick = False
        if len(self.outputs_this_step) > 0:
            final_output = self.outputs_this_step[0]
            if len(self.outputs_this_step) > 1:
                for output in self.outputs_this_step[1:]:
                    final_output += output
            final_output.play()
            self.outputs_this_step = []
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
    def settings_changed(self):
        self.chunk_length = 60/self.settings['bpm'].get_value()


class FactoryComponent:
    name = "<component>"
    opentop = False
    opengates = True
    characteristic_colour = (255,255,255)
    settings = {}
    info = '[no information given]'
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
        sprite = Sprites.get_sprite('component', self.sprite_name)
        if self.direction == Compass.NORTH:
            screen.blit(pg.transform.scale(sprite, (self.factory.viewscale, self.factory.viewscale)), location)
        elif self.direction == Compass.SOUTH:
            screen.blit(pg.transform.scale(pg.transform.rotate(sprite, 180), (self.factory.viewscale, self.factory.viewscale)), location)
        elif self.direction == Compass.EAST:
            screen.blit(pg.transform.scale(pg.transform.rotate(sprite, 270), (self.factory.viewscale, self.factory.viewscale)), location)
        elif self.direction == Compass.WEST:
            screen.blit(pg.transform.scale(pg.transform.rotate(sprite, 90), (self.factory.viewscale, self.factory.viewscale)), location)
        else:
            print(f'WARNING: factorycomponent with improper direction ({self.direction})')

class SettingWidget:
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

class MultipleChoiceSetting(SettingWidget):
    def __init__(self, name, location, options):
        self.options = options
        self.value = options[0]
        self.rect = pg.Rect(*location, 0, 0)
        self.name = name
    def set_value(self, new_v):
        if new_v in self.options:
            self.value = new_v
    def draw(self, screen, font):
        if self.rect.w == 0:
            self.rect.w = max([Sprites.get_sprite('text', option).get_size()[0] for option in self.options])
            self.rect.h = sum([Sprites.get_sprite('text', option).get_size()[1] for option in self.options])
            self.rect.w = max(self.rect.w, Sprites.get_sprite('text', self.name).get_size()[0])
        pg.draw.rect(screen, (50,50,50), self.rect)
        screen.blit(Sprites.get_sprite('text', self.name), (self.rect.x, self.rect.y - Sprites.get_sprite('text', self.name).get_size()[1]))
        y = self.rect.y
        for i in range(len(self.options)):
            screen.blit(Sprites.get_sprite('text', self.options[i]), (self.rect.x, y))
            if self.value == self.options[i]:
                pg.draw.rect(screen, (255,255,255), (self.rect.x, y, self.rect.w, Sprites.get_sprite('text', self.options[i]).get_size()[1]), width=3)
            y += Sprites.get_sprite('text', self.options[i]).get_size()[1]
    def mouseup(self, pos):
        y = self.rect.y
        for i in range(len(self.options)):
            if pos[1] >= y and pos[1] < y + Sprites.get_sprite('text', self.options[i]).get_size()[1]:
                self.set_value(self.options[i])
            y += Sprites.get_sprite('text', self.options[i]).get_size()[1]
            

class SliderSetting(SettingWidget):
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
            self.labels = [str(round(self.minimum,1)),
                           str(round((self.minimum+self.maximum)/2,1)),
                           str(round(self.maximum,1))]
            self.rect.w = max([Sprites.get_sprite('text', label).get_size()[0] for label in self.labels]) + 30
            self.rect.h = 320
            self.rect.w = max(self.rect.w, Sprites.get_sprite('text', self.name).get_size()[0])
        pg.draw.rect(screen, (50,50,50), self.rect)
        screen.blit(Sprites.get_sprite('text', self.name), (self.rect.x, self.rect.y - Sprites.get_sprite('text', self.name).get_size()[1]))
        pg.draw.rect(screen, (150,150,150), (self.rect.x+10, self.rect.y+10, 10, 300))
        pg.draw.rect(screen, (230,230,230), (self.rect.x+10, self.rect.y+(300*(1-((self.value-self.minimum)/self.range))), 10, 20))
        pg.draw.line(screen, (0,0,0),
                     (self.rect.x+10, self.rect.y+10+(300*(1-((self.value-self.minimum)/self.range)))),
                     (self.rect.x+20, self.rect.y+10+(300*(1-((self.value-self.minimum)/self.range)))))
        screen.blit(Sprites.get_sprite('text', self.labels[2]), (self.rect.x+30, self.rect.y))
        screen.blit(Sprites.get_sprite('text', self.labels[1]), (self.rect.x+30, self.rect.y+150))
        screen.blit(Sprites.get_sprite('text', self.labels[0]), (self.rect.x+30, self.rect.y+300))
    def mousedrag(self, pos):
        self.set_value(((1-((pos[1]-self.rect.y)/self.rect.h))*self.range) + self.minimum)
    def set_value(self, new_v):
        self.value = max(self.minimum, min(self.maximum, new_v))


class Conveyor(FactoryComponent):
    name = 'conveyor belt'
    sprite_name = 'conveyor'
    opentop = True
    info = 'moves any block on it in the direction it faces.'
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks[self.location].velocity = self.direction


class Oscillator(FactoryComponent):
    name = 'oscillator'
    sprite_name = 'sine_generator'
    info = 'an oscillator generates a block of a plain tone whenever no other block is passing through it. different waveforms create different sounds.'
    characteristic_colour = (0,0,255)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = {'waveform': MultipleChoiceSetting('waveform', (10,50), ['sine', 'square', 'sawtooth', 'triangle', 'noise', 'silence']),
                         'frequency': MultipleChoiceSetting('note', (120, 50), ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']),
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
        self.sprite_name, self.characteristic_colour = {'sine': ('sine_generator', (0,0,255)),
                                                        'square': ('square_generator', (0,255,0)),
                                                        'sawtooth': ('sawtooth_generator', (255,0,0)),
                                                        'triangle': ('triangle_generator', (255,255,0)),
                                                        'noise': ('noise_generator', (180,180,180)),
                                                        'silence': ('silence_generator', (0,0,0))}[self.settings['waveform'].get_value()]



class ADSR(FactoryComponent):
    name = 'ADSR envelope'
    sprite_name = 'adsr'
    info = 'applies an ADSR (attack, decay, sustain, release) envelope to each block that passes through it. attack is the time it takes to fade in to maximum volume, decay is the time it takes to fade out to the sustain level where it holds for a while, then release is the time it takes to fade out entirely. attack, decay and release are given as a proportion of the total time of the block, if they total more than 1 then the end of the envelope will be truncated'
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
    sprite_name = 'combine'
    info = 'mixes two blocks, by taking in one and storing it, then taking in the next and producing an average of the two'
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
    sprite_name = 'output'
    info = 'plays the sound of the blocks that enter it, consuming them in the process.'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction = Compass.NORTH
    def operate(self):
        if self.location in self.factory.soundchunks:
            chunk = self.factory.soundchunks.pop(self.location)
            self.factory.outputs_this_step.append(chunk.signal)

class Destroyer(FactoryComponent):
    name = 'destroyer'
    sprite_name = 'destroy'
    info = 'consumes blocks that enter it without playing them. used to get rid of unwanted blocks so they don\'t clog up the system.'
    def operate(self):
        if self.location in self.factory.soundchunks:
            self.factory.soundchunks.pop(self.location)

class Squisher(FactoryComponent):
    name = 'squisher'
    sprite_name = 'squish'
    stored_chunk = None
    info = 'takes two blocks in, one at a time, then produces a block consisting of the two concatenated then doubled in speed so the result remains the same length as the inputs.'
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
    sprite_name = 'stretch'
    info = 'takes a block and produces two blocks in a row that are the first and second half of the input block, halved in speed so that each is the length of the input block.'
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
    sprite_name = 'delay'
    info = 'takes a block, waits one step, then releases it. produces an output stream with gaps in.'
    def operate(self):
        if not self.opengates:
            self.opengates = True
            self.factory.soundchunks[self.location].velocity = self.direction
        elif self.location in self.factory.soundchunks:
            self.opengates = False

class SplitPath(FactoryComponent):
    name = 'split path'
    sprite_name = 'splitpath'
    info = 'alternates between sending its input blocks left or right.'
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
        chunk_sfc = pg.Surface((int(self.factory.viewscale*0.8), int(self.factory.viewscale*0.8)))
        chunk_sfc.set_alpha(128)
        chunk_sfc.fill(self.colour)
        screen.blit(chunk_sfc, ((draw_location[0]+(self.factory.viewscale//10), draw_location[1]+(self.factory.viewscale//10))))


class FactoryUI:
    def __init__(self, factory, component_menu):
        self.factory = factory
        self.currentcomponent = Conveyor
        self.current_view = 'factory' # or 'settings' or 'component menu' or a specific component's settings
        self.component_menu = component_menu
        self.screen_width = 1
        self.font = pg.font.Font(size=30)
        self.save_button_rect = None
        self.load_button_rect = None
        self.playing = True
        Sprites.font = self.font
    def draw(self, screen):
        w,h = screen.get_size()
        self.screen_width = w
        if self.current_view == 'component menu':
            screen.fill((10,10,10))
            for i in range(len(self.component_menu)):
                screen.blit(pg.transform.scale(Sprites.get_sprite('component', self.component_menu[i].sprite_name), (40,40)), (((i%(w//50))*50)+5,((i//(w//50))*50)+5))
        elif self.current_view == 'factory':
            self.factory.draw(screen)
            screen.blit(pg.transform.scale(Sprites.get_sprite('icon', 'settings'), (50,50)), (5,5))
            if self.playing:
                screen.blit(pg.transform.scale(Sprites.get_sprite('icon', 'pause'), (50,50)), (5,60))
            else:
                screen.blit(pg.transform.scale(Sprites.get_sprite('icon', 'play'), (50,50)), (5,60))
            pg.draw.rect(screen, (10,10,10), (60,5,50,50))
            if self.currentcomponent is not None:
                screen.blit(pg.transform.scale(Sprites.get_sprite('component', self.currentcomponent.sprite_name), (40,40)), (65,10))
        elif self.current_view == 'settings':
            screen.fill((10,10,10))
            title = Sprites.get_sprite('text', 'factory settings')
            screen.blit(title, (0,0))
            savetxt = Sprites.get_sprite('text', 'save')
            self.save_button_rect = pg.Rect(150, 50, *savetxt.get_size())
            pg.draw.rect(screen, (50,50,50), self.save_button_rect)
            screen.blit(savetxt, (150, 50))
            loadtxt = Sprites.get_sprite('text', 'load')
            self.load_button_rect = pg.Rect(150, 100, *loadtxt.get_size())
            pg.draw.rect(screen, (50,50,50), self.load_button_rect)
            screen.blit(loadtxt, (150, 100))
            pg.draw.rect(screen, (255,0,0), (self.screen_width - 50, 0, 50, 50))
            for setting in self.factory.settings.values():
                setting.draw(screen, self.font)
        elif isinstance(self.current_view, FactoryComponent):
            screen.fill((10,10,10))
            title = Sprites.get_sprite('text', self.current_view.name)
            screen.blit(title, (0,0))
            info = Sprites.get_sprite('text', 'info')
            pg.draw.rect(screen, (50,50,50), (title.get_size()[0] + 20, 0, *info.get_size()))
            screen.blit(info, (title.get_size()[0]+20, 0))
            pg.draw.rect(screen, (255,0,0), (self.screen_width - 50, 0, 50, 50))
            for setting in self.current_view.settings.values():
                setting.draw(screen, self.font)
    def mousedrag(self, pos):
        if isinstance(self.current_view, FactoryComponent):
            for setting in self.current_view.settings.values():
                if setting.rect.collidepoint(pos):
                    setting.mousedrag(pos)
                    break
        elif self.current_view == 'settings':
            for setting in self.factory.settings.values():
                if setting.rect.collidepoint(pos):
                    setting.mousedrag(pos)
                    break
    def leftbuttondown(self, pos):
        pass
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
            elif pg.Rect(5,5,50,50).collidepoint(pos):
                self.current_view = 'settings'
                return True
            elif pg.Rect(5,60,50,50).collidepoint(pos):
                self.playing = not self.playing
                return True
            position = self.factory.screenlocation_to_floorlocation(pos)
            if position in self.factory.components:
                if pg.key.get_mods() & pg.KMOD_SHIFT:
                    self.current_view = self.factory.components[position]
                else:
                    self.factory.components[position].rotate()
            else:
                if self.currentcomponent is not None:
                    self.factory.create_component(self.currentcomponent, position, Compass.NORTH)
        elif self.current_view == 'settings':
            if pg.Rect(self.screen_width- 50, 0, 50, 50).collidepoint(pos):
                self.factory.settings_changed()
                self.current_view = 'factory'
            elif self.save_button_rect.collidepoint(pos):
                self.save()
            elif self.load_button_rect.collidepoint(pos):
                self.load()
            else:
                for setting in self.factory.settings.values():
                    if setting.rect.collidepoint(pos):
                        setting.mouseup(pos)
                        break
        elif isinstance(self.current_view, FactoryComponent):
            if pg.Rect(self.screen_width- 50, 0, 50, 50).collidepoint(pos):
                self.current_view.settings_changed()
                self.current_view = 'factory'
            elif pg.Rect(Sprites.get_sprite('text', self.current_view.name).get_size()[0] + 20, 0, *Sprites.get_sprite('text', 'info').get_size()).collidepoint(pos):
                self.show_info(self.current_view)
            else:
                for setting in self.current_view.settings.values():
                    if setting.rect.collidepoint(pos):
                        setting.mouseup(pos)
                        break
    def rightbuttondown(self, pos):
        pass
    def rightbuttonup(self, pos):
        position = self.factory.screenlocation_to_floorlocation(pos)
        if position in self.factory.components:
            self.factory.remove_component(position)
    def keyup(self, keyevent):
        if self.current_view == 'factory':
            if keyevent.key == pg.K_UP:
                self.factory.viewlocation[1] -= 1
            elif keyevent.key == pg.K_DOWN:
                self.factory.viewlocation[1] += 1
            elif keyevent.key == pg.K_LEFT:
                self.factory.viewlocation[0] -= 1
            elif keyevent.key == pg.K_RIGHT:
                self.factory.viewlocation[0] += 1
            elif keyevent.key == pg.K_MINUS:
                if self.factory.viewscale > 10:
                    self.factory.viewscale -= 10
            elif keyevent.key == pg.K_EQUALS:
                self.factory.viewscale += 10
    def show_info(self, component):
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title=component.name, message=component.info)
        root.destroy()
    def load(self):
        root = tk.Tk()
        root.withdraw()
        file = filedialog.askopenfile(mode='rb')
        if file is None:
            messagebox.showwarning('could not open file', 'an error occured while trying to open the file, do you have the right permissions?')
        else:
            try:
                self.factory = pickle.load(file)
            except Exception as e:
                messagebox.showwarning(f'could not load file', 'an error occured while trying to load save data from the file: {e}')
        root.destroy()
        self.current_view = 'factory'
    def save(self):
        root = tk.Tk()
        root.withdraw()
        file = filedialog.asksaveasfile(confirmoverwrite=True, mode='wb')
        if file is None:
             messagebox.showwarning('could not open file', 'an error occured while trying to create/open the file, do you have the right permissions for that folder?')
        else:
            pickle.dump(self.factory, file)
        root.destroy()
        self.current_view = 'factory'
            

def run():
    pg.init()
    screen = pg.display.set_mode((1000,600))
    clock = pg.time.Clock()
    delta_t_ms = 0
    ui = FactoryUI(FactoryFloor(), [Oscillator, Conveyor, Output, Destroyer, ADSR, SplitPath, Delay, Squisher, Stretcher, Combine])
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
            elif event.type == pg.KEYUP:
                ui.keyup(event)
        if ui.playing:
            delta_t_ms += clock.tick(30)
        if delta_t_ms >= 1000 * ui.factory.chunk_length:
            ui.factory.step()
            delta_t_ms -= 1000 * ui.factory.chunk_length
        ui.draw(screen)

        pg.display.flip()





run()



