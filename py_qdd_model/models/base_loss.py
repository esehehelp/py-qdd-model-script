from abc import ABC, abstractmethod

class LossModel(ABC):
    @abstractmethod
    def calculate_loss(self, *args, **kwargs):
        """引数・返却は実装毎に定義する"""
        pass
