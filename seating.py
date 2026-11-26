"""GUIから独立した、ランダムな席割り。"""

import random
from collections.abc import Mapping, Sequence
from typing import Any


def assign_seats(trainees: Sequence[Mapping[str, Any]]) -> list[list[Mapping[str, Any]]]:
    """入力を変更せずシャッフルし、最大4人のグループに分ける。"""
    shuffled = list(trainees)
    random.shuffle(shuffled)
    return [shuffled[index : index + 4] for index in range(0, len(shuffled), 4)]
