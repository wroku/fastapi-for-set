from typing import Self

from pydantic import BaseModel


class Record(BaseModel):
    player: str
    score: int
    time: float

    @classmethod
    def from_tuple(cls, record_tuple: tuple) -> Self:
        keys = list(cls.__pydantic_fields__.keys())
        dict = {key: value for key, value in zip(keys, record_tuple)}
        return cls(**dict)

    def is_valid_successor(self, previous: Self) -> bool:
        MAX_SCORE = 81
        state_transition_constraints = [
            self.player == previous.player or previous.player == "Anonym",
            previous.score - 1 <= self.score <= previous.score + 3,
            self.time >= previous.time,
            self.score <= MAX_SCORE,
        ]

        return all(state_transition_constraints)