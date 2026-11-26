import itertools
import unittest

from gender_optimization import assign_gender_balanced, gender_counts, gender_imbalance


def people(genders):
    return [{"id": i, "名前": "同じ名前", "性別": gender} for i, gender in enumerate(genders)]


class GenderOptimizationTest(unittest.TestCase):
    def test_known_scores(self):
        trainees = people(["男性"] * 4 + ["女性"] * 4)
        self.assertEqual(gender_imbalance([trainees[:4], trainees[4:]]), 64)
        self.assertEqual(gender_imbalance([trainees[:2] + trainees[4:6], trainees[2:4] + trainees[6:]]), 0)

    def test_optimum_matches_exhaustive_search(self):
        for genders in (["男性"] * 4 + ["女性"] * 4,
                        ["男性", "男性", "男性", "女性", "その他", "未入力", "回答しない"],
                        ["男性"] * 5, ["未入力"] * 6,
                        ["男性", "女性", "その他"]):
            with self.subTest(genders=genders):
                trainees = people(genders)
                original = list(trainees)
                groups, optimal = assign_gender_balanced(trainees)
                self.assertTrue(optimal)
                self.assertEqual([len(g) for g in groups], [min(4, len(trainees) - i) for i in range(0, len(trainees), 4)])
                self.assertEqual(sorted(p["id"] for group in groups for p in group), list(range(len(trainees))))
                self.assertEqual(trainees, original)
                if len(trainees) > 4:
                    candidates = ([trainees[i] for i in indexes] for indexes in itertools.combinations(range(len(trainees)), 4))
                    best = min(gender_imbalance([group, [p for p in trainees if p not in group]]) for group in candidates)
                else:
                    best = gender_imbalance([trainees])
                self.assertEqual(gender_imbalance(groups), best)

    def test_counts_and_empty_input(self):
        self.assertEqual(gender_counts(people(["男性", "女性", "その他", "", None])), (1, 1, 3))
        with self.assertRaises(ValueError):
            assign_gender_balanced([])


if __name__ == "__main__":
    unittest.main()
