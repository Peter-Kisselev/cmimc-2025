from abc import ABC, abstractmethod
from typing import Any, List, Tuple
import numpy as np

class Bot(ABC):
    def __init__(self, index: int, difficulty: int):
        super().__init__()

    @abstractmethod
    def step(
        self,
        height: np.ndarray,
        neighbors: List[Tuple[int, int, int]]
    ) -> Tuple[int, int, int]:
        pass
