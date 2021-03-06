from midiutil.MidiFile import MIDIFile

import random
import math
import os
import time
import sys
import argparse

from types import *
from bisect import bisect
# coding=utf-8
import re
import sys

with open('/usr/share/dict/words') as f:
    WORDS = [re.sub(r'\W+', '', word) for line in f for word in line.split()]

'''
Mdict and MName generate a random name for the file based on markov chains from the above file
'''


class Mdict:
    def __init__(self):
        self.d = {}

    def __getitem__(self, key):
        if key in self.d:
            return self.d[key]
        else:
            raise KeyError(key)

    def add_key(self, prefix, suffix):
        if prefix in self.d:
            self.d[prefix].append(suffix)
        else:
            self.d[prefix] = [suffix]

    def get_suffix(self, prefix):
        l = self[prefix]
        return random.choice(l)


class MName:
    """
    A name from a Markov chain
    """

    def __init__(self, chainlen=2):
        """
        Building the dictionary
        """
        if chainlen > 10 or chainlen < 1:
            print("Chain length must be between 1 and 10, inclusive")
            sys.exit(0)
        self.mcd = Mdict()  # Creates a dictionary
        oldnames = []  # Saves original list of names
        self.chainlen = chainlen
        for l in WORDS:
            l = l.strip()
            oldnames.append(l)  # Build whitespace-stripped list of names
            s = " " * chainlen + l  # s = "   "
            for n in range(0, len(l)):  # Iterate through the string l
                self.mcd.add_key(s[n:n + chainlen], s[n + chainlen])  # For each element of string, add 
            self.mcd.add_key(s[len(l):len(l) + chainlen], "\n")

    def New(self):
        """
        New name from the Markov chain
        """
        prefix = " " * self.chainlen  # Prefix = "  "
        name = ""
        suffix = ""
        while True:
            suffix = self.mcd.get_suffix(prefix)
            if suffix == "\n" or len(name) > 9:
                break
            else:
                name = name + suffix
                prefix = prefix[1:] + suffix
        if not name in WORDS:
            return name
        else:
            return self.New()


# Handles writeback of every channel  to file
def write_midi(filename, sequence):
    filename = "music/" + filename
    midi = MIDIFile(1)
    track = 0
    start_time = 0
    midi.addTrackName(track, start_time, filename[:-4])
    tempo = random.randrange(120, 480)
    midi.addTempo(track, start_time, tempo)
    for seq in range(len(sequence)):
        for note in sequence[seq]:
            midi.addNote(track, 9, note.pitch, note.time, note.duration, note.volume)
        # midi.addProgramChange(0, seq, 0, instrList[seq])
    f = open(filename, 'w')
    midi.writeFile(f)
    f.close()


'''
The arrangement contains everything about the song.
It's divided up into an instrument that receives the melody, and remaining instruments that compose the harmony.
The melody receives a part for the Intro, Chorus, each verse, and the Outro.
Harmonies *might* get an intro part, have a part for the chorus and verses, and hold for outro
'''


class Arrangement(object):
    def __init__(self, key):
        self.key = key
        self.scale = SCALE
        self.length_intro = random.randrange(10, 20)
        self.Intro = None  # List of notes used as the 'pickup'
        self.length_chorus = random.randrange(30, 50)
        self.Chorus = None  # List of notes used as the main motif
        self.length_verse = random.randrange(30, 50)
        self.Verses = []  # List of verses, which are each list of notes of the verse
        self.numVerses = random.randrange(2, 5)
        self.length_outro = random.randrange(10, 20)
        self.Outro = None  # List of notes used as the end of the song

    def gen(self):
        self.Intro = Intro(self.length_intro, self.key)  # Intro dictated by 
        self.Intro.gen()
        self.Chorus = Chorus(self.length_chorus, self.key)
        self.Chorus.gen()
        for i in range(self.numVerses):
            self.Verses.append(Verse(self.length_verse, self.key))
            self.Verses[i].gen()
        self.Outro = Outro(self.length_outro, self.key)
        self.Outro.gen()
        print("Length of Intro:", (self.length_intro))
        print("Length of Chorus:", (self.length_chorus))
        print("Length of Verses:", (self.length_verse))
        print("Number of verses:", (self.numVerses))

    def build_arrangement(self):
        # Song structure is Intro/Chorus/(Verse/Chorus pairs)/Outro
        self.melody = []
        self.melody.append(self.Intro.melody)
        self.melody.append(self.Chorus.melody)
        for i in range(self.numVerses):
            self.melody.append(self.Verses[i].melody)
            self.melody.append(self.Chorus.melody)
        self.melody.append(self.Outro.melody)
        return [cat(self.melody)]  ## TODO HARMONY


