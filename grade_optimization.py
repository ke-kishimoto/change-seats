"""成績A・Bの人数の偏りとグループ分け。"""

import random

from ortools.sat.python import cp_model

from trainee_file import GRADES


def high_grade_count(group):
    return sum(person.get("成績") in ("A", "B") for person in group)


def grade_imbalance(groups):
    """成績が全員分ある場合、A・Bの人数の偏りを返す。"""
    trainees = [person for group in groups for person in group]
    if any(person.get("成績") not in GRADES for person in trainees):
        raise ValueError("成績の偏りを計算するには全員の成績が必要です。")
    total = len(trainees)
    high_total = high_grade_count(trainees)
    return sum(abs(total * high_grade_count(group) - len(group) * high_total) for group in groups)


def assign_grade_balanced(trainees):
    """A・Bの比率が全体に近いグループを作り、グループ内を混ぜる。"""
    total = len(trainees)
    if not total:
        raise ValueError("研修生を1人以上入力してください。")
    if any(person.get("成績") not in GRADES for person in trainees):
        raise ValueError("成績を考慮するには全員の成績を入力してください。")

    group_sizes = [min(4, total - start) for start in range(0, total, 4)]
    high_indices = [i for i, person in enumerate(trainees) if person["成績"] in ("A", "B")]
    model = cp_model.CpModel()
    x = {(i, g): model.new_bool_var(f"person_{i}_group_{g}")
         for i in range(total) for g in range(len(group_sizes))}
    for i in range(total):
        model.add_exactly_one(x[i, g] for g in range(len(group_sizes)))

    deviations = []
    for g, size in enumerate(group_sizes):
        model.add(sum(x[i, g] for i in range(total)) == size)
        deviation = model.new_int_var(0, total * size, f"grade_deviation_{g}")
        model.add_abs_equality(
            deviation, total * sum(x[i, g] for i in high_indices) - size * len(high_indices)
        )
        deviations.append(deviation)
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
