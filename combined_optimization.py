"""性別と所属の偏りを重み付けして同時に最適化する。"""

import random
from ortools.sat.python import cp_model

from affiliation_optimization import add_affiliation_deviations
from gender_optimization import add_gender_deviations


def assign_combined_balanced(trainees, gender_weight=1, affiliation_weight=1):
    if not trainees:
        raise ValueError("研修生を1人以上入力してください。")
    if (type(gender_weight) is not int or type(affiliation_weight) is not int
            or not 0 <= gender_weight <= 10 or not 0 <= affiliation_weight <= 10
            or gender_weight + affiliation_weight == 0):
        raise ValueError("重みは0〜10の整数とし、少なくとも一方を1以上にしてください。")

    total = len(trainees)
    group_sizes = [min(4, total - i) for i in range(0, total, 4)]
    model = cp_model.CpModel()
    x = {(i, g): model.new_bool_var(f"person_{i}_group_{g}")
         for i in range(total) for g in range(len(group_sizes))}
    for i in range(total):
        model.add_exactly_one(x[i, g] for g in range(len(group_sizes)))
    for g, size in enumerate(group_sizes):
        model.add(sum(x[i, g] for i in range(total)) == size)

    gender_deviations = add_gender_deviations(model, x, group_sizes, trainees)
    affiliation_deviations = add_affiliation_deviations(model, x, group_sizes, trainees)
    model.minimize(gender_weight * sum(gender_deviations) + affiliation_weight * sum(affiliation_deviations))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        messages = {cp_model.INFEASIBLE: "条件を満たす配置が見つかりませんでした。",
                    cp_model.MODEL_INVALID: "最適化モデルに問題があります。",
                    cp_model.UNKNOWN: "制限時間内に配置を見つけられませんでした。"}
        raise RuntimeError(messages.get(status, "席替えを実行できませんでした。"))
    groups = [[trainees[i] for i in range(total) if solver.value(x[i, g])]
              for g in range(len(group_sizes))]
    for group in groups:
        random.shuffle(group)
    return groups, status == cp_model.OPTIMAL
