import os
import requests
from typing import List

from config import settings


class EmbeddingServiceClient:
    def embed(self, texts: List[str]) -> List[List[float]]:
        url = os.getenv('EMBEDDING_SERVICE_URL', settings.EMBEDDING_SERVICE_URL)

        response = requests.post(
            url,
            json={"texts": texts},
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )

        if not response.ok:
            response.raise_for_status()

        return response.json()
