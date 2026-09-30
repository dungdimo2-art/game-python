# main.py
# GAME V1 - "NE VAT CAN" (Endless Score)
# Python + Kivy | Offline | Touch friendly | 1 file
#
# Chay tren PC:
#   pip install kivy
#   python main.py
#
# Dong goi Android:
#   Dung Buildozer tren Linux/WSL (xem huong dan sau code).
#
# Dieu khien:
#   - PC: A/D hoac mui ten trai/phai
#   - Dien thoai: cham ben trai/phai man hinh de di chuyen
#   - Cham giua man hinh khi Game Over de choi lai

import random
import math
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout


# -----------------------------
# Cấu hình
# -----------------------------
WIDTH = 720
HEIGHT = 1280
SAVE_FILE = Path.home() / ".nevatcan_highscore.txt"

try:
    Window.size = (420, 760)
except Exception:
    pass

Window.clearcolor = (0.04, 0.05, 0.09, 1)


def load_high_score():
    try:
        return int(SAVE_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return 0


def save_high_score(score):
    try:
        SAVE_FILE.write_text(str(int(score)), encoding="utf-8")
    except Exception:
        pass


# -----------------------------
# Đối tượng game
# -----------------------------
class Player:
    def __init__(self):
        self.w = dp(58)
        self.h = dp(58)
        self.x = 0
        self.y = 0
        self.speed = dp(430)
        self.target_x = None

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def set_center(self, x):
        self.target_x = x

    def update(self, dt, left, right, game_width):
        if self.target_x is not None:
            dx = self.target_x - self.cx
            max_move = self.speed * dt
            if abs(dx) <= max_move:
                self.x += dx
                self.target_x = None
            else:
                self.x += max_move if dx > 0 else -max_move

        if left:
            self.x -= self.speed * dt
        if right:
            self.x += self.speed * dt

        self.x = max(0, min(game_width - self.w, self.x))


class Obstacle:
    def __init__(self, x, y, size, speed, kind):
        self.x = x
        self.y = y
        self.w = size
        self.h = size
        self.speed = speed
        self.kind = kind
        self.spin = random.uniform(0, 360)
        self.spin_speed = random.choice([-1, 1]) * random.uniform(90, 220)

    def update(self, dt):
        self.y -= self.speed * dt
        self.spin += self.spin_speed * dt

    def offscreen(self):
        return self.y + self.h < -dp(20)


class Coin:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.w = size
        self.h = size
        self.speed = speed
        self.phase = random.random() * math.pi * 2

    def update(self, dt):
        self.y -= self.speed * dt
        self.phase += dt * 5

    def offscreen(self):
        return self.y + self.h < -dp(20)


# -----------------------------
# Game canvas
# -----------------------------
class GameBoard(Widget):
    score = NumericProperty(0)
    high_score = NumericProperty(0)
    level = NumericProperty(1)
    status = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.running = False
        self.game_over = False
        self.left = False
        self.right = False
        self.spawn_timer = 0
        self.coin_timer = 0
        self.elapsed = 0
        self.shake = 0
        self.high_score = load_high_score()

        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_interval(self.update, 1 / 60)
        Clock.schedule_once(self.start_game, 0.2)

    # ---------- Game state ----------
    def start_game(self, *args):
        self.score = 0
        self.level = 1
        self.elapsed = 0
        self.spawn_timer = 0
        self.coin_timer = 0
        self.obstacles.clear()
        self.coins.clear()
        self.game_over = False
        self.running = True
        self.status = ""
        self.player.x = self.width / 2 - self.player.w / 2
        self.player.y = max(dp(75), self.height * 0.12)
        self.player.target_x = None
        self.redraw()

    def end_game(self):
        self.running = False
        self.game_over = True
        self.shake = 0.15
        if self.score > self.high_score:
            self.high_score = int(self.score)
            save_high_score(self.high_score)
        self.status = "GAME OVER"
        self.redraw()

    def add_score(self, amount):
        self.score = int(self.score + amount)
        if self.score > self.high_score:
            self.high_score = int(self.score)

    # ---------- Difficulty ----------
    def difficulty(self):
        # Tang dan theo thoi gian, nhung khong co diem dung.
        return min(10.0, 1.0 + self.elapsed / 18.0)

    def spawn_obstacle(self):
        d = self.difficulty()
        size = random.uniform(dp(34), dp(62))
        margin = dp(8)
        x = random.uniform(margin, max(margin, self.width - size - margin))
        speed = dp(random.uniform(230, 330)) * (0.72 + d * 0.12)
        kind = random.randrange(4)
        self.obstacles.append(Obstacle(x, self.height + size, size, speed, kind))

    def spawn_coin(self):
        size = dp(30)
        x = random.uniform(dp(10), max(dp(10), self.width - size - dp(10)))
        speed = dp(random.uniform(170, 240)) * (0.85 + self.difficulty() * 0.05)
        self.coins.append(Coin(x, self.height + size, size, speed))

    # ---------- Collision ----------
    @staticmethod
    def hit(a, b, padding=0):
        return (
            a.x + padding < b.x + b.w
            and a.x + a.w - padding > b.x
            and a.y + padding < b.y + b.h
            and a.y + a.h - padding > b.y
        )

    def update(self, dt):
        if not self.running:
            self.redraw()
            return

        self.elapsed += dt
        self.level = max(1, int(self.elapsed / 12) + 1)

        # Di chuyen
        self.player.update(dt, self.left, self.right, self.width)

        # Spawn vat can
        self.spawn_timer -= dt
        interval = max(0.24, 0.78 - self.difficulty() * 0.045)
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = interval

            # Thỉnh thoảng tạo thêm vật cản khi game nhanh
            if self.difficulty() > 5 and random.random() < 0.18:
                self.spawn_obstacle()

        # Spawn coin
        self.coin_timer -= dt
        if self.coin_timer <= 0:
            self.spawn_coin()
            self.coin_timer = random.uniform(1.0, 1.8)

        # Update vat can
        for obj in self.obstacles[:]:
            obj.update(dt)
            if obj.offscreen():
                self.obstacles.remove(obj)
                self.add_score(2)
                continue

            if self.hit(self.player, obj, dp(7)):
                self.end_game()
                return

        # Update coin
        for coin in self.coins[:]:
            coin.update(dt)
            if coin.offscreen():
                self.coins.remove(coin)
                continue

            if self.hit(self.player, coin, dp(8)):
                self.coins.remove(coin)
                self.add_score(15)
                self.shake = 0.06

        # Điểm sống sót
        self.add_score(dt * (4 + self.difficulty() * 0.9))

        if self.shake > 0:
            self.shake -= dt

        self.redraw()

    # ---------- Input ----------
    def on_touch_down(self, touch):
        if self.game_over:
            self.start_game()
            return True

        if touch.x < self.width * 0.42:
            self.left = True
            self.right = False
        elif touch.x > self.width * 0.58:
            self.right = True
            self.left = False
        else:
            self.player.set_center(touch.x)

        return True

    def on_touch_move(self, touch):
        if not self.game_over:
            self.player.set_center(touch.x)
        return True

    def on_touch_up(self, touch):
        self.left = False
        self.right = False
        return True

    def key_down(self, key):
        if key in (276, ord("a"), ord("A")):
            self.left = True
        elif key in (275, ord("d"), ord("D")):
            self.right = True
        elif key in (32, 13) and self.game_over:
            self.start_game()

    def key_up(self, key):
        if key in (276, ord("a"), ord("A")):
            self.left = False
        elif key in (275, ord("d"), ord("D")):
            self.right = False

    # ---------- Drawing ----------
    def redraw(self, *args):
        self.canvas.clear()

        # Nền
        with self.canvas:
            Color(0.035, 0.045, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Nền sọc
            for i in range(12):
                yy = self.y + i * self.height / 12
                Color(0.05, 0.06 + i * 0.001, 0.11, 1)
                Rectangle(pos=(self.x, yy), size=(self.width, 1))

            # Sao nền
            random.seed(77)
            for i in range(36):
                sx = self.x + random.random() * self.width
                sy = self.y + random.random() * self.height
                r = random.choice([1, 1, 1, 2])
                Color(0.35, 0.4, 0.55, 0.5)
                Ellipse(pos=(sx, sy), size=(r, r))
            random.seed()

            # Khu vực chơi
            Color(0.07, 0.09, 0.16, 1)
            Rectangle(pos=(self.x + dp(5), self.y + dp(5)),
                      size=(self.width - dp(10), self.height - dp(10)))

            # Lưới nhẹ
            Color(0.12, 0.14, 0.22, 0.55)
            for i in range(1, 8):
                x = self.x + self.width * i / 8
                Line(points=[x, self.y, x, self.top], width=0.5)
            for i in range(1, 14):
                y = self.y + self.height * i / 14
                Line(points=[self.x, y, self.right, y], width=0.5)

            # Coin
            for coin in self.coins:
                pulse = 1 + math.sin(coin.phase) * 0.08
                size = coin.w * pulse
                cx = coin.x + coin.w / 2
                cy = coin.y + coin.h / 2
                Color(1.0, 0.76, 0.08, 1)
                Ellipse(pos=(cx - size / 2, cy - size / 2), size=(size, size))
                Color(1.0, 0.93, 0.35, 1)
                Ellipse(pos=(cx - size * 0.28, cy - size * 0.28),
                        size=(size * 0.56, size * 0.56))
                Color(0.55, 0.35, 0.02, 1)
                Line(circle=(cx, cy, size * 0.30), width=1.2)

            # Vat can
            for obj in self.obstacles:
                cx = obj.x + obj.w / 2
                cy = obj.y + obj.h / 2
                if obj.kind == 0:
                    Color(0.95, 0.18, 0.25, 1)
                    Ellipse(pos=(obj.x, obj.y), size=(obj.w, obj.h))
                    Color(1, 0.45, 0.45, 0.8)
                    Ellipse(pos=(obj.x + obj.w * .25, obj.y + obj.h * .58),
                            size=(obj.w * .18, obj.h * .18))
                elif obj.kind == 1:
                    Color(0.55, 0.22, 0.95, 1)
                    Rectangle(pos=(obj.x, obj.y), size=(obj.w, obj.h))
                    Color(0.8, 0.62, 1, 0.8)
                    Line(rectangle=(obj.x, obj.y, obj.w, obj.h), width=2)
                elif obj.kind == 2:
                    Color(0.95, 0.38, 0.08, 1)
                    Ellipse(pos=(obj.x, obj.y), size=(obj.w, obj.h))
                    Color(1, 0.76, 0.25, 1)
                    Line(circle=(cx, cy, obj.w * .28), width=2)
                else:
                    Color(0.1, 0.75, 0.9, 1)
                    Rectangle(pos=(obj.x, obj.y), size=(obj.w, obj.h))
                    Color(0.65, 0.95, 1, 1)
                    Line(points=[
                        obj.x + obj.w*.2, obj.y + obj.h*.2,
                        obj.x + obj.w*.8, obj.y + obj.h*.8
                    ], width=2)
                    Line(points=[
                        obj.x + obj.w*.8, obj.y + obj.h*.2,
                        obj.x + obj.w*.2, obj.y + obj.h*.8
                    ], width=2)

            # Player
            px = self.player.x
            py = self.player.y
            if self.shake > 0:
                px += random.uniform(-dp(3), dp(3))
                py += random.uniform(-dp(3), dp(3))

            # Shadow
            Color(0, 0, 0, 0.45)
            Ellipse(pos=(px + dp(4), py - dp(5)),
                    size=(self.player.w - dp(8), dp(16)))

            # Robot/player
            Color(0.18, 0.78, 1.0, 1)
            RoundedRectangle(pos=(px, py), size=(self.player.w, self.player.h),
                             radius=[dp(12)])
            Color(0.55, 0.94, 1, 1)
            RoundedRectangle(pos=(px + dp(7), py + dp(20)),
                             size=(self.player.w - dp(14), dp(28)),
                             radius=[dp(8)])
            Color(0.03, 0.08, 0.14, 1)
            Ellipse(pos=(px + dp(16), py + dp(30)), size=(dp(9), dp(9)))
            Ellipse(pos=(px + dp(33), py + dp(30)), size=(dp(9), dp(9)))

            # Mui ten huong dan
            if self.running and self.elapsed < 4:
                Color(1, 1, 1, 0.10)
                Rectangle(pos=(self.x, self.y), size=(self.width, dp(70)))


# -----------------------------
# UI
# -----------------------------
class ScoreLabel(Label):
    pass


class MainLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.board = GameBoard()
        self.add_widget(self.board)

        self.score_label = Label(
            text="ĐIỂM: 0",
            font_size=dp(22),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(dp(180), dp(50)),
            pos_hint={"x": 0.03, "top": 0.985},
            halign="left",
            valign="middle",
        )
        self.add_widget(self.score_label)

        self.high_label = Label(
            text="KỶ LỤC: 0",
            font_size=dp(16),
            color=(0.72, 0.82, 1, 1),
            size_hint=(None, None),
            size=(dp(170), dp(40)),
            pos_hint={"right": 0.98, "top": 0.985},
            halign="right",
            valign="middle",
        )
        self.add_widget(self.high_label)

        self.level_label = Label(
            text="CẤP 1",
            font_size=dp(15),
            color=(1, 0.78, 0.25, 1),
            size_hint=(None, None),
            size=(dp(120), dp(38)),
            pos_hint={"center_x": 0.5, "top": 0.985},
            halign="center",
            valign="middle",
        )
        self.add_widget(self.level_label)

        self.game_over_label = Label(
            text="",
            font_size=dp(34),
            bold=True,
            color=(1, 0.35, 0.4, 1),
            size_hint=(0.9, 0.22),
            pos_hint={"center_x": 0.5, "center_y": 0.56},
            halign="center",
            valign="middle",
        )
        self.add_widget(self.game_over_label)

        self.help_label = Label(
            text="CHẠM TRÁI / PHẢI • KÉO ĐỂ DI CHUYỂN",
            font_size=dp(12),
            color=(0.65, 0.7, 0.82, 0.85),
            size_hint=(0.9, None),
            height=dp(32),
            pos_hint={"center_x": 0.5, "y": 0.01},
            halign="center",
        )
        self.add_widget(self.help_label)

        Clock.schedule_interval(self.refresh_ui, 1 / 20)

    def refresh_ui(self, dt):
        score = int(self.board.score)
        high = int(max(self.board.high_score, score))
        self.score_label.text = f"ĐIỂM: {score}"
        self.high_label.text = f"KỶ LỤC: {high}"
        self.level_label.text = f"CẤP {int(self.board.level)}"

        if self.board.game_over:
            self.game_over_label.text = (
                f"GAME OVER\n\n"
                f"Điểm: {score}\n"
                f"Kỷ lục: {high}\n\n"
                f"CHẠM MÀN HÌNH ĐỂ CHƠI LẠI"
            )
            self.help_label.text = "CHẠM BẤT KỲ ĐÂU ĐỂ CHƠI LẠI"
        else:
            self.game_over_label.text = ""
            if self.board.elapsed < 4:
                self.help_label.text = "CHẠM TRÁI / PHẢI • KÉO ĐỂ DI CHUYỂN"
            else:
                self.help_label.text = "A/D hoặc ←/→ trên máy tính"

    def keyboard(self, window, key, scancode, codepoint, modifiers):
        self.board.key_down(key)

    def keyboard_up(self, window, key, scancode):
        self.board.key_up(key)


class EndlessGameApp(App):
    title = "Ne Vat Can - Endless Score"

    def build(self):
        layout = MainLayout()
        Window.bind(on_key_down=layout.keyboard)
        Window.bind(on_key_up=layout.keyboard_up)
        return layout


if __name__ == "__main__":
    EndlessGameApp().run()
