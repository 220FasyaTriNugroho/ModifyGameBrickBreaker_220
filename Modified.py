import tkinter as tk
import random

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        
        # membuat gameplay lebih "Smooth"
        self.speed = 3.0
        
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        hit_a_brick = False
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()
                hit_a_brick = True 

        return hit_a_brick


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        
        # --- FISIKA PADDLE (MOVE FADE) ---
        self.velocity = 0.0      # Kecepatan saat ini
        self.acceleration = 1.5  # Seberapa cepat paddle menambah speed
        self.friction = 0.85     # Gesekan (semakin kecil, semakin cepat berhenti / kurang licin)
        self.max_speed = 12.0    # Batas kecepatan maksimum paddle
        
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    # Method baru untuk update fisika paddle setiap frame
    def update_physics(self, left_pressed, right_pressed):
        # 1. Tambah kecepatan berdasarkan input (Akselerasi)
        if left_pressed:
            self.velocity -= self.acceleration
        if right_pressed:
            self.velocity += self.acceleration

        # 2. Terapkan Gesekan (Friction) agar paddle melambat jika tidak dipencet
        #    atau agar tidak terus bertambah cepat tanpa batas
        self.velocity *= self.friction

        # 3. Batasi Kecepatan Maksimum (Cap Speed)
        if self.velocity > self.max_speed:
            self.velocity = self.max_speed
        elif self.velocity < -self.max_speed:
            self.velocity = -self.max_speed

        # 4. Cek batas tembok sebelum bergerak (Wall Collision)
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Jika nabrak kiri dan mau ke kiri, stop
        if coords[0] + self.velocity < 0:
            self.velocity = 0
            # Paksa posisi ke pinggir pas
            self.move(-coords[0], 0) 
            return

        # Jika nabrak kanan dan mau ke kanan, stop
        if coords[2] + self.velocity > width:
            self.velocity = 0
            # Paksa posisi ke pinggir pas
            self.move(width - coords[2], 0)
            return

        # 5. Gerakkan Paddle (jika velocity sangat kecil, anggap 0)
        if abs(self.velocity) < 0.1:
            self.velocity = 0
        else:
            self.move(self.velocity, 0)
            if self.ball is not None:
                self.ball.move(self.velocity, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height,)
        self.canvas.pack()
        self.pack()

        # --- SISTEM INPUT BARU ---
        # Kita menggunakan set() untuk menyimpan tombol apa saja yang sedang ditekan
        self.pressed_keys = set()

        self.items = {}
        self.balls = [] 

        self.paddle = Paddle(self.canvas, self.width/2, 326)
        self.items[self.paddle.item] = self.paddle
        
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()
        
        # Binding event KeyPress dan KeyRelease
        self.canvas.bind('<KeyPress>', self.on_key_press)
        self.canvas.bind('<KeyRelease>', self.on_key_release)

    # Saat tombol ditekan, masukkan ke dalam set
    def on_key_press(self, event):
        self.pressed_keys.add(event.keysym)

    # Saat tombol dilepas, hapus dari set
    def on_key_release(self, event):
        if event.keysym in self.pressed_keys:
            self.pressed_keys.remove(event.keysym)

    def setup_game(self):
           for b in self.balls:
               b.delete()
           self.balls.clear()

           self.add_initial_ball()
           self.update_lives_text()
           self.text = self.draw_text(300, 200,
                                      'Press Space to start')
           # Space hanya sekali pakai, jadi bind biasa
           self.canvas.bind('<space>', lambda _: self.start_game())

    def add_initial_ball(self):
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(ball)
        self.balls.append(ball) 

    def spawn_extra_ball(self, source_ball_coords):
        x = (source_ball_coords[0] + source_ball_coords[2]) / 2
        y = (source_ball_coords[1] + source_ball_coords[3]) / 2
        new_ball = Ball(self.canvas, x, y)
        new_ball.direction[0] = random.choice([-1, 1])
        new_ball.direction[1] = 1 
        self.balls.append(new_ball) 

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None 
        self.game_loop()

    def game_loop(self):
        # --- UPDATE PADDLE DENGAN PHYSICS ---
        # Cek apakah tombol kiri atau kanan ada di dalam set pressed_keys
        left_is_pressed = 'Left' in self.pressed_keys
        right_is_pressed = 'Right' in self.pressed_keys
        
        # Panggil fungsi fisika paddle
        self.paddle.update_physics(left_is_pressed, right_is_pressed)

        # --- UPDATE BOLA ---
        bricks_hit_coords = [] 
        for ball in list(self.balls):
            ball.update()
            if self.check_collisions(ball):
                bricks_hit_coords.append(ball.get_position())

            if ball.get_position()[3] >= self.height:
                ball.delete()
                self.balls.remove(ball)

        for coords in bricks_hit_coords:
            if len(self.balls) < 15: 
                self.spawn_extra_ball(coords)

        # --- GAME LOGIC ---
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            for b in self.balls: b.speed = None
            self.draw_text(300, 200, 'You win! You the Breaker of Bricks.')
        elif len(self.balls) == 0:
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, 'You Lose! Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.after(16, self.game_loop) # Tetap 60 FPS

    def check_collisions(self, ball_to_check):
        ball_coords = ball_to_check.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        return ball_to_check.collide(objects)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Smooth Physics Breakout')
    game = Game(root)
    game.mainloop()