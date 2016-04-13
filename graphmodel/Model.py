from collections import OrderedDict, defaultdict
import sys

__author__ = 'Adisor'


def is_chord(sound_event):
    return is_chord(sound_event.notes)


def is_chord(notes):
    return len(notes) > 0


class NotesTable(object):
    """
    Base class used for storing Note objects in a table
    """

    def __init__(self):
        self.table = {}
        self.channels = []

    def add(self, note):
        self.table[note.timeline_tick] = note

    def add_channel_if_not_exists(self, channel):
        if not self.has_channel(channel):
            self.add_channel(channel)

    def has_channel(self, channel):
        return channel in self.channels

    def add_channel(self, channel):
        self.channels.append(channel)


class OrganizedNotesTable(NotesTable):
    """
    This class is used for structuring Note objects into a table.

    The row is the timeline tick and the column is the channel
    Each cell contains at least 1 note. If there are more than 1 notes, then the cell stores a chord.
    """

    def __init__(self):
        # We use channel encoding to speed up checking
        super(OrganizedNotesTable, self).__init__()
        self.channel_coding = 0 << 16

    def add(self, note):
        # Add the note to a cell located by its timeline tick, channel and pitch
        tick = note.timeline_tick
        channel = note.channel
        pitch = note.pitch
        self.add_channel_if_not_exists(channel)
        if tick not in self.table:
            self.table[tick] = {}
        if channel not in self.table[tick]:
            self.table[tick][channel] = {}
        self.table[tick][channel][pitch] = note

    def has_channel(self, channel):
        return self.channel_coding & (1 << channel)

    def add_channel(self, channel):
        super(OrganizedNotesTable, self).add_channel(channel)
        self.channel_coding |= 1 << channel

    def get_note(self, tick, channel, pitch):
        return self.table[tick][channel][pitch]

    def sort(self):
        # sort by timeline_tick
        self.table = OrderedDict(sorted(self.table.items(), key=lambda key: key[0]))

    def first_tick(self):
        for tick in self.table:
            return tick

    def update_delta_times(self):
        """
        TODO: Change the way durations are computed, because for some notes, the duration is based on
        notes in the same chord, which is not correct
        """
        # Computes tick duration to previous and next note for each note
        previous_tick = self.first_tick()
        for tick in self.table:
            # compute duration to previous note
            for channel in self.table[tick]:
                for pitch in self.table[tick][channel]:
                    note = self.table[tick][channel][pitch]
                    note.previous_delta_ticks = note.timeline_tick - previous_tick
            # compute duration to next note from the previous one
            for channel in self.table[previous_tick]:
                for pitch in self.table[previous_tick][channel]:
                    note = self.table[previous_tick][channel][pitch]
                    note.next_delta_ticks = tick - note.timeline_tick
            previous_tick = tick

    def __str__(self):
        string = "OrganizedNotesTable:\n"
        for tick in self.table:
            for channel in self.table[tick]:
                if len(self.table[tick][channel]) > 1:
                    string += "CHORD:\n"
                else:
                    string += "NOTE:\n"
                for pitch in self.table[tick][channel]:
                    string += str(self.table[tick][channel][pitch]) + "\n"
        return string


class MusicalTranscript(object):
    """
    Used for simplifying the structure that stores the notes from the OrganizedTableNotes object
    Stores SoundEvent objects into lists called tracks
    """

    def __init__(self, notes_table):
        self.notes_table = notes_table
        self.tracks = {}
        self.__build__()

    def __build__(self):
        """
        Loops through each tick and channel and creates SoundEvent objects from the notes.
        The objects are then added to tracks, where each track corresponds to a channel
        """
        table = self.notes_table.table
        for channel in self.notes_table.channels:
            self.tracks[channel] = []
        for tick in table:
            for channel in table[tick]:
                notes = []
                for pitch in table[tick][channel]:
                    notes.append(table[tick][channel][pitch])
                sound_event = SoundEvent(notes)
                 # TODO: IF THE NOTE IF A DIFFERENT CHANNEL BUT IT IS PART OF A SOUND EVENT WITH MULTIPLE NOTES, THEN IT IS NOT PART OF THAT CHORD
                self.tracks[channel].append(sound_event)

    def get_sound_events(self, channel):
        return self.tracks[channel]

    def __str__(self):
        string = "MusicalTranscript:\n"
        for channel in self.tracks:
            string += "Track: %d\n" % channel
            for sound_event in self.tracks[channel]:
                string += str(sound_event) + "\n"
        return string


