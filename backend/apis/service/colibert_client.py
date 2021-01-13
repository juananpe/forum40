import json
import requests


class CoLiBertClient:
    def __init__(self):
        self.base_url = 'http://colibert:8080'

    def score_all_pairs(self, contexts, queries):
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        payload = {'contexts': contexts, 'queries': queries}

        response = requests.post(f'{self.base_url}/predict', headers=headers, data=json.dumps(payload))
        return response.json()
