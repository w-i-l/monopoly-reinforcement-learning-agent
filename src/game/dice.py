import numpy as np

class DiceManager:
    def __init__(self, cache_size: int = 1000):
        self.cache_size = cache_size
        self.cache = self.__get_cache()


    def roll(self) -> tuple[int, int]:
        if len(self.cache) > 0:
            return tuple(self.cache.pop())
        
        self.cache = self.__set_cache()
        return tuple(self.cache.pop())
    
    
    def __get_cache(self) -> list[tuple[int, int]]:
        values = np.random.randint(1, 7, (self.cache_size, 2))
        values = map(lambda x: (int(x[0]), int(x[1])), values)
        self.cache = list(values)
        return self.cache
    