class Frame(object):
    """
    Object that encapsulates a tuple of SoundEvent objects
    """

    def __init__(self, max_size, sound_events=None):
        self.max_size = max_size
        if sound_events is None:
            self.sound_events = ()
        else:
            self.sound_events = sound_events

    def add(self, sound_event):
        self.sound_events += (sound_event,)

    def is_full(self):
        return self.__sizeof__() == self.max_size

    def first(self):
        return self.sound_events[0]

    def last_sound_event(self):
        return self.sound_events[-1]

    def __sizeof__(self):
        return len(self.sound_events)

    def __hash__(self):
        return hash(self.sound_events)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        string = "Frame:\n"
        for sound_event in self.sound_events:
            string += str(sound_event) + "\n"
        return string


class SoundEvent(object):
    """
    Stores a list of sorted notes by next_delta_ticks duration

    If the size of the list is greater than 1 - this object symbolizes a chord
    """

    def __init__(self, notes):
        # sorted by duration
        self.notes = ()
        for note in sorted(notes, key=lambda note: note.next_delta_ticks):
            self.notes += (note,)

    def first(self):
        return self.notes[0]

    def shortest_note(self):
        return self.notes[0]

    def get_smallest_duration(self):
        min_ticks = sys.maxint
        for note in self.notes:
            if note.next_delta_ticks < min_ticks:
                min_ticks = note.duration_ticks
        return min_ticks

    def __hash__(self):
        return (hash(self.notes) << 4) | len(self.notes)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        string = "SoundEvent:\n"
        for note in self.notes:
            string += str(note) + " "
        return string


class Note(object):
    """
    The class that represents a musical note. Contains all the necessary data.
    """

    def __init__(self, timeline_tick, wait_ticks, duration_ticks, channel, pitch, velocity):
        # timestamp from original song
        self.timeline_tick = timeline_tick

        # ticks before playing this note
        self.wait_ticks = wait_ticks

        # how long to play this note (not how many ticks until next note)
        self.duration_ticks = duration_ticks

        # ticks from last sound event
        self.previous_delta_ticks = 0

        # ticks to next sound event
        self.next_delta_ticks = 0
        self.channel = channel
        self.pitch = pitch
        self.velocity = velocity

        # TODO: USE THIS WHEN DOING COMPLEX METADATA RESOLUTION
        self.context = []

    # ticks | channel | pitch | velocity
    # bytes: 12 | 5 | 7 | 8
    def encode(self):
        return (self.duration_ticks << 20) | (self.channel << 15) | (self.pitch << 8) | self.velocity
        # return (self.ticks << 20) | (self.channel << 15) | (self.pitch << 8)
        # return (self.ticks << 20) | (self.channel << 15)

    def __hash__(self):
        return self.encode()

    def __eq__(self, other):
        # return self.__hash__() == other.__hash__ and abs(self.pitch - other.pitch) < 10
        return self.encode() == other.encode()

    def __str__(self):
        return (
            "Note(start_tick:%d, wait_ticks:%d, ticks:%d, "
            "previous_delta_ticks:%d, next_delta_ticks:%d, "
            "channel:%d, pitch:%d, velocity:%d)" %
            (self.timeline_tick, self.wait_ticks, self.duration_ticks,
             self.previous_delta_ticks, self.next_delta_ticks,
             self.channel, self.pitch, self.velocity))
