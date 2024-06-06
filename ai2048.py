#!/usr/bin/python
# -*- coding: utf-8 -*-

''' Help the user achieve a high score in a real game of 2048 by using a move searcher. '''
# g++ -shared -o 2048.dll 2048.cpp


from __future__ import print_function

import ctypes
import math
import os
import random
import sys
import time

from grid import Grid

# Enable multithreading?
MULTITHREAD = True

for suffix in ['so', 'dll', 'dylib']:
    dllfn = './2048.' + suffix
    if not os.path.isfile(dllfn):
        continue
    ailib = ctypes.CDLL(dllfn)
    break
else:
    print("Couldn't find 2048 library bin/2048.{so,dll,dylib}! Make sure to build it first.")
    sys.exit()

ailib.init_tables()

ailib.find_best_move.argtypes = [ctypes.c_uint64]
ailib.score_toplevel_move.argtypes = [ctypes.c_uint64, ctypes.c_int]
ailib.score_toplevel_move.restype = ctypes.c_float


def to_c_board(m):
    board = 0
    i = 0
    for row in m:
        for c in row:
            if c == 0:
                res = 0
            else:
                res = int(math.log2(c))
            board |= res << (4 * i)
            i += 1
    return board


def print_board(m):
    for row in m:
        for c in row:
            print('%8d' % c, end=' ')
        print()


if MULTITHREAD:
    from multiprocessing.pool import ThreadPool

    pool = ThreadPool(4)


    def score_toplevel_move(args):
        return ailib.score_toplevel_move(*args)


    def find_best_move(m):
        board = to_c_board(m)

        # print_board(m)

        scores = pool.map(score_toplevel_move, [(board, move) for move in range(4)])
        bestmove, bestscore = max(enumerate(scores), key=lambda x: x[1])
        if bestscore == 0:
            return -1
        return bestmove
else:
    def find_best_move(m):
        board = to_c_board(m)
        return ailib.find_best_move(board)


def movename(move):
    return ['up', 'down', 'left', 'right'][move]


def play_game():
    moveno = 0
    g = Grid()
    time_list = [time.time()]
    if random.random() < 0.9:
        g.insertTile(g.getAvailableCells()[random.randint(0, len(g.getAvailableCells()) - 1)], 2)
    else:
        g.insertTile(g.getAvailableCells()[random.randint(0, len(g.getAvailableCells()) - 1)], 4)
    start = time.time()
    while 1:
        moveno += 1
        board = g.map

        move = find_best_move(board)
        time_list.append(time.time())
        if len(time_list) > 20:
            time_list.pop(0)
        if move < 0:
            break
        print("%010.6f: Score %d, Move %d: %s" % (time_list[0] - start, g.score, moveno, movename(move)))
        print("average speed: %.2f, current 20 move step speed: %.2f" % (moveno / (time_list[-1] - start),
                                                                          len(time_list) / (time_list[-1]
                                                                                            - time_list[0])))
        g.move(move)
        if random.random() < 0.9:
            g.insertTile(g.getAvailableCells()[random.randint(0, len(g.getAvailableCells()) - 1)], 2)
        else:
            g.insertTile(g.getAvailableCells()[random.randint(0, len(g.getAvailableCells()) - 1)], 4)


def main():
    play_game()


if __name__ == '__main__':
    main()
