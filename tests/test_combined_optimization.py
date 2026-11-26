import itertools
import unittest

from affiliation_optimization import affiliation_imbalance
from combined_optimization import assign_combined_balanced
from gender_optimization import gender_imbalance


class CombinedOptimizationTest(unittest.TestCase):
    def test_matches_exhaustive_search(self):
        data = [
            {"id": i, "性別": gender, "所属": company}
            for i, (gender, company) in enumerate([
                ("男性", "A"), ("男性", "A"), ("男性", "B"), ("女性", "A"),
                ("女性", "B"), ("女性", "C"), ("未入力", ""),
            ])
        ]
        for gender_weight, company_weight in ((1, 1), (5, 1), (1, 5), (0, 1), (1, 0)):
            with self.subTest(weights=(gender_weight, company_weight)):
                groups, optimal = assign_combined_balanced(data, gender_weight, company_weight)
                self.assertTrue(optimal)
                self.assertEqual([len(group) for group in groups], [4, 3])
                self.assertEqual(sorted(p["id"] for group in groups for p in group), list(range(len(data))))
                score = lambda gs: gender_weight * gender_imbalance(gs) + company_weight * affiliation_imbalance(gs)
                expected = min(score([[data[i] for i in indices], [p for i, p in enumerate(data) if i not in indices]]) for indices in itertools.combinations(range(len(data)), 4))
                self.assertEqual(score(groups), expected)

    def test_empty_fields_and_invalid_inputs(self):
        groups, optimal = assign_combined_balanced([{"性別": "", "所属": ""}] * 5)
        self.assertTrue(optimal)
        self.assertEqual(gender_imbalance(groups) + affiliation_imbalance(groups), 0)
        for args in (([], 1, 1), ([{}], 0, 0), ([{}], -1, 1), ([{}], 1.5, 1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                assign_combined_balanced(*args)


if __name__ == "__main__":
    unittest.main()
