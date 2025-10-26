from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")
class Setting(BaseModel, Generic[T]):
    name: str
    setting_value: T

class Workflow:
    def __init__(self, n_inputs: int) -> None:
        self.n_inputs = n_inputs
        self.name: str = ""

    def function(self, inputs: list) -> list:
        """ Override this function to add the correct functionality of the workflow and
        ensure the correct order of parameters. All inputs given to the workflow are
        available and the arguments set by the __init__ override can be used with
        'self.args'."""
        return inputs

    def run(self, inputs: list) -> list:
        """ This function will be executed when the workflow is applied to an input. It
        has to handle the correct order of arguments in the corresponding function
        call. All parameters are included in the settings."""
        if len(inputs) != self.n_inputs:
            raise ValueError(f"Number of inputs does not match the expected number: {len(inputs)} != {self.n_inputs}")
        res = inputs.copy()
        try:
            res = self.function(res)
        except Exception as e:
            # TODO: Error handling
            print(e)
        return res


