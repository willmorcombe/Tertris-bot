# tetris bot
# plan - take screenshot, decide best possible move for that piece based off score
# scored well for placing in a hole, and not going too high.
# using tetris.com so dont have to create my own tetris.


# open https://tetris.com/play-tetris , when ready to start press enter
import pyautogui as ss
import webbrowser
import time
from pynput import *
from pynput.keyboard import Key, Controller
import numpy as np
from PIL import Image, ImageOps
import random



def on_release(key):
    if key == keyboard.Key.ctrl_l:
        # Stop listener
        return False

# gets initial position of game window
def startGame():
    print("Press left control to open tetris")

    with keyboard.Listener(on_release=on_release) as listener:
        listener.join()

    #open game
    webbrowser.open('https://tetris.com/play-tetris')

    print("Press left control to run game (make sure the game and next box are in view)")

    while True:

        with keyboard.Listener(on_release=on_release) as listener:
            listener.join()

        # locate game coords for screeshots
        x = ss.locateOnScreen("screenshots/find.png", confidence=0.9)

        if x == None:
            print("Game not found, make sure game is in view")
        else:
            break

    return x

# get the position of the box region
def getNextBoxRegion():
    x = ss.locateOnScreen("screenshots/find_next_box.png", confidence=0.9)
    if x == None:
        print("Cant find next box")

    return x

# if there is a patten of this -> 1 0 1
#                                 1 0 1
# then make a return a bad score
def checkThinLines(grid):
    level = maxLevelCheck(grid)
    mid_patten = np.array([[1, 0, 1],
                           [1, 0, 1]])

    right_patten = np.array([[1, 0],
                            [1, 0]])

    left_patten = np.array([[0, 1],
                             [0, 1]])
    score = 0
    # check middle patten
    for x in range(19 - (level + 1)):
        # print('\n', x)
        for i in range(8):
            if np.array_equal(grid[18-x:20-x, i:3+i], mid_patten):
                score += 1

    # check left patten
    for x in range(19 - (level + 1)):
        # print(grid[18-x:20-x, :2])
        if np.array_equal(grid[18-x:20-x, :2], left_patten):
            score += 1


    # ceheck right patten
    for x in range(19 - (level + 1)):
        if np.array_equal(grid[18-x:20-x, 8:10], right_patten):
            score += 0

    return score


def getNextPiece(next_box_region):

    piece_screenshot = ImageOps.grayscale(ss.screenshot(region=next_box_region))
    piece_screenshot.save('screenshots/next_piece.png')
    piece_screenshot_list = np.asarray(piece_screenshot)


    color = piece_screenshot_list[175][121]

    switcher = {
        64: 1, # t-shape
        96: 2, # dark blue L (left)
        49: 3, # red lightning
        36: 4, # long thin
        148: 5, # square
        124: 6, # orage L (right)
        128: 7 # green lightning
    }
    shape = switcher.get(color, "can't see shape - quitting") # add force stop

    return shape

#get score based on grid state, returns score to add to list
def getScore(grid, level):
    # the higher the level the better
    # the more gaps the worse

    level_score = level * 1.5

    holes_score = 0

    for x in range(level, 19):
        for i in range(10):
            if grid[x][i] == 1 and grid[x + 1][i] == 0:
                holes_score += 1


    holes_score *= 8 # punishing the hoes more

    thin_lines_score = checkThinLines(grid)
    return level_score - holes_score - thin_lines_score

#checks to see the highest piece on the board, returns that integer
def maxLevelCheck(grid):
    for y in range(len(grid[:, 0])):
        for x in range(len(grid[0])):
            if grid[y][x] == 1:
                return y -1

def checkClearLines(grid):
    indices = []
    for x in range(20):
        if all(grid[x] == [ 1 for x in range(10)]):
            indices.append(x)

    if indices:
        time.sleep(0.3)
    for x in indices:
        grid = np.delete(grid, x, 0)
        grid = np.insert(grid, 0, 0, 0)


    return grid


