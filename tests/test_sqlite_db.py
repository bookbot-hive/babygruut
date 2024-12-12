import itertools
import logging
import sqlite3
import typing
from pathlib import Path

from gruut.const import PHONEMES_TYPE

# -----------------------------------------------------------------------------

_LOGGER = logging.getLogger("gruut.phonemize")

ROLE_TO_PHONEMES = typing.Dict[str, PHONEMES_TYPE]

WORD_TRANSFORM_TYPE = typing.Callable[[str], str]

class SqlitePhonemizer:
    def __init__(
        self,
        db_conn: sqlite3.Connection,
    ):
        self.db_conn = db_conn
    def __call__(self, word: str) -> typing.Optional[PHONEMES_TYPE]:
        cursor = self.db_conn.execute(
                "SELECT role, phonemes FROM merged_phonemes WHERE word = ? ORDER BY pron_order",
                (word,),
            )
        for row in cursor:
            print(row)
            
if __name__ == "__main__":
    db_conn = sqlite3.connect("/home/s44504/babygruut/gruut-lang-en/gruut_lang_en/en_lexicon.db")
    phonemizer = SqlitePhonemizer(db_conn)
    phonemizer("abbreviate")
