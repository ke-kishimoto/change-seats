import itertools
import unittest

from affiliation_optimization import affiliation_counts, affiliation_imbalance, assign_affiliation_balanced


def people(companies):
    return [{"id": i, "名前": "同じ名前", "所属": company} for i, company in enumerate(companies)]


class AffiliationOptimizationTest(unittest.TestCase):
    def test_known_scores(self):
        trainees = people(["A"] * 4 + ["B"] * 4)
        self.assertEqual(affiliation_imbalance([trainees[:4], trainees[4:]]), 64)
        self.assertEqual(affiliation_imbalance([trainees[:2] + trainees[4:6], trainees[2:4] + trainees[6:]]), 0)
        twelve = people(["A"] * 6 + ["B"] * 3 + ["C"] * 3)
        groups, optimal = assign_affiliation_balanced(twelve)
        self.assertTrue(optimal)
        self.assertEqual(affiliation_imbalance(groups), 0)
        self.assertTrue(all(affiliation_counts(group)[0] == {"A": 2, "B": 1, "C": 1} for group in groups))

    def test_optimum_matches_exhaustive_search(self):
        for companies in (["A"] * 4 + ["B"] * 4,
                          ["A", "A", "A", "B", "C", "", None],
                          ["A"] * 5, [""] * 6,
                          ["A", "B", "C"]):
            with self.subTest(companies=companies):
                trainees = people(companies)
                groups, optimal = assign_affiliation_balanced(trainees)
                self.assertTrue(optimal)
                self.assertEqual([len(group) for group in groups], [min(4, len(trainees) - i) for i in range(0, len(trainees), 4)])
                self.assertEqual(sorted(person["id"] for group in groups for person in group), list(range(len(trainees))))
                self.assertEqual([person["所属"] for person in trainees], list(companies))
                if len(trainees) > 4:
                    candidates = itertools.combinations(range(len(trainees)), 4)
                    best = min(affiliation_imbalance([[trainees[i] for i in indexes], [person for i, person in enumerate(trainees) if i not in indexes]]) for indexes in candidates)
                else:
                    best = affiliation_imbalance([trainees])
                self.assertEqual(affiliation_imbalance(groups), best)

    def test_missing_and_empty_input(self):
        self.assertEqual(affiliation_counts(people(["A", "A", "", "  ", None])), ({"A": 2}, 3))
        with self.assertRaises(ValueError):
            assign_affiliation_balanced([])


if __name__ == "__main__":
    unittest.main()
