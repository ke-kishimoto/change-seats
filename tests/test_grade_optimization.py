import itertools
import unittest

from grade_optimization import assign_grade_balanced, grade_imbalance, high_grade_count


def people(grades):
    return [{"id": i, "名前": "同じ名前", "成績": grade} for i, grade in enumerate(grades)]


class GradeOptimizationTest(unittest.TestCase):
    def test_known_scores(self):
        trainees = people(["A", "B", "A", "B", "C", "D", "E", "C"])
        self.assertEqual(grade_imbalance([trainees[:4], trainees[4:]]), 32)
        self.assertEqual(grade_imbalance([trainees[:2] + trainees[4:6], trainees[2:4] + trainees[6:]]), 0)
        nine = people(["A", "B"] + ["C"] * 7)
        self.assertEqual(grade_imbalance([[nine[0]] + nine[2:5], [nine[1]] + nine[5:8], nine[8:]]), 4)
        self.assertEqual(grade_imbalance([[nine[0]] + nine[2:5], nine[5:9], [nine[1]]]), 16)

    def test_optimum_matches_exhaustive_search(self):
        for grades in (["A", "A", "B", "B", "C", "D", "E", "E"],
                       ["A", "B", "C", "C", "D", "E", "E"],
                       ["A"] * 5, ["E"] * 6, ["A", "C", "E"]):
            with self.subTest(grades=grades):
                trainees = people(grades)
                groups, optimal = assign_grade_balanced(trainees)
                self.assertTrue(optimal)
                self.assertEqual([len(group) for group in groups], [min(4, len(trainees) - i) for i in range(0, len(trainees), 4)])
                self.assertEqual(sorted(p["id"] for group in groups for p in group), list(range(len(trainees))))
                self.assertEqual([person["成績"] for person in trainees], list(grades))
                if len(trainees) > 4:
                    best = min(grade_imbalance([[trainees[i] for i in indices], [person for i, person in enumerate(trainees) if i not in indices]]) for indices in itertools.combinations(range(len(trainees)), 4))
                else:
                    best = grade_imbalance([trainees])
                self.assertEqual(grade_imbalance(groups), best)

    def test_missing_and_empty_input(self):
        self.assertEqual(high_grade_count(people(["A", "B", "C", "D", "E"])), 2)
        for data in ([], people(["A", None]), people(["A", ""])):
            with self.subTest(data=data), self.assertRaises(ValueError):
                assign_grade_balanced(data)
        with self.assertRaises(ValueError):
            grade_imbalance([people(["A", None])])


if __name__ == "__main__":
    unittest.main()
