import json
import random
import sys
import time
import os

import pygame
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


"""for k in NUM2COLOR.keys():
    if k != 0:
        NUM2COLOR[k] = (random.randint(200, 255),
                        random.randint(100, 255),
                        random.randint(0, 100))"""
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
    def __init__(self, pos, num, width, guijiao=False):
        self.pos = pos
        self.num = num
        self.width = width

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
        screen.blit(self.img, self.pos)


class Button:
    def __init__(self, pos, width, height, text, text_color, bg_color, font_dir='C:/Windows/Fonts/seguibl.ttf'):
        self.width = width
        self.height = height
        self.pos = pos
        self.width = width
        self.bg_color = bg_color

        size = int(self.height * 0.5)
        self.f = pygame.font.Font(font_dir, size)
        self.text = self.f.render(text, True, text_color, bg_color)

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, (self.pos[0] - self.width * 0.5, self.pos[1] - self.height * 0.5, self.width, self.height), border_radius=4)
        screen.blit(self.text, (self.pos[0] - self.text.get_width() / 2, self.pos[1] - self.text.get_height() / 2))

    def is_in(self, pos):
        if self.pos[0] - self.width * 0.5 < pos[0] < self.pos[0] + self.width * 0.5 and self.pos[1] - self.height * 0.5 < pos[1] < self.pos[1] + self.height * 0.5:
            return True
        else:
            return False


class Game:
    def __init__(self):
        self.cell_width = 100
        self.space = 16
        self.counter = 0
        self.width = self.cell_width * 4 + self.space * 5
        self.height = self.width * 0.4
        self.bgcolor = (251, 248, 239)
        self.tiles_color = (189, 173, 157)
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
        self.guijiao = True
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

        self.ai_button = Button((self.width * 0.4, self.height * 0.8), self.width * 0.2, self.height * 0.35, 'ai', (255, 255, 255), (143, 122, 101))
        self.ng_button = Button((self.width * 0.75, self.height * 0.8), self.width * 0.4, self.height * 0.35, 'new game', (255, 255, 255), (143, 122, 101))

        pygame.display.set_caption('2048')
        self.screen = pygame.display.set_mode((self.width, self.height + self.width))
        self.reset()

    def reset(self):
        self.g = Grid()
        self.add_new_tile()
        self.LOSE = False
        for i in range(4):
            for j in range(4):
                if self.g.map[i][j] != 0:
                    self.grids[i][j] = Tile((i * (self.cell_width + self.space) + self.space,
                                             j * (self.cell_width + self.space) + self.space + self.height),
                                            self.g.map[i][j],
                                            self.cell_width)

    def add_new_tile(self):
        if random.random() < 0.9:
            self.g.insertTile(self.g.getAvailableCells()[random.randint(0, len(self.g.getAvailableCells()) - 1)], 2)
        else:
            self.g.insertTile(self.g.getAvailableCells()[random.randint(0, len(self.g.getAvailableCells()) - 1)], 4)

    def key_down(self, event):
        if self.guijiao:
                li = self.musics["failed"]
                li[random.randint(0, len(li) - 1)].play()
        if event.key == pygame.K_s:
            if 1 in self.g.getAvailableMoves():
                self.move(1)
                self.add_new_tile()
        elif event.key == pygame.K_w:
            if 0 in self.g.getAvailableMoves():
                self.move(0)
                self.add_new_tile()
        elif event.key == pygame.K_a:
            if 2 in self.g.getAvailableMoves():
                self.move(2)
                self.add_new_tile()
        elif event.key == pygame.K_d:
            if 3 in self.g.getAvailableMoves():
                self.move(3)
                self.add_new_tile()

    def start_ai(self):
        thread = Thread(target=play_game, args=(self.g.clone(), self.qg, self.flag))
        thread.start()

    def move(self, d):
        self.g.move(d)
        if self.guijiao:
            for num in self.g.merged:
                try:
                    li = self.musics[str(num)]
                    li[random.randint(0, len(li) - 1)].play()
                except:
                    pass
            
    def main(self):
        while True:
            # self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.flag.set()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self.key_down(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    m_pos = pygame.mouse.get_pos()
                    if self.ai_button.is_in(m_pos):
                        if self.AI:
                            self.flag.set()
                            self.AI = False
                        else:
                            self.flag.clear()
                            self.AI = True
                            self.start_ai()
                    elif self.ng_button.is_in(m_pos):
                        self.reset()

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

    def update(self):
        self.screen.fill(self.bgcolor)
        pygame.draw.rect(self.screen, self.tiles_color, (0, self.height, self.width, self.width), border_radius=-1)
        for i in range(4):
            for j in range(4):
                Tile((j * (self.cell_width + self.space) + self.space,
                      i * (self.cell_width + self.space) + self.space + self.height),
                     self.g.map[i][j], self.cell_width, self.guijiao).draw(self.screen)
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
