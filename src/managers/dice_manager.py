import numpy as np


class DiceManager:
    """
    High-performance dice rolling manager with pre-generated value caching.

    Attributes
    ----------
    cache_size : int
        Number of dice roll pairs to pre-generate in each batch
    cache : list[tuple[int, int]]
        Current cache of pre-generated dice roll pairs
    """


    def __init__(self, cache_size: int = 1000):
        """
        Initialize the dice manager with specified cache size.
        
        Parameters
        ----------
        cache_size : int, default 1000
            Number of dice roll pairs to pre-generate in each cache batch.
            Larger values improve performance at the cost of memory usage.
            Typical values: 100-5000 depending on game length and memory constraints.
        """
        self.cache_size = cache_size
        self.cache = self.__get_cache()


    def roll(self) -> tuple[int, int]:
        """
        Generate a dice roll by returning the next cached value.
        
        Returns
        -------
        tuple[int, int]
            Pair of dice values (die1, die2) where each value is 1-6
        """
        if len(self.cache) > 0:
            return tuple(self.cache.pop())
        
        # Cache is empty, replenish and return a value
        self.cache = self.__get_cache()
        return tuple(self.cache.pop())


    def __get_cache(self) -> list[tuple[int, int]]:
        """
        Generate a new cache of random dice roll pairs.

        Returns
        -------
        list[tuple[int, int]]
            List of dice roll pairs ready for consumption
        """
        # Generate cache_size pairs of dice rolls (1-6 each)
        values = np.random.randint(1, 7, (self.cache_size, 2))
        
        # Convert numpy arrays to Python int tuples for compatibility
        values = map(lambda x: (int(x[0]), int(x[1])), values)
        self.cache = list(values)
        return self.cache