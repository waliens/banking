import abc

from transaction import Transaction


class BaseTagClassifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def predict(self, t: Transaction):
        """Given a transaction returns a tag identifier"""
        pass

