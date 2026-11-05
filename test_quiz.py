"""기본 데이터, 입력 검사 및 JSON 저장 동작을 확인합니다."""

import json
import io
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
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
            game.games_played = 3
            game.last_score = 2
            game.quizzes.append(Quiz("추가 문제", ["가", "나", "다", "라"], 2))
            game.save_state()

            reloaded = QuizGame(state_file)
            self.assertEqual(reloaded.best_score, 4)
            self.assertEqual(reloaded.games_played, 3)
            self.assertEqual(reloaded.last_score, 2)
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

    def test_corrupt_state_is_preserved_for_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            original = "{broken state"
            state_file.write_text(original, encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                game = QuizGame(state_file)
            backup_file = state_file.with_name("state.json.corrupt")
            self.assertEqual(backup_file.read_text(encoding="utf-8"), original)
            self.assertEqual(len(game.quizzes), 5)
            self.assertIn("손상된 파일을 보존했습니다", output.getvalue())

    def test_wrong_answer_is_shown_in_review(self):
        with tempfile.TemporaryDirectory() as directory:
            game = QuizGame(Path(directory) / "state.json")
            game.quizzes = default_quizzes()[:1]
            output = io.StringIO()
            with patch("builtins.input", return_value="4"), redirect_stdout(output):
                game.play()
            self.assertIn("복습할 문제", output.getvalue())
            self.assertEqual(game.games_played, 1)

    def test_quiz_can_be_deleted_after_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            game = QuizGame(state_file)
            game.best_score = 5
            game.save_state()
            with patch("builtins.input", side_effect=["2", "y"]):
                game.delete_quiz()
            self.assertEqual(len(game.quizzes), 4)
            reloaded = QuizGame(state_file)
            self.assertEqual(len(reloaded.quizzes), 4)
            self.assertEqual(reloaded.best_score, 5)

    def test_hint_and_correct_answer_update_persistent_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            game = QuizGame(state_file)
            game.quizzes = default_quizzes()[:1]
            output = io.StringIO()
            with patch("random.shuffle", side_effect=lambda questions: None):
                with patch("builtins.input", side_effect=["h", "1"]), redirect_stdout(output):
                    game.play()
            self.assertIn("힌트:", output.getvalue())
            self.assertIn("정답입니다!", output.getvalue())
            reloaded = QuizGame(state_file)
            self.assertEqual(reloaded.best_score, 1)
            self.assertEqual(reloaded.last_score, 1)
            self.assertEqual(reloaded.games_played, 1)


if __name__ == "__main__":
    unittest.main()
