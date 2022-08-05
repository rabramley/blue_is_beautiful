from itertools import accumulate
from re import S


class Scale:
    NOTES = ['a', 'a#', 'b', 'c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#']
    SCALES = {
        'major': ['W', 'W', 'H', 'W', 'W', 'W', 'H'],
        'minor': ['W', 'H', 'W', 'W', 'H', 'W', 'W'],
        'ionian': ['W', 'W', 'H', 'W', 'W', 'W', 'H'],
        'dorian': ['W', 'H', 'W', 'W', 'W', 'H', 'W'],
        'phrygian': ['H', 'W', 'W', 'W', 'H', 'W', 'W'],
        'lydian': ['W', 'W', 'W', 'H', 'W', 'W', 'H'],
        'myxolydian': ['W', 'W', 'H', 'W', 'W', 'H', 'W'],
        'aolian': ['W', 'H', 'W', 'W', 'H', 'W', 'W'],
        'locrian': ['H', 'W', 'W', 'H', 'W', 'W', 'W'],
    }
    INTYERVALS = {
        'W': 2,
        'H': 1,
    }

    def __init__(self, key, scale, lowest_octave=None, highest_octave=None):
        key_base = 21 + Scale.NOTES.index(key.lower())

        self._notes = [key_base + (lowest_octave * 12)]

        intervals = list(accumulate((Scale.INTYERVALS[i] for i in Scale.SCALES[scale.lower()])))

        for octave in range(lowest_octave or 0, (highest_octave or 8) + 1):
            for interval in intervals:
                note = key_base + (octave * 12) + interval
                if note <= 127:
                    self._notes.append(note)

    def quantize_note(self, note):
        return [n for n in self._notes if n >= note][0]

    def get_notes(self):
        return self._notes
