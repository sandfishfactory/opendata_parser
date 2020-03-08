from abc import ABCMeta, abstractmethod


class BaseParser(metaclass=ABCMeta):
    @abstractmethod
    def parse(self):
        pass
