#!/usr/bin/env python3
"""Tests the online gruut with the original gruut"""
from gruut import sentences
from tqdm import tqdm
import logging
import unittest

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger("gruut").setLevel(logging.INFO) 

TURSO_URL = os.getenv("TURSO_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

en_turso_config = {
    "url": TURSO_URL,
    "auth_token": TURSO_AUTH_TOKEN,
    "table": "en_phonemes"
}

sw_turso_config = {
    "url": TURSO_URL,
    "auth_token": TURSO_AUTH_TOKEN,
    "table": "sw_phonemes"
}


def get_phonemes_online(text, lang, turso_config=None):
    phonemes = []
    for sent in sentences(text, lang="en-us", turso_config=turso_config):
        for word in sent:
            if word.phonemes:
                phonemes.extend([phoneme for phoneme in word.phonemes])
    return " ".join(phonemes)

def get_phonemes_offline(text, lang, turso_config=None):
    phonemes = []
    for sent in sentences(text, lang="en-us"):
        for word in sent:
            if word.phonemes:
                phonemes.extend([phoneme for phoneme in word.phonemes])
    return " ".join(phonemes)
                
            

class TestPhonemeFunctions(unittest.TestCase):
    def test_phoneme_functions_english(self):
        logging.info("Testing English language phonemes")
        file_path = './test/english_test_sentences.txt'
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line_number, line in tqdm(enumerate(lines, start=1), total=len(lines), desc="English Test Progress"):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                online_phonemes = get_phonemes_online(line, "en_US", en_turso_config)
                offline_phonemes = get_phonemes_offline(line, "en_US")

                self.assertEqual(
                    online_phonemes, offline_phonemes,
                    f"Mismatch at line {line_number}: Online: {online_phonemes} | Offline: {offline_phonemes}"
                )

    def test_phoneme_functions_swahili(self):
        logging.info("Testing Swahili language phonemes")
        file_path = './test/swahili_test_sentences.txt'  # Update with the actual path to your file
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line_number, line in tqdm(enumerate(lines, start=1),total=len(lines), desc="Swahili Test Progress"):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                online_phonemes = get_phonemes_online(line, "sw", sw_turso_config)
                offline_phonemes = get_phonemes_offline(line, "sw")

                self.assertEqual(
                    online_phonemes, offline_phonemes,
                    f"Mismatch at line {line_number}: Online: {online_phonemes} | Offline: {offline_phonemes}"
                )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
