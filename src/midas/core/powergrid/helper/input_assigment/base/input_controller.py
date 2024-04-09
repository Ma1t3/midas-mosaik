from abc import abstractmethod


class InputController:
    @abstractmethod
    def assigment(self, input, time):
        """
        replace input variable
        :param input: invalid input
        :return: replaced input
        """
        pass
