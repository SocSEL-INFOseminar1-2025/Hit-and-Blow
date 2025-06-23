import random
import time
from enum import Enum, auto
from itertools import permutations

from js import alert, document, prompt
from pyodide.ffi import create_proxy


class HitAndBlowGame:
    class HitBlowResult(Enum):
        HIT = auto()  # 数字と場所が一致
        BLOW = auto()  # 数字のみが一致
        NONE = auto()

    def __init__(self):
        """初期化処理"""

        # 変数の宣言
        self.turn = 1
        self.cpu_num = ""
        self.player_num = ""
        self.is_game_continue = True

        # --- CPU思考ロジック用の変数を追加 ---
        self.cpu_possible_answers = []
        self.cpu_initial_guesses = ["012", "345", "678"]
        self.cpu_guess_index = 0

        # HTMLの要素を取得
        self.player_table = document.getElementById("player-table")
        self.a = document.getElementById("cpu-table")  # 元のコードの 'a' を維持
        self.input_form = document.getElementById("inputForm")
        self.result = document.getElementById("result")
        self.new_game_button = document.getElementById("newGameBtn")
        self.shuffle_button = document.getElementById("shuffleBtn")
        self.shot_button = document.getElementById("shotBtn")
        self.highLow_button = document.getElementById("highLowBtn")

        # HTMLの要素にイベントを追加
        self.input_form.addEventListener("submit", create_proxy(self.input_method))
        self.new_game_button.addEventListener("click", create_proxy(self.game_start))
        self.shuffle_button.addEventListener("click", create_proxy(self.shuffle))
        self.shot_button.addEventListener("click", create_proxy(self.shot))
        self.highLow_button.addEventListener("click", create_proxy(self.highLow))

    def game_start(self, event=None):
        """ゲームをスタート時に呼び出し"""
        if event:
            event.preventDefault()
        self.clear_table()
        self.enable_input_form()
        self.clear_input_form()
        self.set_player_num()
        self.result.innerText = ""
        self.turn = 1
        self.is_game_continue = True

        # --- CPUロジックの初期化処理を追加 ---
        # 重複のない3桁の数字の組み合わせをすべて生成
        all_digits = list("0123456789")
        self.cpu_possible_answers = ["".join(p) for p in permutations(all_digits, 3)]
        self.cpu_guess_index = 0

        # CPUの答え（重複なし）を生成
        self.cpu_num = self._generate_unique_3_digits()

        print(f"自分の数字: {self.player_num}")
        print(f"cpuの数字: {self.cpu_num}")

    def _generate_unique_3_digits(self):
        """重複のないランダムな3桁の数字（文字列）を生成するヘルパー関数"""
        numbers = list("0123456789")
        random.shuffle(numbers)
        return "".join(numbers[:3])

    def input_method(self, event):
        """フォームを入力するたびに走る関数"""
        event.preventDefault()
        # 入力を受け取る (3桁の文字列として結合)
        first_digit = document.getElementById("first-digit").value
        second_digit = document.getElementById("second-digit").value
        third_digit = document.getElementById("third-digit").value
        player_input = f"{first_digit}{second_digit}{third_digit}"

        # --- 入力バリデーションを追加 ---
        if not (
            len(player_input) == 3
            and player_input.isdigit()
            and len(set(player_input)) == 3
        ):
            alert("無効な入力です。重複のない3桁の数字を入力してください。")
            return

        self.clear_input_form()

        # プレイヤーが入力した数字のHit数とBLow数を判定
        p_hit, p_blow = self.HB_judge(player_input, self.cpu_num)

        # プレイヤーの入力とHit数とBLow数をテーブルに追加
        new_row = self.player_table.insertRow(-1)
        new_row.insertCell(0).textContent = player_input
        new_row.insertCell(1).textContent = p_hit
        new_row.insertCell(2).textContent = p_blow

        # プレイヤーが勝利したかどうかを判定
        if self.game_judge(p_hit, is_player_turn=True):
            self.result.innerText = "You Win!"
            self.disable_input_form()
            # CPUのターンは行わない
            return

        # CPUが考えている感じにするため、少し待つ
        time.sleep(0.5)

        # CPUの入力を受け取る (新しいロジック)
        cpu_input = self.cpu_input()

        # cpuが入力した数字のHit数とBLow数を判定
        c_hit, c_blow = self.HB_judge(cpu_input, self.player_num)

        # --- CPUの候補を更新 ---
        self._update_cpu_candidates(cpu_input, c_hit, c_blow)

        # CPUの入力とHit数とBLow数をテーブルに追加
        new_row = self.a.insertRow(-1)
        new_row.insertCell(0).textContent = cpu_input
        new_row.insertCell(1).textContent = c_hit
        new_row.insertCell(2).textContent = c_blow

        # CPUが勝利したかどうかを判定
        if self.game_judge(c_hit, is_player_turn=False):
            # プレイヤーが先に勝利していなければCPUの勝ち
            if self.is_game_continue:
                self.result.innerText = "You Lose!"
            else:  # 同ターンで両者クリアならドロー
                self.result.innerText = "Draw!"
            self.disable_input_form()

    def cpu_input(self):
        """【刷新】攻略法に基づいて次の手を予測する"""
        # 最初の3手は数字を特定するために固定の値を試す
        if self.cpu_guess_index < len(self.cpu_initial_guesses):
            guess = self.cpu_initial_guesses[self.cpu_guess_index]
            self.cpu_guess_index += 1
            return guess

        # 4手目以降は、可能性のある答えの中から最適な手を選ぶ
        if not self.cpu_possible_answers:
            # 候補がない場合（ロジックの矛盾など）、フォールバック
            return self._generate_unique_3_digits()

        # 最も多くの候補をふるい落とせる手を選ぶ（ミニマックス法）
        # 簡単な実装として、候補の中からランダムに1つ選ぶ
        return random.choice(self.cpu_possible_answers)

    def _update_cpu_candidates(self, guess, hit, blow):
        """CPUのコール結果を元に、答えの候補を絞り込む"""
        remaining_answers = []
        for candidate in self.cpu_possible_answers:
            # 候補(candidate)が正解だったと仮定した場合のHit/Blow数を計算
            h, b = self._calculate_hb_for_logic(guess, candidate)
            # 実際のHit/Blow数と一致すれば、その候補はまだ可能性が残っている
            if h == hit and b == blow:
                remaining_answers.append(candidate)

        self.cpu_possible_answers = remaining_answers
        print(f"CPUの残りの候補数: {len(self.cpu_possible_answers)}")
        if len(self.cpu_possible_answers) <= 10:
            print(f"候補: {self.cpu_possible_answers}")

    def _calculate_hb_for_logic(self, guess_str, answer_str):
        """CPUの思考ロジック内で使用する汎用的なHit/Blow判定"""
        hit = 0
        blow = 0

        for i in range(3):
            # Hit: 場所と数字が一致
            if guess_str[i] == answer_str[i]:
                hit += 1
            # Blow: 数字は含まれているが場所が違う
            elif guess_str[i] in answer_str:
                blow += 1
        return hit, blow

    def HB_judge(self, input_num_str, correct_num_str):
        """
        入力した数字のHとBを返す
        【修正】元のコードのHit/Blowの解釈が逆だったため修正。
        """
        hit = 0
        blow = 0

        for i in range(3):
            # Hit: 場所と数字が一致
            if input_num_str[i] == correct_num_str[i]:
                hit += 1
            # Blow: 数字は含まれているが場所が違う
            elif input_num_str[i] in correct_num_str:
                blow += 1

        return hit, blow

    def game_judge(self, hit, is_player_turn):
        """ゲームが終了したかどうかの判定"""
        if hit == 3:
            if is_player_turn:
                self.is_game_continue = False  # プレイヤーがクリア
            return True  # 3ヒットで終了

        # ターンはプレイヤーとCPUのセットで1つ進むと解釈し、ここではインクリメントしない
        # self.turn += 1
        return False

    def hit(self, split_i_num, split_num, result):
        # このメソッドはHB_judgeのロジック変更に伴い不要になった
        pass

    def blow(self, split_i_num, split_num, result):
        # このメソッドはHB_judgeのロジック変更に伴い不要になった
        pass

    def clear_table(self):
        """テーブルをクリアする"""
        table_ids = ["player-table", "cpu-table"]
        for table_id in table_ids:
            table = document.getElementById(table_id)
            while table.rows.length > 1:
                table.deleteRow(-1)

    def clear_input_form(self):
        """フォームをクリアする"""
        document.getElementById("first-digit").value = ""
        document.getElementById("second-digit").value = ""
        document.getElementById("third-digit").value = ""
        document.getElementById("first-digit").focus()

    def disable_input_form(self):
        """フォームを無効にする"""
        for element in self.input_form.elements:
            element.disabled = True

    def enable_input_form(self):
        """フォームを有効にする"""
        for element in self.input_form.elements:
            element.disabled = False

    def set_player_num(self):
        """【修正】プレイヤーに重複のない3桁の数字を設定させる"""
        while True:
            player_input = prompt("重複しない3桁の数字を入力してください", "例: 123")
            if (
                player_input
                and len(player_input) == 3
                and player_input.isdigit()
                and len(set(player_input)) == 3
            ):
                self.player_num = player_input
                break
            else:
                alert(
                    "無効な入力です。重複しない3桁の数字（例: 123）を入力してください。"
                )

        your_num = document.getElementById("your-number")
        your_num.innerText = "Your Number : " + self.player_num

    def shuffle(self, event=None):
        """数字をシャッフルする"""
        num_list = list(str(self.player_num))
        random.shuffle(num_list)
        self.player_num = "".join(num_list)
        your_num = document.getElementById("your-number")
        your_num.innerText = "Your Number : " + str(self.player_num)

        # (略) 以下、CPUのターンに続く処理...
        # この機能は複雑化するため、主要ロジックの外として一旦実装を省略します
        alert("シャッフル機能は現在無効です。")

    def shot(self, event=None):
        """３桁のうちランダムで一つの数字がわかる"""
        alert("自分で実装してね")
        # (略)

    def highLow(self, event=None):
        """3桁の数字のうち、一番大きい数字と一番小さい数字を教える"""
        alert("自分で実装してね")
        # (略)
