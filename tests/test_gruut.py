#!/usr/bin/env python3
"""Tests for phonemization"""
import unittest
import logging
from gruut import sentences

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger("gruut").setLevel(logging.INFO) 


class PhonemizerTestCase(unittest.TestCase):
    """Test cases for phonemization"""

    def test_en_us(self):
        """English test"""
        self.assertEqual(
            get_phonemes("My hovercraft is full of eels.", "en_US", en_turso_config),
            [
                ("My", ["m", "ˈaɪ"]),
                ("hovercraft", ["h", "ˈʌ", "v", "ɚ", "k", "ɹ", "ˌæ", "f", "t"],),
                ("is", ["ˈɪ", "z"]),
                ("full", ["f", "ˈʊ", "l"]),
                ("of", ["ə", "v"]),
                ("eels", ["ˈi", "l", "z"]),
                (".", ["‖"]),
            ],
        )
        
    def test_sw(self):
        """Swahili test"""
        self.assertEqual(
            get_phonemes("Gari langu linaloangama limejaa na mikunga.", "sw", sw_turso_config),
            [
                ("Gari", ["ɠ", "ɑ", "ɾ", "i"]),
                ("langu", ["l", "ɑ", "ᵑg", "u"],),
                (
                    "linaloangama",
                    ["l", "i", "n", "ɑ", "l", "ɔ", "ɑ", "ᵑg", "ɑ", "m", "ɑ"],
                ),
                ("limejaa", ["l", "i", "m", "ɛ", "ʄ", "ɑ", "ɑ"]),
                ("na", ["n", "ɑ"]),
                ("mikunga", ["m", "i", "k", "u", "ᵑg", "ɑ"]),
                (".", ["‖"]),
            ],
        )
      

def get_phonemes(text, lang):
    """Return (text, phonemes) for each word"""
    sentence = next(sentences(
        text, 
        lang=lang,
    ))
    return [(w.text, w.phonemes) for w in sentence if w.phonemes]


if __name__ == "__main__":
    unittest.main()