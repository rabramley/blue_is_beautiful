from itertools import accumulate, cycle, takewhile, dropwhile, chain
from re import S


class Scale:
    NOTES = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
    SCALES = {
        'major': [2, 2, 1, 2, 2, 2, 1],
        'minor': [2, 1, 2, 2, 1, 2, 2],
        'ionian': [2, 2, 1, 2, 2, 2, 1],
        'dorian': [2, 1, 2, 2, 2, 1, 2],
        'phrygian': [1, 2, 2, 2, 1, 2, 2],
        'lydian': [2, 2, 2, 1, 2, 2, 1],
        'myxolydian': [2, 2, 1, 2, 2, 1, 2],
        'aolian': [2, 1, 2, 2, 1, 2, 2],
        'locrian': [1, 2, 2, 1, 2, 2, 2],
    }

    def __init__(self, key, scale, lowest_note=0, highest_note=127):
        self._key = key.lower()
        self._scale = scale.lower()
        self._lowest_note = lowest_note
        self._highest_note = highest_note
        self._notes = []

        self._initialise_notes()
    
    def _initialise_notes(self):
        self._notes = []

        key_base = Scale.NOTES.index(self._key)

        self._notes = list(dropwhile(
            lambda x: x < self._lowest_note,
            takewhile(
                lambda x: x <= self._highest_note,
                accumulate(chain([key_base], cycle(Scale.SCALES[self._scale])))
            )
        ))
    
    def quantize_note(self, note):
        return [n for n in self._notes if n >= note][0]

    def get_notes(self):
        return self._notes
