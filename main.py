"""찰리와 초콜릿 공장 이야기 퀴즈 게임."""

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "state.json"


def default_quizzes():
    """Return the original questions that ship with the game."""
    return [
        Quiz(
            "찰리가 찾은 마지막 황금 티켓은 무엇을 위한 초대장이었나요?",
            ["초콜릿 공장 견학", "새 학교 입학", "사탕 가게 개업식", "배 여행"],
            1,
            "초대장을 받은 아이들은 신비한 공장 안으로 들어갑니다.",
        ),
        Quiz(
            "찰리와 함께 공장을 둘러본 가족은 누구인가요?",
            ["엄마", "조지 할아버지", "조 할아버지", "아버지"],
            3,
            "그는 침대에서 일어나 찰리와 함께 모험을 떠납니다.",
        ),
        Quiz(
            "바이올렛 뷰리가드가 실험용 껌을 씹은 뒤 어떤 모습으로 변했나요?",
            ["풍선처럼 부풀었다", "블루베리처럼 변했다", "투명해졌다", "목소리가 사라졌다"],
            2,
            "그 껌에는 아직 시험 중인 식사 메뉴가 들어 있었습니다.",
        ),
        Quiz(
            "버루카 솔트가 다람쥐들에게 다가간 뒤 벌어진 일은 무엇인가요?",
            ["다람쥐들이 춤을 췄다", "버루카가 견과류 판정을 받았다", "다람쥐들이 공장을 떠났다", "찰리가 티켓을 잃었다"],
            2,
            "다람쥐들은 견과류를 검사하는 일을 하고 있었습니다.",
        ),
        Quiz(
            "마이크 티비가 공장에서 작아진 계기는 무엇인가요?",
            ["텔레비전 전송 장치를 이용했다", "초콜릿 강에 빠졌다", "껌을 씹었다", "유리 엘리베이터를 탔다"],
            1,
            "그는 화면 속으로 물건을 보내는 기술을 직접 시험했습니다.",
        ),
    ]


class Quiz:
    """A four-choice question and its hint."""

    def __init__(self, question, choices, answer, hint=""):
        self.question = str(question).strip()
        self.choices = [str(choice).strip() for choice in choices]
        self.answer = int(answer)
        self.hint = str(hint).strip()
        if not self.question:
            raise ValueError("질문은 비워 둘 수 없습니다.")
        if len(self.choices) != 4 or any(not choice for choice in self.choices):
            raise ValueError("선택지는 빈칸 없이 4개여야 합니다.")
        if self.answer not in range(1, 5):
            raise ValueError("정답 번호는 1부터 4까지여야 합니다.")

    def to_dict(self):
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["question"], data["choices"], data["answer"], data.get("hint", ""))


class QuizGame:
    """Own the menu, questions, score, and JSON persistence."""

    def __init__(self, state_file=STATE_FILE):
        self.state_file = Path(state_file)
        self.quizzes = default_quizzes()
        self.best_score = 0
        self.load_state()

    def load_state(self):
        if not self.state_file.exists():
            return
        try:
            with self.state_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
            saved = [Quiz.from_dict(item) for item in data.get("quizzes", [])]
            score = int(data.get("best_score", 0))
            if score < 0:
                raise ValueError("최고 점수 값이 올바르지 않습니다.")
            if saved:
                self.quizzes = saved
            self.best_score = score
            print("저장된 퀴즈와 최고 점수를 불러왔습니다.")
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print("저장 파일을 읽을 수 없어 기본 데이터로 시작합니다:", error)

    def save_state(self):
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
        }
        try:
            with self.state_file.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.write("\n")
        except OSError as error:
            print("저장 중 오류가 발생했습니다:", error)

    @staticmethod
    def read_nonempty(prompt):
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("빈칸은 사용할 수 없습니다. 다시 입력해 주세요.")

    @staticmethod
    def read_number(prompt, minimum, maximum):
        while True:
            value = input(prompt).strip()
            if not value:
                print("숫자를 입력해 주세요.")
                continue
            try:
                number = int(value)
            except ValueError:
                print("숫자로 입력해 주세요.")
                continue
            if number < minimum or number > maximum:
                print(f"{minimum}부터 {maximum} 사이의 숫자를 입력해 주세요.")
                continue
            return number

    def play(self):
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return
        score = 0
        questions = list(self.quizzes)
        random.shuffle(questions)  # 보너스: 실행할 때마다 문제 순서를 섞습니다.
        print(f"\n퀴즈를 시작합니다! 총 {len(questions)}문제입니다.")
        for index, quiz in enumerate(questions, start=1):
            print(f"\n[문제 {index}] {quiz.question}")
            for number, choice in enumerate(quiz.choices, start=1):
                print(f"{number}. {choice}")
            while True:
                answer = input("정답 번호 (1-4, 힌트는 h): ").strip().lower()
                if answer == "h":
                    print("힌트:", quiz.hint or "이 문제에는 힌트가 없습니다.")
                    continue
                if answer not in {"1", "2", "3", "4"}:
                    print("1부터 4까지의 번호 또는 h를 입력해 주세요.")
                    continue
                if int(answer) == quiz.answer:
                    print("정답입니다!")
                    score += 1
                else:
                    print(f"아쉽지만 오답입니다. 정답은 {quiz.answer}번입니다.")
                break
        percent = round(score / len(questions) * 100)
        print(f"\n결과: {len(questions)}문제 중 {score}문제 정답 ({percent}점)")
        if score > self.best_score:
            self.best_score = score
            print("새로운 최고 점수입니다!")
        self.save_state()

    def add_quiz(self):
        print("\n새 퀴즈를 등록합니다.")
        question = self.read_nonempty("문제: ")
        choices = [self.read_nonempty(f"선택지 {number}: ") for number in range(1, 5)]
        answer = self.read_number("정답 번호 (1-4): ", 1, 4)
        hint = input("힌트 (없으면 Enter): ").strip()
        self.quizzes.append(Quiz(question, choices, answer, hint))
        self.save_state()
        print("퀴즈를 저장했습니다.")

    def show_quizzes(self):
        print(f"\n등록된 퀴즈: {len(self.quizzes)}개")
        for index, quiz in enumerate(self.quizzes, start=1):
            print(f"{index}. {quiz.question}")

    def show_score(self):
        if self.best_score == 0:
            print("아직 기록된 점수가 없습니다. 퀴즈에 도전해 보세요!")
        else:
            print(f"최고 점수: {self.best_score}문제 정답")

    def run(self):
        print("찰리와 초콜릿 공장 이야기 퀴즈")
        while True:
            print("\n1. 퀴즈 풀기  2. 퀴즈 추가  3. 퀴즈 목록  4. 최고 점수  5. 종료")
            choice = self.read_number("메뉴 선택 (1-5): ", 1, 5)
            if choice == 1:
                self.play()
            elif choice == 2:
                self.add_quiz()
            elif choice == 3:
                self.show_quizzes()
            elif choice == 4:
                self.show_score()
            else:
                self.save_state()
                print("게임을 종료합니다. 다음에 또 만나요!")
                return


def main():
    game = QuizGame()
    try:
        game.run()
    except (KeyboardInterrupt, EOFError):
        print("\n입력이 종료되어 저장하고 안전하게 마칩니다.")
        game.save_state()


if __name__ == "__main__":
    main()
