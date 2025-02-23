from midi import events
import midi

__author__ = 'Adisor'


def is_channel_event(event):
    """
    :param event: Midi event
    :return: boolean
    """
    return isinstance(event, events.Event)


def get_event_type(event):
    """
    :param event: Midi Event
    :return: the type of the Midi Event object
    """
    return type(event)


def is_meta_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.MetaEvent)


def is_music_control_event(event):
    """
    Checks to see if the event is an event that sets music control - meaning tempo, control change event
    :param event: Midi Event
    :return: boolean
    """
    event_type = get_event_type(event)
    return event_type in [events.ControlChangeEvent, events.SetTempoEvent, events.AfterTouchEvent,
                          events.ChannelAfterTouchEvent, events.PitchWheelEvent, events.SysexEvent]


def is_time_signature_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.TimeSignatureEvent)


def is_set_tempo_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.SetTempoEvent)


def is_event_with_channel(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.Event)


def is_key_signature_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.KeySignatureEvent)


def is_control_change_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return event.name == events.ControlChangeEvent.name


def is_port_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.PortEvent)


def is_program_change_event(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.ProgramChangeEvent)


def has_note_ended(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.NoteOffEvent) or (isinstance(event, events.NoteOnEvent) and event.velocity == 0)


def is_new_note(event):
    """
    :param event: Midi Event
    :return: boolean
    """
    return isinstance(event, events.NoteOnEvent) and event.velocity > 0


def to_note_on_event(note, channel):
    """
    :param note: model Note
    :return: Midi Event
    """
    return midi.NoteOnEvent(channel=channel, tick=0, pitch=note.pitch,
                            velocity=note.volume)


def to_note_off_event(note, channel):
    """
    :param note: model Note
    :return: Midi Event
    """
    return midi.NoteOnEvent(channel=channel, tick=0, pitch=note.pitch,
                            velocity=0)


def delete_tracks(pattern, start, stop):
    """
    Deletes tracks that are in the range
    :param pattern: midi pattern
    :param start: start index
    :param stop: end index
    :return: modified pattern
    """
    tracks = []
    for i in range(start, stop, 1):
        tracks.append(pattern[i])
    for track in tracks:
        pattern.remove(track)


def convert_channel(track, channel):
    """
    Converts all the notes in the track to the specified channel
    :param track: Midi Track
    :param channel: target conversion channel
    :return: Modified Midi Track
    """
    for event in track:
        event.channel = channel


def change_program(track, data):
    """
    Changes the data value of the ProgramChangeEvent event in the track
    :param track: Midi track
    :param data: array with 1 number element, specifying the the program change
    :return: track with modified ProgramChangeEvent
    """
    for event in track:
        if is_program_change_event(event):
            event.data = data


def change_key_signature(track, data):
    """
    Changes the data value of the key signature event in the track
    :param track: Midi track
    :param data: array with 2 bytes
    :return: track with modified key signature
    """
    for event in track:
        if is_key_signature_event(event):
            event.data = data


def get_channel(track):
    """
    Returns the channel of the track
    :param track: Midi track
    :return: channel number
    """
    for event in track:
        if is_event_with_channel(event):
            return event.channel
    return None


def get_program_change_event(track):
    """
    Returns the event that specifies the instrument of the track
    :param track:  Midi track
    :return: instrument event
    """
    return loop_track_and_return_event_on_condition(track, is_program_change_event)


def get_instrument(track):
    """
    :param track: Midi track
    :return: instrument number
    """
    program_change_event = get_program_change_event(track)
    if program_change_event is None:
        return None
    return program_change_event.data[0]


def get_port_event(track):
    """
    Returns the port event of the track
    :param track:
    :return: port event
    """
    return loop_track_and_return_event_on_condition(track, is_port_event)


def get_time_signature_event(pattern):
    """
    Returns the time signature of the entire musical piece
    :param pattern: Midi pattern
    :return: time signature event
    """
    return loop_track_and_return_event_on_condition(pattern[0], is_time_signature_event)


def get_key_signature_event(pattern):
    """
    Returns the key signature event of the entire musical piece
    :param pattern: Midi pattern
    :return: key signature event
    """
    return loop_track_and_return_event_on_condition(pattern[0], is_key_signature_event)


def loop_track_and_return_event_on_condition(track, condition):
    """
    :param track: Midi track
    :param condition: boolean function
    :return: Midi event
    """
    for event in track:
        if condition(event):
            return event
    return None


def is_song_meta_event(event):
    """
    :param event: Midi event
    :return: boolean
    """
    return isinstance(event, events.KeySignatureEvent) or isinstance(event, events.TimeSignatureEvent)


def remove_control_change_events(pattern):
    """
    :param pattern: Midi pattern
    :return: pattern without change events
    """

    for track in pattern:
        for event in track:
            if is_control_change_event(event):
                event.data = [0, 0]


def has_notes(track):
    """
    :param track: Midi track
    :return: boolean
    """
    for event in track:
        if is_new_note(event):
            return True
    return False


def hash_event(event):
    """
    Hashes based on an event's data
    :param event: Midi event
    :return: hash number
    """
    string = ""
    if isinstance(event, events.AbstractEvent):
        for byte in event.data:
            string += chr(byte)
    return hash(string)


def to_program_change_event(instrument):
    """
    :param instrument: instrument number
    :return: Midi event
    """
    return events.ProgramChangeEvent(data=[instrument])


def print_rhythmic_pattern(pattern):
    """
    :param pattern: Midi pattern
    :return:
    """
    total_tempo = 0
    total_change = 0
    number_of_events = 0
    previous_tempo = 0
    for event in pattern[0]:
        if is_set_tempo_event(event):
            data = event.data
            tempo = (data[0] << 16) | (data[1] << 8) | data[2]
            print tempo, data, tempo - previous_tempo
            total_change += tempo - previous_tempo
            previous_tempo = tempo
            total_tempo += tempo
            number_of_events += 1
    print "average tempo, change of tempo", total_tempo / number_of_events, total_change / number_of_events


def are_tempo_events_same(tempo_event1, tempo_event2):
    """
    :param tempo_event1: Midi tempo event
    :param tempo_event2: Midi tempo event
    :return: boolean
    """
    return tempo_event1.data == tempo_event2.data
