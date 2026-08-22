import logging
import typing
import requests
from gruut.const import PHONEMES_TYPE

# ... existing code ...

class CloudflarePhonemizer:
    def __init__(
        self,
        api_url: str,
        bearer_token: str,
    ):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {bearer_token}"}

    def __call__(self, word: str) -> typing.Optional[PHONEMES_TYPE]:
        payload = {
            "action": "READ",
            "table": "en_phonemes",  # Adjust table name if needed
            "where": "",
            "params": []
        }
        
        response = requests.post(self.api_url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        results = response.json()
        for row in results:
            print(row)  # Keeping the same print behavior as original
            
if __name__ == "__main__":
    phonemizer = CloudflarePhonemizer(
        api_url="https://lexiconsdb.bookbotkids.workers.dev",
        bearer_token="6837ec97-2670-4eeb-8a5e-0f65271c9ebf"
    )
    phonemizer("hello")