# List of interval jumps + associated probability -- Each integer represents an interval on the song's scale
jump_list = [(1, .2), (2, .35), (3, .2), (4, .15), (5, .1)]

'''
The intro of the song is unique to the song and plays at the beginning
'''


class Intro(object):
    def __init__(self, length, key):
        self.length = length
        self.melody = []
        self.harmonies = []
        self.key = key
        self.DIRECTION = random.randrange(35, 100)  # < DIRECTION Implies direction change
        self.JUMPINESS = random.randrange(30, 100)  # < JUMPINESS Implies jump
        self.MOBILITY = random.randrange(60, 90)  # < MOBILITY Implies moving notes
        self.CHORDINESS = random.randrange(0, 30)  # < CHORDINESS Implies a chord

    def gen(self):
        mel = Melody(self.length, self.key)
        mel.gen()
        self.melody = mel.sequence
        ## TODO Harmony


'''
The chorus is a repeating element of the song, punctated by verses
'''


class Chorus(object):
    def __init__(self, length, key):
        self.length = length
        self.melody = []
        self.harmonies = []
        self.key = key

    def gen(self):
        mel = Melody(self.length, self.key)
        mel.gen()
        self.melody = mel.sequence
        ## TODO Harmony


'''
A verse is a unique element of the song punctuated by the chorus
'''


class Verse(object):
    def __init__(self, length, key):
        self.length = length
        self.melody = []
        self.harmonies = []
        self.key = key

    def gen(self):
        mel = Melody(self.length, self.key)
        mel.gen()
        self.melody = mel.sequence
        ## TODO Harmony


class Outro(object):
    def __init__(self, length, key):
        self.length = length
        self.melody = []
        self.harmonies = []
        self.key = key

    def gen(self):
        mel = Melody(self.length, self.key)
        mel.gen()
        self.melody = mel.sequence
        ## TODO Harmony


'''
Low-level objects:
Notes, Rhythm, Scale generation
'''


class Note(object):
    def __init__(self, pitch, time, duration, volume):
        self.pitch = pitch
        self.time = time
        self.duration = duration
        self.volume = volume


# Probabilities that a given note is followed by another note length
# Cool thing about the weighted choice - probabilities don't need to sum to 1!
noteDict_melody = {1: [(1, .3), (2, .15), (3, .4), (4, .1), (6, 0)],
                   2: [(1, .1), (2, .4), (3, .15), (4, .35), (6, 0)],
                   3: [(1, .4), (2, .1), (3, .3), (4, .2), (6, 0)],
                   4: [(1, .17), (2, .2), (3, .13), (4, .5), (6, .3)],
                   6: [(1, .025), (2, .275), (3, .05), (4, .5), (6, .2)]}


# noteDict_harmony = {2:[(2, ), (3, ), (4, ), (6, .5), (8, 0)], 
#                    3:[(2, ), (3, .7), (4, ), (6, .3), (8, 0)], 
#                    4:[(2, ), (3, ), (4, ), (6, ), (8, .3)], 
#                    6:[(2, ), (3, ), (4, ), (6, ), (8, .2)],
#                    8:[(2, 0), (3, 0), (4, ), (6, ), (8, .4)}

class Rhythm(object):
    def __init__(self, period):
        self.period = period
        self.rhythm = []

    def gen(self):
        current = random.choice([1, 2, 3, 4, 6])  # Starting notes, with 1 being 16th note
        i = 0
        while i < self.period:
            self.rhythm.append(current)
            i += current
            current = weighted_choice(noteDict_melody[current])
        return self.rhythm


# Lists of instruments that pair well together, maybe.
instrGroups = [[0, 0, 0, 0], [40, 41, 42], [21, 22, 105, 109], [77, 79, 104, 15], [14, 10, 6], [65, 59, 1]]  # TODO


def getInstruments():
    if len(sys.argv) == 1:  # Generate random instruments
        return random.choice(instrGroups)
    elif len(sys.argv) > 17:  # 16 insturments allowed + program name
        return random.choice(instrGroups)
    instr = []
    for i in range(1, len(sys.argv)):  # Ignore program name
        assert int(sys.argv[i]) in range(0, 128), "Instrument must be in bounds (1, 128): %d" % sys.argv[i]
        instr.append(int(sys.argv[i]) - 1)
    return instr


# Concatenate components of arrangement
def cat(seqs):
    res = []
    start_time = 0
    for seq in seqs:
        last = start_time
        for note in seq:
            res.append(Note(note.pitch, start_time + note.time, note.duration, note.volume))
            last = start_time + note.time + note.duration
        start_time = last + 1
    return res


MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]
PHRYGIAN = [0, 1, 4, 5, 7, 8, 10]
UKRAINIAN_DORIAN = [0, 2, 3, 6, 7, 9, 10]
MOLOCH = [0, 2, 4, 5, 7, 9, 10]
PERSIAN = [0, 1, 4, 5, 6, 8, 11]


def gen_scale():
    k = random.choice([MAJOR, MINOR, PHRYGIAN, UKRAINIAN_DORIAN, MOLOCH, PERSIAN])
    print(k)
    return (k)


SCALE = gen_scale()


def gen_chords():  # TODO, based on scale. See wikipedia article on chord (music)
    return [[4, 7], [7, 16], [-3, 4], [3, 8], [4], [7]]


def weighted_choice(choices):
    values, weights = zip(*choices)
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random.random() * total
    i = bisect(cum_weights, x)
    return values[i]


# List of common chords. Root note is implied
chordList = gen_chords()  # TODO Chordlist


class Melody(object):
    def __init__(self, length, key):
        self.key = 84 + key
        self.rhythm = []
        self.sequence = []
        self.scale = SCALE
        self.length = length
        self.DIRECTION = random.randrange(35, 100)  # < DIRECTION Implies direction change
        self.JUMPINESS = random.randrange(50, 100)  # < JUMPINESS Implies jump
        self.MOBILITY = random.randrange(60, 90)  # < MOBILITY Implies moving notes
        self.CHORDINESS = random.randrange(0, 30)  # < CHORDINESS Implies a chord

    def gen(self):
        self.rhythm = Rhythm(self.length).gen()  ## TODO Rhythm length
        currentNote = self.key
        t = 0
        currentDirection = 1
        index = 0
        for i in self.rhythm:
            self.sequence.append(Note(currentNote, t, i, 100))
            if (random.randrange(0, 100) < self.CHORDINESS):
                chord = random.choice(chordList)
                for note in chord:
                    self.sequence.append(Note(currentNote + note, t, i, 100))
            if (random.randrange(0, 100) < self.MOBILITY):
                currentNote = self.key + (
                    self.scale[index % len(self.scale)] + (index / len(self.scale)) * 12 if index > 0 else self.scale[-(
                            -index % len(self.scale))] + 12 * (index / len(self.scale)))
            if (random.randrange(0, 100) < self.DIRECTION):
                currentDirection = -currentDirection
            if (random.randrange(0, 100) < self.JUMPINESS):
                index += currentDirection * random.choice([2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 4, 5])
            if (currentNote < 50 or currentNote > 100):
                currentNote = self.key
            t += i


class Percussion(object):
    def __init__(self, length, key):
        self.key = key
        self.rhythm = []
        self.scale = SCALE
        self.length = length
        self.DIRECTION = random.randrange(35, 100)
        self.JUMPINESS = random.randrange(50, 100)
        self.MOBILITY = random.randrange(60, 90)
        self.CHORDINESS = random.randrange(0, 30)

    def gen(self):
        self.rhythm = Rhythm(self.length).gen()
        currentNote = self.key
        t = 0
        currentDirection = 1
        index = 0
        for i in self.rhythm:
            self.sequence.append(Note(currentNote, t, i, 100))
            if (random.randrange(0, 100) < self.MOBILITY):
                currentNote = random.randrange(37,
                                               80)  # choice([37, 37, 37, 37, 37, 37, 37, 41, 41, 41, 42, 42, 43, 43, 48, 48])
            t += i


# I don't know at the moment how this should work, aside from picking 'nice' chords relating to melody'
class Harmony(object):
    def __init__(self, melody):
        self.melody = melody
        self.key = melody.key + random.randchoice(-24, -12, 0, 12)  # Get a random octave shift
        self.shift = random.choice([-24, -12, 0])
        self.rhythm = []  # Currently copying the rhythm
        self.sequence = []

    def gen_rhythm(self):
        for i in range(songLength, 8):  ## TODO
            self.rhythm.append(8)  # For now, half notes 

    def gen(self):
        self.gen_rhythm()
        startNote = self.key
        t = 0
        for i in self.rhythm:
            self.sequence.append(Note(i.pitch + self.shift + random.choice(chordList), i.time, i.duration, 75))  ## TODO


name = time.strftime(MName().New() + '.mid')
print(name)
instrList = getInstruments()  # Get a list of instruments used, either randomly or from user input
numHarmonies = len(instrList) - 1
print("Number of harmonies:", (numHarmonies))
# Initialize the entire song, part-by-part
arrangement = Arrangement(random.randrange(0, 12))
arrangement.gen()
write_midi(name, arrangement.build_arrangement())
# os.system('./play.sh %s' % (name,))
