from abc import ABC, abstractmethod

import numpy as np


class ILineTracker(ABC):
    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> tuple[int, int, np.ndarray]:
        """
        Returns:
            tuple[int, int, np.ndarray]:
                left_speed, right_speed, debug_frame
        """
        raise NotImplementedError