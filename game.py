import tkinter as tk


class Game(tk.Frame):
    """This is the class that controls the game logic and manipulation
    and allocation of GameObjects.
    This is a subclass of tk.Frame and needs a root frame (the master)
    to be embedded into.
    To execute the Game, call the mainloop() function after initialization."""

    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 600
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#aaaaff',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(canvas=self.canvas, x=self.width / 2, y=326)
        self.items[self.paddle.item] = self.paddle
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.text = None
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.slide(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.slide(+10))

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, 'Press Space to start')
        self.canvas.bind('<space>',
                         lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_pos = self.paddle.get_position()
        x = (paddle_pos[0] + paddle_pos[2]) * 0.5
        self.ball = Ball(canvas=self.canvas, x=x, y=310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(canvas=self.canvas, x=x, y=y, hits=hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size=40):
        font = ('Helvetica', size)
        return self.canvas.create_text(x, y, text=text, font=font)

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
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.draw_text(300, 200, 'You win!')
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives <= 0:
                self.draw_text(300, 200, 'Game Over')
            else:
                self.after(1000, self.setup_game())
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_pos = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_pos)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


class GameObject(object):
    """Superclass for all the objects that will be rendered on the screen
    and need the ability to be moved, updated, etc.
    It needs the canvas on which the object must be rendered and the item
    (the reference returned by the canvas) to properly control it."""

    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        """Returns the position of the GameObject as per the internal Canvas."""
        return self.canvas.coords(self.item)

    def move(self, x, y):
        """Translates the position of this GameObject by the given translation
        amounts
        :param x: The translation to be done on the X axis. 
        :param y: The translation to be done on the Y axis."""
        self.canvas.move(self.item, x, y)

    def delete(self):
        """Removes itself from the Canvas and makes sure that it will not
        be rendered again."""
        self.canvas.delete(self.item)


class Ball(GameObject):
    """This is the ball that will be hit using the Paddle to try and
    break the Bricks."""

    def __init__(self, canvas, x, y):
        """
        The constructor for the Ball.
        :param canvas: The canvas necessary to render it on.
        :param x: The initial x coordinate of the Ball.
        :param y: The initial y coordinate of the Ball.
        """
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 10
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        position = self.get_position()
        width = self.canvas.winfo_width()
        if position[0] <= 0 or position[2] >= width:
            self.direction[0] *= -1
        if position[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        position = self.get_position()
        x = (position[0] + position[2]) * 0.5

        # Flip y direction when we hit a Brick
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            obj_pos = game_object.get_position()
            if x > obj_pos[2]:
                self.direction[0] = +1
            elif x < obj_pos[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        """
        The constructor for the Paddle.
        :param canvas: The canvas necessary to render it on.
        :param x: The initial x coordinate of the Paddle.
        :param y: The initial y coordinate of the Paddle.
        """
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill='blue')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def slide(self, offset):
        coordinates = self.get_position()
        width = self.canvas.winfo_width()
        if coordinates[0] + offset >= 0 and coordinates[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
        if self.ball is not None:
            self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#999999', 2: '#555555', 3: '#222222'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Hello, pong!')
    game = Game(root)
    game.mainloop()
