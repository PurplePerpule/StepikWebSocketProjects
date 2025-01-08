from pydantic import BaseModel
from typing import List

class Player(BaseModel):
    sid: str
    name: str
    score: int = 0

class Question(BaseModel):
    number: int
    topic: int
    text: str
    options: List[str]
    answer: int

class Game(BaseModel):
    players: List[Player]
    questions: List[Question]
    current_question_index: int = 0

    def get_current_question(self) -> Question:
        return self.questions[self.current_question_index]

    def next_question(self) -> bool:
        self.current_question_index += 1
        return self.current_question_index < len(self.questions)
