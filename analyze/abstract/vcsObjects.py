from abc import ABC, abstractmethod


class VcsObject(ABC):

    @abstractmethod
    def get_json(self):
        raise NotImplementedError
