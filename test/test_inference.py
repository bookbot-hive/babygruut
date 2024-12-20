#!/usr/bin/env python3
"""Tests the online gruut with the original gruut"""
from gruut import sentences
from tqdm import tqdm
import logging
import unittest
import os
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
                

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    result = get_phonemes_online("Before we read a book", "en_US", en_turso_config)
    print(result)
