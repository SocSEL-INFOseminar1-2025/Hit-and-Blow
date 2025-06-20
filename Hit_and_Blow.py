import random
import time
from enum import Enum, auto

from js import alert, document, prompt
from pyodide.ffi import create_proxy


class HitAndBlowGame:
    class HitBlowResult(Enum):
        HIT = auto()
        BLOW = auto()
        NONE = auto()

    def __init__(self):
        """初期化処理"""

        # 変数の宣言
        self.turn = 1
        self.cpu_num = ""
        self.is_game_continue = True

        # HTMLの要素を取得
        self.player_table = document.getElementById("player-table")
        self.a = document.getElementById("cpu-table")
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
        self.cpu_num = self.cpu_input()
        self.is_game_continue = True
        print(f"自分の数字: {self.player_num}")
        print(f"cpuの数字: {self.cpu_num}")

    def input_method(self, event):
        """
        フォームを入力するたびに走る関数
        """
        event.preventDefault()
        # 入力を受け取る
        first_digit = int(document.getElementById("first-digit").value)
        second_digit = int(document.getElementById("second-digit").value)
        third_digit = int(document.getElementById("third-digit").value)
        player_input = first_digit * 100 + second_digit * 10 + third_digit

        self.clear_input_form()

        # プレイヤーが入力した数字のHit数とBLow数を判定
        p_hit, p_blow = self.HB_judge(player_input)

        # プレイヤーの入力とHit数とBLow数をテーブルに追加
        new_row = self.player_table.insertRow(-1)
        new_row.insertCell(0).textContent = player_input
        new_row.insertCell(1).textContent = p_hit
        new_row.insertCell(2).textContent = p_blow

        # プレイヤーが勝利したかどうかを判定
        self.game_judge(p_hit)
        if self.is_game_continue == False:
            self.result.innerText = "You Lose"
            self.disable_input_form()

        # CPUが考えている感じにするため、1秒待つ
        time.sleep(1)

        # CPUの入力を受け取る
        cpu_input = self.cpu_input()

        # cpuが入力した数字のHit数とBLow数を判定
        c_hit, c_blow = self.HB_judge(cpu_input)

        # CPUの入力とHit数とBLow数をテーブルに追加
        new_row = self.a.insertRow(-1)
        new_row.insertCell(0).textContent = cpu_input
        new_row.insertCell(1).textContent = c_hit
        new_row.insertCell(2).textContent = c_blow

        # CPUが勝利したかどうかを判定
        self.game_judge(c_hit)
        if self.is_game_continue == False:
            self.result = document.getElementById("result")
            if self.result.innerText != "You Win!":  # プレイヤーが3Hitしていたらドロー
                self.result.innerText = "Draw!"
            elif (
                self.result.innerText == ""
            ):  # プレイヤーが3Hitしていない場合、CPUの勝ち
                self.result.innerText = "You Lose!"
            self.disable_input_form()  # これ以上入力させないために、フォームを無効にする

    def cpu_input(self):
        """ランダムに3桁の数字を返す"""
        val = ""

        # 最初が0にならないようにする
        for _ in range(3):
            val += str(random.randint(0, 9))
        return val

    def HB_judge(self, input_num):
        """入力した数字のHとBを返す

        Args:
            input_num (num): 入力した数値
        """
        hit = 0
        blow = 0
        split_i_num = [int(num) for num in str(input_num)]
        result = [
            HitAndBlowGame.HitBlowResult.NONE,
            HitAndBlowGame.HitBlowResult.NONE,
            HitAndBlowGame.HitBlowResult.NONE,
        ]
        if self.turn % 2 == 0:
            split_p_num = [int(num) for num in str(self.player_num)]
            self.hit(split_i_num, split_p_num, result)
            self.blow(split_i_num, split_p_num, result)
        else:
            split_c_num = [int(num) for num in str(self.cpu_num)]
            self.hit(split_i_num, split_c_num, result)
            self.blow(split_i_num, split_c_num, result)

        for re in result:
            if re == HitAndBlowGame.HitBlowResult.HIT:
                blow += 1
            if re == HitAndBlowGame.HitBlowResult.BLOW:
                hit += 1

        return hit, blow

    def game_judge(self, hit):
        """ゲームが終了したかどうかの判定"""
        if hit == 3:
            self.is_game_continue = False
        self.turn += 1

    def hit(self, split_i_num, split_num, result):
        """ヒットしているかの判定

        Args:
            split_i_num (list): 入力した数字を1文字ごとにリストに格納したもの
            split_num (list): 正解を1文字ごとにリストに格納したもの
            result (list): 結果を格納するリスト
        """
        for i in range(3):
            if split_num[i] == split_i_num[i]:
                result[i] = HitAndBlowGame.HitBlowResult.HIT

    def blow(self, split_i_num, split_num, result):
        """ブローしているかの判定

        Args:
            split_i_num (list): 入力した数字を1文字ごとにリストに格納したもの
            split_num (list): 正解を1文字ごとにリストに格納したもの
            result (list): 結果を格納するリスト
        """
        used_indices = []
        for i in range(3):
            if result[i] == HitAndBlowGame.HitBlowResult.HIT:
                used_indices.append(i)
                continue
            for j in range(3):
                if j in used_indices:
                    continue
                if split_num[i] == split_i_num[j]:
                    result[i] = HitAndBlowGame.HitBlowResult.BLOW
                    used_indices.append(j)

    def clear_table(self):
        """テーブルをクリアする"""
        table = document.getElementById("player-table")
        row_count = table.rows.length
        while row_count > 1:
            table.deleteRow(-1)
            row_count -= 1
        table = document.getElementById("cpu-table")
        row_count = table.rows.length
        while row_count > 1:
            table.deleteRow(-1)
            row_count -= 1

    def clear_input_form(self):
        """フォームをクリアする"""
        document.getElementById("first-digit").value = ""
        document.getElementById("second-digit").value = ""
        document.getElementById("third-digit").value = ""

    def disable_input_form(self):
        """フォームを無効にする"""
        input_form = document.getElementById("inputForm")
        # Disable each input element in the form
        for element in input_form.elements:
            element.disabled = True

    def enable_input_form(self):
        """フォームを有効にする"""
        input_form = document.getElementById("inputForm")
        # Disable each input element in the form
        for element in input_form.elements:
            element.disabled = False

    def set_player_num(self):
        """プレイヤーの数字を設定する"""
        # 3桁の数字を入力するまでループ
        self.player_num = prompt("3桁の数字を入力してください")
        your_num = document.getElementById("your-number")
        your_num.innerText = "Your Number : " + self.player_num

    def shuffle(self, event=None):
        """数字をシャッフルする"""
        num_list = list(str(self.player_num))
        random.shuffle(num_list)
        self.player_num = int("".join(num_list))
        your_num = document.getElementById("your-number")
        your_num.innerText = "Your Number : " + str(self.player_num)

        self.turn += 1

        # プレイヤーの入力とHit数とBLow数をテーブルに追加
        new_row = self.player_table.insertRow(-1)
        new_row.insertCell(0).textContent = "shuffled"
        new_row.insertCell(1).textContent = ""
        new_row.insertCell(2).textContent = ""

        # CPUが考えている感じにするため、1秒待つ
        time.sleep(1)

        # CPUの入力を受け取る
        cpu_input = self.cpu_input()

        # cpuが入力した数字のHit数とBLow数を判定
        c_hit, c_blow = self.HB_judge(cpu_input)

        # CPUの入力とHit数とBLow数をテーブルに追加
        new_row = self.cpu_table.insertRow(-1)
        new_row.insertCell(0).textContent = cpu_input
        new_row.insertCell(1).textContent = c_hit
        new_row.insertCell(2).textContent = c_blow

        # CPUが勝利したかどうかを判定
        self.game_judge(c_hit)
        if self.is_game_continue == False:
            self.result = document.getElementById("result")
            if self.result.innerText != "You Win!":  # プレイヤーが3Hitしていたらドロー
                self.result.innerText = "Draw!"
            elif (
                self.result.innerText == ""
            ):  # プレイヤーが3Hitしていない場合、CPUの勝ち
                self.result.innerText = "You Lose!"
            self.disable_input_form()  # これ以上入力させないために、フォームを無効にする

    def shot(self, event=None):
        """３桁のうちランダムで一つの数字がわかる"""

        alert("自分で実装してね")

        self.turn += 1

        # プレイヤーの入力とHit数とBLow数をテーブルに追加
        new_row = self.player_table.insertRow(-1)
        new_row.insertCell(0).textContent = "shot"
        new_row.insertCell(1).textContent = ""
        new_row.insertCell(2).textContent = ""
        # CPUが考えている感じにするため、1秒待つ
        time.sleep(1)

        # CPUの入力を受け取る
        cpu_input = self.cpu_input()

        # cpuが入力した数字のHit数とBLow数を判定
        c_hit, c_blow = self.HB_judge(cpu_input)

        # CPUの入力とHit数とBLow数をテーブルに追加
        new_row = self.a.insertRow(-1)
        new_row.insertCell(0).textContent = cpu_input
        new_row.insertCell(1).textContent = c_hit
        new_row.insertCell(2).textContent = c_blow

        # CPUが勝利したかどうかを判定
        self.game_judge(c_hit)
        if self.is_game_continue == False:
            self.result = document.getElementById("result")
            if self.result.innerText != "You Win!":  # プレイヤーが3Hitしていたらドロー
                self.result.innerText = "Draw!"
            elif (
                self.result.innerText == ""
            ):  # プレイヤーが3Hitしていない場合、CPUの勝ち
                self.result.innerText = "You Lose!"
            self.disable_input_form()  # これ以上入力させないために、フォームを無効にする

    def highLow(self, event=None):
        """3桁の数字のうち、一番大きい数字と一番小さい数字を教える"""

        alert("自分で実装してね")

        # プレイヤーの入力とHit数とBLow数をテーブルに追加
        new_row = self.player_table.insertRow(-1)
        new_row.insertCell(0).textContent = "HighLow"
        new_row.insertCell(1).textContent = ""
        new_row.insertCell(2).textContent = ""

        self.turn += 1

        # CPUが考えている感じにするため、1秒待つ
        time.sleep(1)

        # CPUの入力を受け取る
        cpu_input = self.cpu_input()

        # cpuが入力した数字のHit数とBLow数を判定
        c_hit, c_blow = self.HB_judge(cpu_input)

        # CPUの入力とHit数とBLow数をテーブルに追加
        new_row = self.a.insertRow(-1)
        new_row.insertCell(0).textContent = cpu_input
        new_row.insertCell(1).textContent = c_hit
        new_row.insertCell(2).textContent = c_blow

        # CPUが勝利したかどうかを判定
        self.game_judge(c_hit)
        if self.is_game_continue == False:
            self.result = document.getElementById("result")
            if self.result.innerText != "You Win!":  # プレイヤーが3Hitしていたらドロー
                self.result.innerText = "Draw!"
            elif (
                self.result.innerText == ""
            ):  # プレイヤーが3Hitしていない場合、CPUの勝ち
                self.result.innerText = "You Lose!"
            self.disable_input_form()  # これ以上入力させないために、フォームを無効にする
