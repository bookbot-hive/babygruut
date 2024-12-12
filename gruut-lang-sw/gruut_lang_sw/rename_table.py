import sqlite3

def rename_table(database_path, old_table_name, new_table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    try:
        # Rename the table
        cursor.execute(f"ALTER TABLE {old_table_name} RENAME TO {new_table_name};")
        print(f"Table '{old_table_name}' has been renamed to '{new_table_name}'.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Commit the changes and close the connection
        conn.commit()
        conn.close()

# Example usage
database_path = '/home/s44504/babygruut/gruut-lang-sw/gruut_lang_sw/sw_lexicon.db'
rename_table(database_path, 'merged_phonemes', 'word_phonemes')
