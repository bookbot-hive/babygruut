import sqlite3

def merge_tables():
    try:
        # Connect to the source database
        source_conn = sqlite3.connect('/home/s44504/babygruut/gruut-lang-sw/gruut_lang_sw/lexicon.db')  # Replace with your source database name
        
        # Connect to the new database (will be created if it doesn't exist)
        new_conn = sqlite3.connect('/home/s44504/babygruut/gruut-lang-sw/gruut_lang_sw/merged_lexicon.db')
        
        # Create cursors
        source_cursor = source_conn.cursor()
        new_cursor = new_conn.cursor()
        
        # Create the new merged table
        new_cursor.execute('''
            CREATE TABLE IF NOT EXISTS merged_phonemes (
                id INTEGER PRIMARY KEY,
                word TEXT,
                phonemes TEXT,
                pron_order INTEGER,
                g2p_alignment TEXT,
                role TEXT
            )
        ''')
        
        # Perform the merge using SQL JOIN
        merge_query = '''
            SELECT 
                wp.id,
                wp.word,
                wp.phonemes,
                wp.pron_order,
                g2p.alignment as g2p_alignment,
                wp.role
            FROM word_phonemes wp
            LEFT JOIN g2p_alignments g2p ON wp.word = g2p.word
        '''
        
        # Execute the merge query and fetch results
        results = source_cursor.execute(merge_query).fetchall()
        
        # Insert the merged data into the new database
        new_cursor.executemany('''
            INSERT INTO merged_phonemes 
            (id, word, phonemes, pron_order, g2p_alignment, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', results)
        
        # Commit the changes
        new_conn.commit()
        
        print(f"Successfully merged tables. Total rows: {len(results)}")
        
    except sqlite3.Error as error:
        print(f"Error occurred: {error}")
    finally:
        # Close both connections
        if source_conn:
            source_conn.close()
        if new_conn:
            new_conn.close()
        print("Database connections closed.")

if __name__ == "__main__":
    merge_tables()