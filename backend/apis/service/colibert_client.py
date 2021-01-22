from typing import List

import json
import requests


class CoLiBertClient:
    def __init__(self):
        self.base_url = 'http://colibert:8080'

    def score_all_pairs(self, queries: List[str], contexts: List[str]) -> List[List[float]]:
        """
        Score the link strength between each query-context pair
        :param queries: A list of texts that refer to the concepts mentioned in contexts
        :param contexts: A list of texts that that give the contexts the queries might refer to
        :return: A len(queries)×len(contexts) matrix as list of lists representing the link scores.
        Given res, the value at res[i][j] is the link strength from queries[i] to contexts[j].
        """

        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        payload = {'queries': queries, 'contexts': contexts}

        response = requests.post(f'{self.base_url}/predict', headers=headers, data=json.dumps(payload))
        return response.json()
