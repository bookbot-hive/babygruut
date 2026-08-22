import sqlite3

def export_to_dict(db_path, dict_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query the word_phonemes table
    cursor.execute("SELECT word, phonemes FROM word_phonemes")
    
    # Open the .dict file for writing
    with open(dict_path, 'w') as dict_file:
        for word, phonemes in cursor.fetchall():
            # Write each word and its phonemes to the file
            dict_file.write(f"{word}\t{phonemes}\n")
    
    # Close the database connection
    conn.close()

if __name__ == "__main__":
# Example usage
    export_to_dict('/home/s44504/babygruut/gruut-lang-en/gruut_lang_en/lexicon.db', '/home/s44504/g2p_alignment/example/en_lexicon.dict')