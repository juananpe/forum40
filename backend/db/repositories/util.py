import math
from typing import Any

from pypika import Parameter, CustomFunction


Random = CustomFunction('random')


class QueryArguments:
    alphabet = ''.join([chr(ord('a') + i) for i in range(26)])

    def __init__(self):
        self.values = {}
        self.__key_num = 1

    def __next_key(self) -> str:
        key = self.__key(self.__key_num)
        self.__key_num += 1
        return key

    def __key(self, n: int) -> str:
        b = len(QueryArguments.alphabet)
        key_len = 1 + math.floor(math.log(n-1, b)) if n > 1 else 1
        return ''.join([QueryArguments.alphabet[n // b ** s % b - 1] for s in range(key_len)])[::-1]

    def add(self, value: Any):
        key = self.__next_key()
        self.values[key] = value
        return Parameter(f'%({key})s')
