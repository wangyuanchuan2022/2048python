import json
import random
import sys
import time
import ctypes
import ctypes.wintypes
import os
import math

import pygame
import numpy as np
from grid import Grid
from ai2048 import find_best_move
import copy
import threading
from queue import Queue

from threading import Thread


NUM2COLOR = {
    0: (205, 193, 179),
    2: (238, 228, 218),
    4: (236, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (245, 124, 95),
    64: (246, 93, 59),
    128: (237, 206, 113),
    256: (233, 208, 90),
    512: (236, 200, 80),
    1024: (255, 207, 79),
    2048: (235, 190, 73),
    4096: (214, 174, 66),
    8192: (194, 157, 60),
    16384: (171, 139, 53),
    32768: (135, 110, 42),
    65536: (84, 68, 26),
}

GUIJIAO = {
    2: '啊',
    4: '死',
    8: '冰',
    16: '卧槽',
    32: '击败',
    64: 'Allin',
    128: '说的道理',
    256: '哈比下',
    512: '奥利安费',
    1024: '哈利路大旋风',
    2048: '哇 袄',
}


user32 = ctypes.windll.user32
screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
new_pos_x = screen_width // 2 - 200
new_pos_y = screen_height // 2 -  300
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (new_pos_x, new_pos_y)

pygame.init()


def play_game(grid, qg, flag):
    moveno = 0
    g = grid
    time_list = [time.time()]
    start = time.time()
    while not flag.is_set():
        moveno += 1
        board = g.map

        move = find_best_move(board)
        if len(time_list) > 20:
            time_list.pop(0)
        if move < 0:
            break
        g.move(move)
        qg.put(g.clone())
        if random.random() < 0.9:
            g.insertTile(g.getAvailableCells()[random.randint(0, len(g.getAvailableCells()) - 1)], 2)
        else:
            g.insertTile(g.getAvailableCells()[random.randint(0, len(g.getAvailableCells()) - 1)], 4)



class Tile:
    def __init__(self, pos, num, width, guijiao=False, new=False):
        self.pos = pos
        self.num = num
        self.width = width
        self._width = width
        self.new = new
        self.counter = 1

        color = NUM2COLOR[num]
        # if (0.299*color[0] + 0.587*color[1] + 0.114*color[2]) > 190:
        if num == 2 or num == 4:
            text_color = (120, 111, 106)
        else:
            text_color = (255, 255, 255)
        size = int(min(self.width * 0.7, self.width / len(str(num)) * 1.3))
        if guijiao:
            self.f = pygame.font.Font('C:/Windows/Fonts/msyh.ttc', int(size * 0.6))
        else:
            self.f = pygame.font.Font('C:/Windows/Fonts/seguibl.ttf', size)

        self.img = pygame.image.load('temp.png')
        self.img.fill((0, 0, 0, 0))
        pygame.draw.rect(self.img, color, (0, 0, self.width, self.width), border_radius=3)
        if num > 0:
            if guijiao:
                try:
                    text = GUIJIAO[num]
                except:
                    text = str(num)
                if len(text) <= 5:
                    text = self.f.render(text, True,
                                     text_color, color)
                    self.img.blit(text, (self.width / 2 - text.get_width() / 2, self.width
                                     / 2 - text.get_height() / 2))
                else:
                    text1 = self.f.render(text[:3], True,
                                     text_color, color)
                    text2 = self.f.render(text[3:], True,
                                     text_color, color)
                    self.img.blit(text1, (self.width / 2 - text1.get_width() / 2, self.width
                                     * 0.3 - text1.get_height() / 2))
                    self.img.blit(text2, (self.width / 2 - text2.get_width() / 2, self.width
                                     * 0.7 - text2.get_height() / 2))
            else:
                text = self.f.render(str(num), True,
                                     text_color, color)
                self.img.blit(text, (self.width / 2 - text.get_width() / 2, self.width
                                     / 2 - text.get_height() / 2))

    def draw(self, screen):
        limit = 8
        if self.new:
            if self.counter <= limit:
                self._img = pygame.transform.scale(self.img, (int(self.width * self.counter / limit),
                                                             int(self.width * self.counter / limit)))
                self.counter += 1
        else:
            self._img = pygame.transform.scale(self.img, (self._width, self._width))
        screen.blit(self._img, (self.pos[0] - self._img.get_width() // 2 + self.width // 2,
                               self.pos[1] - self._img.get_height() // 2 + self.width // 2))


class Button:
    def __init__(self, pos, width, height, text, text_color, bg_color, font_dir='C:/Windows/Fonts/seguibl.ttf'):
        self.width = width
        self.height = height
        self.pos = pos
        self.width = width
        self.bg_color = bg_color
        self.text_color = text_color
        self._text = text

        size = int(self.height * 0.5)
        self.f = pygame.font.Font(font_dir, size)

    def draw(self, screen):
        self.text = self.f.render(self._text, True, self.text_color, self.bg_color)
        pygame.draw.rect(screen, self.bg_color, (self.pos[0] - self.width * 0.5, self.pos[1] - self.height * 0.5, self.width, self.height), border_radius=4)
        screen.blit(self.text, (self.pos[0] - self.text.get_width() / 2, self.pos[1] - self.text.get_height() / 2))

    def is_in(self, pos):
        if self.pos[0] - self.width * 0.5 < pos[0] < self.pos[0] + self.width * 0.5 and self.pos[1] - self.height * 0.5 < pos[1] < self.pos[1] + self.height * 0.5:
            return True
        else:
            return False


class LoadingPage():
    def __init__(self):
        pygame.display.set_caption('loading 2048')
        self.screen = pygame.display.set_mode((200, 50), pygame.NOFRAME)
        self.f = pygame.font.Font('C:/Windows/Fonts/seguibl.ttf', 30)
        self.text = self.f.render('loading...', True, (255, 255, 255), (189, 173, 157))

    def main(self, flag):
        while not flag.is_set():
            self.screen.fill((189, 173, 157))
            self.screen.blit(self.text, (100 - self.text.get_width() / 2, 25 - self.text.get_height() / 2))
            pygame.display.update()
            pygame.display.flip()


class Game:
    def __init__(self):
        ld = LoadingPage()
        _f = threading.Event()
        t = Thread(target = ld.main, args=(_f,))
        t.start()
        
        # time.sleep(1)
        self.cell_width = 100
        self.space = 16
        self.counter = 0
        self.width = self.cell_width * 4 + self.space * 5
        self.height = self.width * 0.4
        self.bgcolor = (251, 248, 239)
        self.tiles_color = (189, 173, 157)
        self.pos = (0, 0)
        self.grids = [[None, None, None, None],
                      [None, None, None, None],
                      [None, None, None, None],
                      [None, None, None, None]]
        self.g = None
        self.UP = False
        self.DOWN = False
        self.LEFT = False
        self.RIGHT = False
        self.LOSE = False
        self.step = 0
        with open("cfg.json") as f:
            self.cfg = json.load(f)
        self.AI = False
        self.guijiao = self.cfg['gj']
        self.flag = threading.Event()
        self.flag.clear()
        self.qg = Queue()
        
        self.musics = {}

        for root, dirs, files in os.walk("./music"):
            name = root.split('\\')[-1]
            for file in files:
                try:
                    self.musics[name]
                except:
                    self.musics[name] = []
                try:
                    s1 = pygame.mixer.Sound(os.path.join(root, file))
                    s1.set_volume(0.5)
                    self.musics[name].append(s1)
                except pygame.error:
                    pass

        self.clock = pygame.time.Clock()
        size = int(self.height * 0.25)
        self.f = pygame.font.Font('C:/Windows/Fonts/seguibl.ttf', size)
        self.f_s = pygame.font.Font('C:/Windows/Fonts/seguibl.ttf', int(size * 0.5))
        self.tiles_img = pygame.Surface((self.width, self.width))
        pygame.draw.rect(self.tiles_img, self.tiles_color, (0, 0, self.width, self.width), border_radius=-1)
        for i in range(4):
            for j in range(4):
                Tile((j * (self.cell_width + self.space) + self.space,
                      i * (self.cell_width + self.space) + self.space),
                     0, self.cell_width, self.guijiao).draw(self.tiles_img)

        self.ai_button = Button((self.width * 0.4, self.height * 0.8), self.width * 0.2, self.height * 0.35, 'ai', (255, 255, 255), (143, 122, 101))
        self.ng_button = Button((self.width * 0.75, self.height * 0.8), self.width * 0.4, self.height * 0.35, 'new game', (255, 255, 255), (143, 122, 101))

        self.list_to_left = list(np.empty(65536))
        self.list_to_right = list(np.empty(65536))
        self.merge_to_left = list(np.empty(65536))
        self.merge_to_right = list(np.empty(65536))
        
        self.merged = []
        self.where_to_go = [[None, None, None, None],
                      [None, None, None, None],
                      [None, None, None, None],
                      [None, None, None, None]]
        for row in range(65536):
            board = [
                (row >>  0) & 0xf,
                (row >>  4) & 0xf,
                (row >>  8) & 0xf,
                (row >> 12) & 0xf]
            res = [-1] * 4
            res_m = []
            flag = [0] * 4
            # print(board)                            
            row_right = 0
            i = 3
            for c in board:
                row_right |= c << (4 * i)
                i -= 1
            for i in range(4):
                if board[i] == 0:
                    continue
                for j in range(i - 1, -1, -1):
                    if board[i] == board[j] and not flag[j]:
                        board[j] += 1
                        board[i] = 0
                        res[i] = j
                        res_m.append(j)
                        flag[j] = 1
                        break
                    elif board[j] > 0:
                        res[i] = j + 1
                        if i != j + 1:
                            board[j + 1] = board[i]
                            board[i] = 0
                        break
                    elif j == 0 and board[0] == 0:
                        res[i] = 0
                        if i != 0:
                            board[0] = board[i]
                            board[i] = 0

            self.list_to_left[row] = res
            self.merge_to_left[row] = res_m
            # print(row_right)
            self.list_to_right[row_right] = [-1 if i == -1 else (3 - i) for i in res][::-1]
            self.merge_to_right[row_right] = [(3 - i) for i in res_m][::-1]
            
        pygame.display.set_caption('2048')
        self.screen = pygame.display.set_mode((self.width, self.height + self.width))
        self.reset()
            
        self.thread = Thread(target=play_game, args=(self.g.clone(), self.qg, self.flag))

        _f.set()

    def reset(self):
        self.g = Grid()
        self.add_new_tile()
        self.LOSE = False
        for i in range(4):
            for j in range(4):
                if self.g.map[i][j] != 0:
                    self.grids[i][j] = Tile((j * (self.cell_width + self.space) + self.space,
                                             i * (self.cell_width + self.space) + self.space + self.height),
                                            self.g.map[i][j],
                                            self.cell_width, self.guijiao)

    def add_new_tile(self):
        if random.random() < 0.9:
            self.pos = self.g.insertTile(self.g.getAvailableCells()[random.randint(0, len(self.g.getAvailableCells()) - 1)], 2)
        else:
            self.pos = self.g.insertTile(self.g.getAvailableCells()[random.randint(0, len(self.g.getAvailableCells()) - 1)], 4)
        i, j = self.pos
        self.grids[i][j] = Tile((j * (self.cell_width + self.space) + self.space,
                                             i * (self.cell_width + self.space) + self.space + self.height),
                                            self.g.map[i][j], self.cell_width, self.guijiao, new=True)

    def key_down(self, event):
        if self.guijiao:
                li = self.musics["failed"] + self.musics["2"]
                li[random.randint(0, len(li) - 1)].play()
        if event.key == pygame.K_s:
            if 1 in self.g.getAvailableMoves():
                self.move(1)
        elif event.key == pygame.K_w:
            if 0 in self.g.getAvailableMoves():
                self.move(0)
        elif event.key == pygame.K_a:
            if 2 in self.g.getAvailableMoves():
                self.move(2)
        elif event.key == pygame.K_d:
            if 3 in self.g.getAvailableMoves():
                self.move(3)

    def start_ai(self):
        self.thread = Thread(target=play_game, args=(self.g.clone(), self.qg, self.flag))
        self.thread.start()

    def move(self, d):
        _map = copy.deepcopy(self.g.map)
        self.g.move(d)
        self.merged = []
        if self.guijiao:
            for num in self.g.merged:
                try:
                    li = self.musics[str(num)]
                    li[random.randint(0, len(li) - 1)].play()
                except:
                    pass
        if not self.AI:
            self.step = 0
            for i in range(4):
                for j in range(4):
                    if _map[i][j] != 0:
                        self.grids[i][j] = Tile((j * (self.cell_width + self.space) + self.space,
                                             i * (self.cell_width + self.space) + self.space + self.height),
                                            _map[i][j],
                                            self.cell_width, self.guijiao)
                        _map[i][j] = int(math.log2(_map[i][j]))
                    else:
                        self.grids[i][j] =  None
            if d == 0:  # up
                self.UP = True
                for j in range(4):
                    col = 0
                    for i in range(4):
                        col |= _map[i][j] << (4 * i)
                    for p in self.merge_to_left[col]:
                        self.merged.append((p, j))
                    for i in range(4):
                        if _map[i][j] == 0:
                            self.where_to_go[i][j] = None
                        elif self.list_to_left[col][i] == -1:
                            self.where_to_go[i][j] = (i, j)
                        else:
                            self.where_to_go[i][j] = (self.list_to_left[col][i], j)
            elif d == 1:  # down
                self.DOWN = True
                for j in range(4):
                    col = 0
                    for i in range(4):
                        col |= _map[i][j] << (4 * i)
                    for p in self.merge_to_right[col]:
                        self.merged.append((p, j))
                    for i in range(4):
                        if _map[i][j] == 0:
                            self.where_to_go[i][j] = None
                        elif self.list_to_right[col][i] == -1:
                            self.where_to_go[i][j] = (i, j)
                        else:
                            self.where_to_go[i][j] = (self.list_to_right[col][i], j)
            elif d == 3:  # right
                self.RIGHT = True
                for i in range(4):
                    row = 0
                    for j in range(4):
                        row |= _map[i][j] << (4 * j)
                    for p in self.merge_to_right[row]:
                        self.merged.append((i, p))
                    for j in range(4):
                        if _map[i][j] == 0:
                            self.where_to_go[i][j] = None
                        elif self.list_to_right[row][j] == -1:
                            self.where_to_go[i][j] = (i, j)
                        else:
                            self.where_to_go[i][j] = (i, self.list_to_right[row][j])
            else:  # left
                self.LEFT = True
                for i in range(4):
                    row = 0
                    for j in range(4):
                        row |= _map[i][j] << (4 * j)
                    for p in self.merge_to_left[row]:
                        self.merged.append((i, p))
                    for j in range(4):
                        if _map[i][j] == 0:
                            self.where_to_go[i][j] = None
                        elif self.list_to_left[row][j] == -1:
                            self.where_to_go[i][j] = (i, j)
                        else:
                            self.where_to_go[i][j] = (i, self.list_to_left[row][j])
            
    def main(self):
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.flag.set()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if not self.AI and not self.UP and not self.DOWN and not self.LEFT and not self.RIGHT: 
                        self.key_down(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    m_pos = pygame.mouse.get_pos()
                    if self.ai_button.is_in(m_pos):
                        if self.AI:
                            self.flag.set()
                            self.AI = False
                            self.ai_button.bg_color = (143, 122, 101)
                            for i in range(4):
                                for j in range(4):
                                    if self.g.map[i][j] != 0:
                                        self.grids[i][j] = Tile((j * (self.cell_width + self.space) + self.space,
                                                                 i * (self.cell_width + self.space) + self.space + self.height),
                                                                self.g.map[i][j],
                                                                self.cell_width, self.guijiao)
                        else:
                            self.flag.clear()
                            self.AI = True
                            self.ai_button.bg_color = (170, 170, 170)
                            self.start_ai()
                    elif self.ng_button.is_in(m_pos):
                        self.reset()

            if not self.thread.is_alive() and self.AI:
                self.AI = False
                self.ai_button.bg_color = (143, 122, 101)

            if not self.g.canMove():
                self.LOSE = True
            if self.AI:
                if not self.qg.empty():
                    g = self.qg.get()
                    self.g = g
                    if self.guijiao:
                        for num in self.g.merged:
                            try:
                                li = self.musics[str(num)]
                                li[random.randint(0, len(li) - 1)].play()
                            except:
                                pass

            if self.LOSE:
                self.counter += 1
                if self.counter >= 60:
                    self.counter = 0
                    self.reset()

            self.update()

    def set_grids(self):
        for i in range(4):
            for j in range(4):
                if self.g.map[i][j] != 0:
                    self.grids[i][j] = Tile((j * (self.cell_width + self.space) + self.space,
                                                                 i * (self.cell_width + self.space) + self.space + self.height),
                                                                self.g.map[i][j],
                                                                self.cell_width, self.guijiao)
                    self.grids[i][j].draw(self.screen)
                else:
                    self.grids[i][j] = None

    def update(self):
        self.screen.fill(self.bgcolor)
        self.screen.blit(self.tiles_img, (0, self.height))
        if self.AI:
            self.set_grids()
        else:
            if self.UP or self.DOWN or self.RIGHT or self.LEFT:
                limit = 8
                if self.step <= limit:
                    for i in range(4):
                        for j in range(4):
                            if self.grids[i][j]:
                                pos = self.where_to_go[i][j]
                                self.grids[i][j].pos =  ((j + (pos[1] - j) * self.step / limit) * (self.cell_width + self.space) + self.space, (i + (pos[0] - i) * self.step / limit) * (self.cell_width + self.space) + self.space + self.height)
                                self.grids[i][j].draw(self.screen)
                    self.step += 1
                elif self.step == limit + 1:
                    self.set_grids()
                    self.add_new_tile()
                    self.step += 1
                elif limit + 1 < self.step <= limit * 2:
                    for i in range(4):
                        for j in range(4):
                            if i == self.pos[0] and j== self.pos[1]:
                                self.grids[i][j].draw(self.screen)
                                continue
                            if self.grids[i][j]:
                                if (i, j) in self.merged:
                                    self.grids[i][j]._width = self.cell_width * (1.2 - 0.8 * (self.step / limit - 1.5) ** 2)
                                self.grids[i][j].draw(self.screen)
                    self.step += 1
                else:
                    self.UP , self.DOWN , self.RIGHT , self.LEFT = False, False, False, False
                    for i in range(4):
                        for j in range(4):
                            if self.grids[i][j]:
                                self.grids[i][j].draw(self.screen)
            else:
                for i in range(4):
                    for j in range(4):
                        if self.grids[i][j]:
                            self.grids[i][j].draw(self.screen)
        if self.LOSE:
            pass
            # pygame.draw.rect(self.screen, (125, 125, 125, 255), (0, self.height, self.width, self.width))

        score = self.f.render(str(self.g.score), True, (255, 255, 255), (187, 173, 160))
        text = self.f_s.render("score", True, (236, 224, 212), (187, 173, 160))
        rect = score.get_rect()
        width = max(round(rect.width, -1), text.get_width())
        pygame.draw.rect(self.screen, (187, 173, 160), (self.width - 5 - width * 1.1, 5, width * 1.1, rect.height * 1.5), border_radius=5)
        self.screen.blit(score, (self.width - 5 - width * 1.05, 5 + rect.height * 0.5))
        self.screen.blit(text, (self.width - 5 - width * 0.55 - text.get_width() / 2, 5 + rect.height * 0.1))

        self.ai_button.draw(self.screen)
        self.ng_button.draw(self.screen)

        pygame.display.update()
        pygame.display.flip()


if __name__ == '__main__':
    g = Game()
    g.main()
