"""性別の偏りの評価と、OR-Toolsを使ったグループ分け。"""

import random
from collections import Counter

from ortools.sat.python import cp_model


def gender_counts(group):
    counts = Counter(person.get("性別") for person in group)
    return counts["男性"], counts["女性"], len(group) - counts["男性"] - counts["女性"]


def gender_imbalance(groups):
    """各グループの男女の人数と全体比率との差の合計を返す。"""
    total = sum(map(len, groups))
    men = sum(gender_counts(group)[0] for group in groups)
    women = sum(gender_counts(group)[1] for group in groups)
    return sum(
        abs(total * male - len(group) * men)
        + abs(total * female - len(group) * women)
        for group in groups
        for male, female, _ in [gender_counts(group)]
    )


def add_gender_deviations(model, x, group_sizes, trainees):
    """共通の割り当て変数に対する性別の偏りをモデルに追加する。"""
    total = len(trainees)
    deviations = []
    for label, gender in (("male", "男性"), ("female", "女性")):
        indices = [i for i, person in enumerate(trainees) if person.get("性別") == gender]
        for g, size in enumerate(group_sizes):
            deviation = model.new_int_var(0, total * size, f"{label}_deviation_{g}")
            model.add_abs_equality(deviation, total * sum(x[i, g] for i in indices) - size * len(indices))
            deviations.append(deviation)
    return deviations


def assign_gender_balanced(trainees):
    """グループを最適化し、各グループ内の席順をランダムにする。"""
    total = len(trainees)
    if not total:
        raise ValueError("研修生を1人以上入力してください。")
    group_sizes = [min(4, total - start) for start in range(0, total, 4)]

    model = cp_model.CpModel()
    x = {(i, g): model.new_bool_var(f"person_{i}_group_{g}")
         for i in range(total) for g in range(len(group_sizes))}
    for i in range(total):
        model.add_exactly_one(x[i, g] for g in range(len(group_sizes)))

    for g, size in enumerate(group_sizes):
        model.add(sum(x[i, g] for i in range(total)) == size)
    deviations = add_gender_deviations(model, x, group_sizes, trainees)
    model.minimize(sum(deviations))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        messages = {
            cp_model.INFEASIBLE: "条件を満たす配置が見つかりませんでした。",
            cp_model.MODEL_INVALID: "最適化モデルに問題があります。",
            cp_model.UNKNOWN: "制限時間内に配置を見つけられませんでした。",
        }
        raise RuntimeError(messages.get(status, "席替えを実行できませんでした。"))

    groups = [[trainees[i] for i in range(total) if solver.value(x[i, g])]
              for g in range(len(group_sizes))]
    for group in groups:
        random.shuffle(group)
    return groups, status == cp_model.OPTIMAL