# get the best move for that shaped based off of the grid
def getBestMove(shape, grid):
    # if the move makes the stack high - bad
    # if the move makes a hole - bad
    # can add more rules

    all_positions = getAllShapePositions(shape)
    score_list = []
    # for each rotation get score of that position at lowest point and addd to list
    # pick position and rotation with highest lowest score as the best move

    # level of the highest piece sticking out 19 is bottom 0 is top


    for rotation, piece in enumerate(all_positions):
        piece_width = piece.shape[1]
        piece_height = piece.shape[0]


        for column in range(10 -  piece_width + 1):

            # check to see the lowest position the piece can be placed
            level = maxLevelCheck(grid[:, column:piece_width + column])

            # print(level)

            column_levels = []
            for i in range(piece_width):
                x = 1
                while True:
                    if piece[piece_height - x][i] == 1:
                        column_levels.append(piece_height - x)
                        break
                    else:
                        x += 1

            flag = True
            level -= 1
            while flag:
                level += 1
                for index, elm in enumerate(column_levels):

                    if grid[level - (piece_height -1 - elm)][column:piece_width + column][index] == 1 and piece[elm][index] == 1:
                        level -= 1
                        flag = False



            grid_before = grid.copy()

            # place piece
            for x in range(piece_height):
                for i in range(piece_width):
                    if piece[x][i] == 1:
                        grid[level - (piece_height - x-1)][i + column] = 1


            level = level - piece_height

            # print(grid, '\n')

            grid_state = grid.copy()
            #get score of move
            score = getScore(grid, level)
            score_list.append([score,(column,rotation, piece_width), grid_state, shape] )

            level = level + piece_height

            # remove the piece from board
            grid = grid_before

    list_of_indexs = []
    maxi = max(score_list)[0]
    for index, elm in enumerate(score_list):
        if elm[0] == maxi:
            list_of_indexs.append(index)

    return score_list[random.choice(list_of_indexs)]

# return a list of all shape positions at every angle
#[0 1 0 ] [1 0 ]
#[1 1 1 ] [1 1 ]
#         [1 0 ]
# and so on...
def getAllShapePositions(shape):
    # shape definitions
    t_shape = np.asarray([[0, 1, 0],
                          [1, 1, 1]])
    left_L = np.asarray([[1, 0, 0],
                         [1, 1, 1]])
    red_light = np.asarray([[1, 1, 0],
                            [0, 1, 1]])
    long_thin = np.asarray([[1, 1, 1, 1]])
    square = np.asarray([[1, 1],
                         [1, 1]])
    right_L = np.asarray([[0, 0, 1],
                          [1, 1, 1]])
    green_light = np.asarray([[0, 1, 1],
                              [1, 1, 0]])

    switcher = {
        1: t_shape, # t-shape
        2: left_L, # dark blue L (left)
        3: red_light, # red lightning
        4: long_thin, # long thin
        5: square, # square
        6: right_L, # orage L (right)
        7: green_light # green lightning
    }

    # only these shapes need to be rotated 90 degrees 4 times
    if shape == 1 or shape == 2 or shape == 6:
        flip = 4
    else:
        flip = 2

    shape_array = switcher.get(shape, "ERROR")
    shape_array = np.rot90(shape_array)
    # order of list, normal, left 90, down, right 90
    shape_list = []

    for x in range(flip):
        shape_array = np.rot90(shape_array, 3)
        shape_list.append(shape_array)


    return shape_list

#make move based on the best move given
def executeMove(move):


    start_col = 3
    shape_width = move[1][2]
    rotation = move[1][1]
    column = move[1][0]
    piece = move[3]

    if rotation == 0:
        if piece == 5:
            start_col = 4

    elif rotation == 1:
        if piece == 4:
            start_col = 5
        else:
            start_col = 4

    # do rotation of piece
    for x in range(rotation):
        time.sleep(0.065)
        keyboard.press(Key.up)
        keyboard.release(Key.up)

    if column > start_col:
        for x in range(column - start_col):
            time.sleep(0.065)
            keyboard.press(Key.right)
            keyboard.release(Key.right)

    if column < start_col:
        for x in range(start_col - column):
            time.sleep(0.065)
            keyboard.press(Key.left)
            keyboard.release(Key.left)


    time.sleep(0.065)
    keyboard.press(Key.space)
    keyboard.release(Key.space)

    updated_grid = move[2] # this is the grid state
    print(move[3])
    return updated_grid


# THINGS TO DO
#   - PUNISH FOR LEAVING A THIN LINE
#   - IF YOU FILL IN HOLES BELOW THE MAX HEIGHT IN THE GRID ITS A GOOD MOVE

if __name__ == '__main__':

    game_region = startGame()

    keyboard = Controller()

    next_box_region = getNextBoxRegion()

    game_grid = np.asarray([[0 for x in range(10)] for x in range(21)])
    game_grid[20] = 1

    print(game_region)
    print(next_box_region)


    keyboard.press(Key.enter)
    keyboard.release(Key.enter)

    time.sleep(2)
    next_shape = getNextPiece(next_box_region)
    time.sleep(2)

    #get first piece and find best move

    max_level = 19
    x = 0
    while max_level != 1:
        if x == 0:
            move = getBestMove(next_shape, game_grid)
        else:
            move = getBestMove(next_shape, grid)
        grid = executeMove(move)


        grid = checkClearLines(grid)
        print('ACTUAL GRID SEEN')
        print(grid)
        next_shape = getNextPiece(next_box_region)
        print(maxLevelCheck(grid))
        time.sleep(0.08)
        x += 1

















    # game_screenshot = ss.screenshot("screenshots/game.png", region=game_region)
