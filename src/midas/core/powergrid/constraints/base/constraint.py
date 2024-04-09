from abc import abstractmethod


class Constraint:
    def __init__(self, constraint_container):
        self.constraint_container = constraint_container
        self.satisfied = True
        self.violated_value = None

    @abstractmethod
    def check(self, time):
        """
        Check if the constraint is violated or not
        :param time: Current datetime
        :return bool: True if violated
        """
        pass

    @abstractmethod
    def get_key(self):
        """
        Constraint Key
        :return string: Key
        """
        pass
