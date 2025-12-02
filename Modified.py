import tkinter as tk
from PIL import Image, ImageTk
import random
import os

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
        self.speed = 3.0
        
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill="#FF0000", outline='black', width=2)
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
        self.width = 120 
        self.height = 12
        self.ball = None
        
        self.velocity = 0.0      
        self.acceleration = 1.5  
        self.friction = 0.85     
        self.max_speed = 12.0    
        
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#2C3E50', outline='#00FFFF', width=3)
        
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def update_physics(self, left_pressed, right_pressed):
        if left_pressed:
            self.velocity -= self.acceleration
        if right_pressed:
            self.velocity += self.acceleration

        self.velocity *= self.friction

        if self.velocity > self.max_speed:
            self.velocity = self.max_speed
        elif self.velocity < -self.max_speed:
            self.velocity = -self.max_speed

        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        x_left = coords[0]
        x_right = coords[2]

        if x_left + self.velocity < 0:
            self.velocity = 0
            self.move(-x_left, 0) 
            return

        if x_right + self.velocity > width:
            self.velocity = 0
            self.move(width - x_right, 0)
            return

        if abs(self.velocity) < 0.1:
            self.velocity = 0
        else:
            self.move(self.velocity, 0)
            if self.ball is not None:
                self.ball.move(self.velocity, 0)


class Brick(GameObject):
    COLORS = {1: '#00D2FF', 2: '#FF00FF', 3: '#9D00FF'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick',
                                       outline='white', width=2)
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

        # Tambahkan background image (Logika tetap sama seperti request)
        self.background_image = None
        self.background_photo = None
        self.load_background()

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
        
        self.canvas.bind('<KeyPress>', self.on_key_press)
        self.canvas.bind('<KeyRelease>', self.on_key_release)

    # --- BAGIAN INI TIDAK DIUBAH SAMA SEKALI (CUSTOM BG LOGIC) ---
    def load_background(self):
        try:
            # Coba cari file background (GIF)
            bg_path = None
            for ext in ['bbbackground.gif']:
                if os.path.exists(ext):
                    bg_path = ext
                    break
            
            if bg_path:
                # Buka gambar
                self.bg_image = Image.open(bg_path)
                
                # Cek apakah GIF animasi
                self.is_animated_gif = False
                self.gif_frames = []
                self.gif_frame_index = 0
                self.gif_frame_delay = 100  # default delay
                
                try:
                    # Coba ekstrak semua frame dari GIF
                    frame_count = 0
                    while True:
                        frame = self.bg_image.copy()
                        frame = frame.resize((self.width, self.height), Image.LANCZOS)
                        self.gif_frames.append(ImageTk.PhotoImage(frame))
                        frame_count += 1
                        self.bg_image.seek(frame_count)
                    
                except EOFError:
                    # Sudah sampai akhir frame
                    if frame_count > 1:
                        self.is_animated_gif = True
                        # Ambil duration dari GIF
                        try:
                            self.gif_frame_delay = self.bg_image.info.get('duration', 100)
                        except:
                            self.gif_frame_delay = 100
                        print(f"GIF animasi berhasil dimuat! Total frame: {frame_count}")
                    else:
                        # Hanya 1 frame, treat sebagai gambar biasa
                        self.background_photo = self.gif_frames[0]
                        print("Background image berhasil dimuat!")
                
                # Buat image object di canvas
                self.background_image = self.canvas.create_image(
                    0, 0, 
                    image=self.gif_frames[0] if self.gif_frames else self.background_photo, 
                    anchor='nw',
                    tags='background'
                )
                # Pastikan background ada di layer paling bawah
                self.canvas.tag_lower('background')
                
                # Mulai animasi jika GIF
                if self.is_animated_gif:
                    self.animate_background()
                    
            else:
                print("File bbbackground.gif tidak ditemukan.")
                print("Menggunakan warna default.")
        except Exception as e:
            print(f"Error loading background image: {e}")
            print("Menggunakan warna background default.")
    
    def animate_background(self):
        """Animasi frame GIF background"""
        if self.is_animated_gif and len(self.gif_frames) > 0:
            # Update ke frame berikutnya
            self.gif_frame_index = (self.gif_frame_index + 1) % len(self.gif_frames)
            self.canvas.itemconfig(self.background_image, 
                                  image=self.gif_frames[self.gif_frame_index])
            # Schedule frame berikutnya
            self.after(self.gif_frame_delay, self.animate_background)
    # -------------------------------------------------------------

    def on_key_press(self, event):
        self.pressed_keys.add(event.keysym)

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
           self.canvas.bind('<space>', lambda _: self.start_game())

    def add_initial_ball(self):
        paddle_coords = self.paddle.get_position()
        x_center = (paddle_coords[0] + paddle_coords[2]) * 0.5
        ball = Ball(self.canvas, x_center, 310) 
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
        # MENGUBAH FONT DI SINI
        font = ('Courier New', size, 'bold')
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = ' Health: %s' % self.lives
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
        left_is_pressed = 'Left' in self.pressed_keys
        right_is_pressed = 'Right' in self.pressed_keys
        
        self.paddle.update_physics(left_is_pressed, right_is_pressed)

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
            self.after(16, self.game_loop) 

    def check_collisions(self, ball_to_check):
        ball_coords = ball_to_check.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        return ball_to_check.collide(objects)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Bola-Bola')
    game = Game(root)
    game.mainloop()