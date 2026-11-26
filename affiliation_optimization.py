"""所属の偏りの評価と、OR-Toolsを使ったグループ分け。"""

import random
from collections import Counter

from ortools.sat.python import cp_model


def affiliation_counts(group):
    """企業ごとの人数と、所属が未入力の人数を返す。"""
    counts = Counter()
    missing = 0
    for person in group:
        company = person.get("所属")
        if isinstance(company, str) and company.strip():
            counts[company] += 1
        else:
            missing += 1
    return counts, missing


def affiliation_imbalance(groups):
    """各企業のグループ内人数と全体比率との差を合計する。"""
    total = sum(map(len, groups))
    all_counts = Counter()
    group_counts = []
    for group in groups:
        counts, _ = affiliation_counts(group)
        group_counts.append(counts)
        all_counts.update(counts)
    return sum(
        abs(total * counts[company] - len(group) * company_total)
        for group, counts in zip(groups, group_counts)
        for company, company_total in all_counts.items()
    )


def assign_affiliation_balanced(trainees):
    """所属の偏りが小さいグループを作り、グループ内の席を混ぜる。"""
    total = len(trainees)
    if not total:
        raise ValueError("研修生を1人以上入力してください。")
    group_sizes = [min(4, total - start) for start in range(0, total, 4)]
    company_indices = {}
    for index, person in enumerate(trainees):
        company = person.get("所属")
        if isinstance(company, str) and company.strip():
            company_indices.setdefault(company, []).append(index)

    model = cp_model.CpModel()
    x = {(i, g): model.new_bool_var(f"person_{i}_group_{g}")
         for i in range(total) for g in range(len(group_sizes))}
    for i in range(total):
        model.add_exactly_one(x[i, g] for g in range(len(group_sizes)))

    deviations = []
    for g, size in enumerate(group_sizes):
        model.add(sum(x[i, g] for i in range(total)) == size)
        for company_index, indices in enumerate(company_indices.values()):
            deviation = model.new_int_var(0, total * size, f"company_{company_index}_deviation_{g}")
            model.add_abs_equality(
                deviation, total * sum(x[i, g] for i in indices) - size * len(indices)
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
