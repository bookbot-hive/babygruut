import argparse
import pandas as pd
import sqlite3
from tqdm import tqdm

def update_database_with_g2p_alignment(db_path, csv_path, output_db_path, batch_size=5000):
    # Load data from the CSV file
    df = pd.read_csv(csv_path)

    # Connect to the SQLite database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check if the g2p_alignment column exists
        cursor.execute("PRAGMA table_info(word_phonemes)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'g2p_alignment' not in columns:
            cursor.execute("ALTER TABLE word_phonemes ADD COLUMN g2p_alignment TEXT")

        # Prepare the update statement
        update_stmt = '''
            UPDATE word_phonemes
            SET g2p_alignment = ?
            WHERE word = ? AND phonemes = ?
        '''

        # Update the database with data from the DataFrame in batches
        for start in tqdm(range(0, len(df), batch_size), desc="Updating database"):
            batch = df.iloc[start:start + batch_size]
            data = [(row['g2p_alignment'], row['word'], row['phonemes']) for _, row in batch.iterrows()]
            cursor.executemany(update_stmt, data)

        # Commit the changes
        conn.commit()

    # Save the updated database to the output path
    with sqlite3.connect(output_db_path) as output_conn:
        conn.backup(output_conn)

def main():
    parser = argparse.ArgumentParser(description='Update SQLite database with G2P alignment.')
    parser.add_argument('db_path', type=str, help='Path to the input SQLite database')
    parser.add_argument('csv_path', type=str, help='Path to the lexicon CSV file')
    parser.add_argument('output_db_path', type=str, help='Path to the output SQLite database')

    args = parser.parse_args()

    update_database_with_g2p_alignment(args.db_path, args.csv_path, args.output_db_path)

if __name__ == '__main__':
    main()