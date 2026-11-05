"""기본 데이터, 입력 검사 및 JSON 저장 동작을 확인합니다."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import Quiz, QuizGame, default_quizzes


class QuizTests(unittest.TestCase):
    def test_default_questions_are_valid_four_choice_quizzes(self):
        quizzes = default_quizzes()
        self.assertGreaterEqual(len(quizzes), 5)
        self.assertTrue(all(len(quiz.choices) == 4 for quiz in quizzes))
        self.assertTrue(all(quiz.answer in range(1, 5) for quiz in quizzes))

    def test_quiz_rejects_invalid_answer(self):
        with self.assertRaises(ValueError):
            Quiz("질문", ["가", "나", "다", "라"], 5)

    def test_score_and_questions_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            game = QuizGame(state_file)
            game.best_score = 4
            game.quizzes.append(Quiz("추가 문제", ["가", "나", "다", "라"], 2))
            game.save_state()

            reloaded = QuizGame(state_file)
            self.assertEqual(reloaded.best_score, 4)
            self.assertEqual(len(reloaded.quizzes), 6)
            saved = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(saved["best_score"], 4)
            self.assertFalse(state_file.with_name("state.json.tmp").exists())

    def test_invalid_numeric_input_retries(self):
        with patch("builtins.input", side_effect=["abc", "9", "2"]):
            self.assertEqual(QuizGame.read_number("선택: ", 1, 5), 2)

    def test_corrupt_state_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            broken_values = ["{broken", "[]", '{"quizzes": "not-a-list"}']
            for broken_value in broken_values:
                with self.subTest(value=broken_value):
                    state_file.write_text(broken_value, encoding="utf-8")
                    game = QuizGame(state_file)
                    self.assertEqual(len(game.quizzes), 5)
                    self.assertEqual(game.best_score, 0)


if __name__ == "__main__":
    unittest.main()
