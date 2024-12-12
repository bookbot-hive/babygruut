import argparse
import json
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime

from azure.cosmos import CosmosClient
from tqdm.auto import tqdm
from utils import get_phoneme_syllable

# Constants
URL = "https://bookbot.documents.azure.com:443/"
KEY = "LpobOVoLunTzdwKTw8ZOxBdcfOhCicxffBDBGLbW7agGv4ROSb6VcP1Fdqe8kMtigiCkTHWlMs1kQjjmbjoxOg=="
DATABASE_NAME = "Bookbot"

# Create a Cosmos client
client = CosmosClient(URL, credential=KEY)
database = client.get_database_client(DATABASE_NAME)
word_container = database.get_container_client("WordUniversal")


def fetch_existing_records(language):
    query_iterable = word_container.query_items(
        query=f'SELECT * from c WHERE c.language = "{language}" and not is_defined(c.deletedAt)',
        partition_key="default",
        max_item_count=10000,
    )
    pager = query_iterable.by_page()

    existing_records = []
    print("Fetching existing records...")
    while True:
        page = list(pager.next())
        existing_records += page
        continuation_token = pager.continuation_token

        if not continuation_token:
            break
        pager = query_iterable.by_page(continuation_token)
    print("Existing records fetched.")
    return existing_records


def fetch_lexicons(sqlite_db_path, table_name):
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute(f'SELECT word, phonemes, g2p_alignment, role FROM {table_name}')
    columns = [desc[0] for desc in cursor.description]
    lexicons = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return lexicons


def update_ipa(language, sqlite_db_path, table_name):
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    success_logs = []
    error_logs = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    existing_records = fetch_existing_records(language)
    lexicons = fetch_lexicons(sqlite_db_path, table_name)

    for lex_item in tqdm(lexicons, desc="Updating IPA for lexicon"):
        word = lex_item['word']
        phonemes = lex_item['phonemes']
        g2p_alignment = lex_item['g2p_alignment']
        lex_role = lex_item.get('role') or ''

        if lex_role.startswith('gruut:'):
            lex_role = lex_role[len('gruut:'):]

        for record in existing_records:
            if record.get('word') != word:
                continue

            record_pos = record.get('pos') or ''
            if not record_pos or record_pos == lex_role and g2p_alignment:
                try:
                    ipa = get_phoneme_syllable(word=word, 
                                               word_with_syll=record['syllable'], 
                                               phonemes=phonemes, 
                                               alignment=g2p_alignment)
                    
                    success_logs.append({
                        "word": word,
                        "word_with_syll": record['syllable'],
                        "phonemes": phonemes,
                        "ipa": ipa,
                        "role": lex_role
                    })
                    
                    record['ipa'] = ipa
                    record['updatedAt'] = round(time.time() * 1000)
                    # word_container.replace_item(record, record)
                    break
                    
                except Exception as e:
                    error_logs.append({
                        "word": word,
                        "word_with_syll": record['syllable'],
                        "phonemes": phonemes,
                        "role": lex_role,
                        "error": str(e)
                    })
                    print(f"Error getting ipa for word: {word}")
                    print(f"Error: {e}\n")
                    continue

    with open(f"{logs_dir}/success_log_{language}_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(success_logs, f, indent=2, ensure_ascii=False)
        
    with open(f"{logs_dir}/error_log_{language}_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(error_logs, f, indent=2, ensure_ascii=False)

    print(f"Logs have been written to {logs_dir}/")
    print("Lexicon import completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update IPA using lexicon data.")
    parser.add_argument("language", type=str, help="Language code for the lexicon.")
    parser.add_argument("sqlite_db_path", type=str, help="Path to the SQLite database.")
    parser.add_argument("--table_name", type=str, default="word_phonemes", 
                       help="Name of the SQLite table (default: word_phonemes)")
    args = parser.parse_args()

    update_ipa(args.language, args.sqlite_db_path, args.table_name)