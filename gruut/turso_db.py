import typing
import asyncio 
import logging
import sqlite3
import libsql_client
import asyncio 
import time
import os

from gruut.const import PHONEMES_TYPE
from gruut.phonemize import SqlitePhonemizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger("gruut.turso_db")

TURSO_URL = os.getenv("TURSO_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

class TursoDB:
    """Phonemizer that uses Turso with an in-memory SQLite cache"""

    def __init__(
        self,
        turso_client,
        memory_conn,
        table_name,
        **phonemizer_args
    ):
        self.turso_client = turso_client
        self.memory_conn = memory_conn
        self.phonemizer_args = phonemizer_args
        self.table_name = table_name
        
    @classmethod
    async def create(
        cls,
        url: str,
        auth_token: str,
        table_name: str,
        **phonemizer_args
    ):
        turso_client = None
        try:
            # Initialize Turso client
            turso_client = libsql_client.create_client(
                url=url,
                auth_token=auth_token
            )
            # Create in-memory cache
            memory_conn = sqlite3.connect(":memory:")
            # Create instance
            instance = cls(turso_client, memory_conn, table_name, **phonemizer_args)
            instance._initialize_memory_schema()
            # Load turso database into memory database
            _LOGGER.info("Loading data into memory...")
            await instance._load_data_into_memory()
            instance.phonemizer = SqlitePhonemizer(
                db_conn=instance.memory_conn,
                **instance.phonemizer_args
            )
            return instance
        except Exception as e:
            _LOGGER.error(f"Error during TursoDB creation: {e}")
            raise

    def _initialize_memory_schema(self):
        """Create the schema in the in-memory SQLite database."""
        schema = """
        CREATE TABLE word_phonemes (
            word TEXT,
            phonemes TEXT,
            pron_order INTEGER,
            role TEXT
        );
        """
        self.memory_conn.execute(schema)

    async def _load_data_into_memory(self):
        """Load all rows from Turso into the in-memory database in batches."""
        start_time = time.time()
        _LOGGER.info("Starting to load data from Turso...")
        
        batch_size = 5000  # Increased batch size
        try:
            count_result = await self.turso_client.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            total_count = count_result.rows[0][0]
            
            self.memory_conn.execute("PRAGMA synchronous = OFF")
            self.memory_conn.execute("PRAGMA journal_mode = OFF")
            
            self.memory_conn.execute("BEGIN TRANSACTION")
        
            tasks = []
            for offset in range(0, total_count, batch_size):
                query = f"""
                    SELECT word, phonemes, pron_order, role 
                    FROM {self.table_name} 
                    LIMIT {batch_size} 
                    OFFSET {offset}
                """
                tasks.append(self.turso_client.execute(query))
            
            results = await asyncio.gather(*tasks)
            
            total_rows = 0
            for result in results:
                rows = result.rows
                if rows:
                    total_rows += len(rows)
                    self.memory_conn.executemany(
                        "INSERT INTO word_phonemes (word, phonemes, pron_order, role) VALUES (?, ?, ?, ?)",
                        rows
                    )
            
            self.memory_conn.commit()
            
        except Exception as e:
            self.memory_conn.rollback()
            if self.memory_conn is not None:
                try:
                    self.memory_conn.close()
                except Exception as close_error:
                    _LOGGER.error(f"Error closing memory connection: {close_error}")
            raise e
        
        finally:
            # Ensure the client session is closed
            if self.turso_client is not None:
                try:
                    await self.turso_client.close()
                except Exception as e:
                    _LOGGER.error(f"Error closing Turso client: {e}")
        
        total_time = time.time() - start_time
        _LOGGER.info(f"Loaded {total_rows} rows from {self.table_name} table in {total_time:.2f} seconds")

    async def get_phonemes_direct(self, word: str, role: str = None) -> list[tuple]:
        """Query phonemes directly from Turso database, bypassing the cache.
        
        Args:
            word: The word to look up
            role: Optional part of speech role (e.g., 'noun', 'verb')
            
        Returns:
            List of tuples containing (word, phonemes, pron_order, role)
        """
        try:
            if role:
                query = f"""
                    SELECT word, phonemes, pron_order, role 
                    FROM {self.table_name}
                    WHERE word = ? AND role = ?
                """
                result = await self.turso_client.execute(query, [word, role])
            else:
                query = f"""
                    SELECT word, phonemes, pron_order, role 
                    FROM {self.table_name}
                    WHERE word = ?
                """
                result = await self.turso_client.execute(query, [word])
            
            return result.rows
            
        except Exception as e:
            _LOGGER.error(f"Error querying Turso database: {e}")
            return []

if __name__ == "__main__":
    async def main():
        
        turso_config = {
            "url": TURSO_URL,
            "auth_token": TURSO_AUTH_TOKEN,
            "table": "sw_phonemes"
        }

        # Create the TursoDB instance first
        turso = await TursoDB.create(
            url=turso_config["url"],
            auth_token=turso_config["auth_token"],
            table_name=turso_config["table"]
        )
        
        try:
            # Test direct phoneme lookup
            print(f"SqlitePhonemizer:")
            print(f"All pronunciations for 'langu': {turso.phonemizer('langu')}")
            print(f"All pronunciations for 'gari': {turso.phonemizer('gari')}")
            print(f"="*80)
            
            print(f"TursoDB.get_phonemes_direct:")
            print(f"All pronunciations for 'langu': {await turso.get_phonemes_direct('langu')}")
            print(f"All pronunciations for 'gari': {await turso.get_phonemes_direct('gari')}")
            print(f"="*80)
        finally:
            await turso.close()

    asyncio.run(main())
