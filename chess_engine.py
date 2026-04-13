import pygame
import chess
import random
import sys
import time

WIDTH = HEIGHT = 640
SQ_SIZE = WIDTH // 8
FPS = 15

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)

IMAGES = {}
transposition_table = {}

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

pawn_table = [
 0,0,0,0,0,0,0,0,
 5,5,5,5,5,5,5,5,
 1,1,2,3,3,2,1,1,
 0,0,0,2,2,0,0,0,
 0,0,0,-2,-2,0,0,0,
 1,-1,-2,0,0,-2,-1,1,
 1,2,2,-2,-2,2,2,1,
 0,0,0,0,0,0,0,0
]

def load_images():
    pieces = {
        "P": "white-pawn.png", "N": "white-knight.png",
        "B": "white-bishop.png", "R": "white-rook.png",
        "Q": "white-queen.png", "K": "white-king.png",
        "p": "black-pawn.png", "n": "black-knight.png",
        "b": "black-bishop.png", "r": "black-rook.png",
        "q": "black-queen.png", "k": "black-king.png"
    }
    for p, file in pieces.items():
        img = pygame.image.load("images/" + file)
        IMAGES[p] = pygame.transform.scale(img, (SQ_SIZE, SQ_SIZE))

def draw_board(screen, flip, selected):
    for r in range(8):
        for c in range(8):
            x = (c if not flip else 7-c) * SQ_SIZE
            y = (7-r if not flip else r) * SQ_SIZE
            color = LIGHT if (r+c)%2==0 else DARK
            rect = pygame.Rect(x, y, SQ_SIZE, SQ_SIZE)
            pygame.draw.rect(screen, color, rect)

            if selected is not None:
                sf = chess.square_file(selected)
                sr = chess.square_rank(selected)
                if flip:
                    sf, sr = 7-sf, 7-sr
                if sf==c and sr==r:
                    pygame.draw.rect(screen, HIGHLIGHT, rect, 4)

def draw_pieces(screen, board, flip):
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            if flip:
                f, r = 7-f, 7-r
            screen.blit(IMAGES[piece.symbol()],
                        pygame.Rect(f*SQ_SIZE,(7-r)*SQ_SIZE,SQ_SIZE,SQ_SIZE))

def get_square(pos, flip):
    x, y = pos
    f = x // SQ_SIZE
    r = 7 - (y // SQ_SIZE)
    if flip:
        f, r = 7-f, 7-r
    return chess.square(f, r)


def evaluate(board):
    if board.is_checkmate():
        return -999999 if board.turn else 999999

    score = 0
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            val = piece_values[piece.piece_type]

            if piece.piece_type == chess.PAWN:
                if piece.color == chess.WHITE:
                    val += pawn_table[sq]
                else:
                    val -= pawn_table[chess.square_mirror(sq)]

            score += val if piece.color == chess.WHITE else -val

    return score

def order_moves(board, moves):
    def score(m):
        if board.is_capture(m): return 10
        if m.promotion: return 9
        if board.gives_check(m): return 8
        return 0
    return sorted(moves, key=score, reverse=True)

def minimax(board, depth, alpha, beta, maximizing):
    key = board.fen()
    if key in transposition_table:
        return transposition_table[key]

    if depth == 0 or board.is_game_over():
        return evaluate(board)

    moves = order_moves(board, list(board.legal_moves))

    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            board.push(move)
            eval = minimax(board, depth-1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        transposition_table[key] = max_eval
        return max_eval

    else:
        min_eval = float('inf')
        for move in moves:
            board.push(move)
            eval = minimax(board, depth-1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[key] = min_eval
        return min_eval

def best_move(board, depth):
    best = None
    best_val = -float('inf') if board.turn else float('inf')

    for move in order_moves(board, list(board.legal_moves)):
        board.push(move)
        val = minimax(board, depth-1, -float('inf'), float('inf'), not board.turn)
        board.pop()

        if board.turn:
            if val > best_val:
                best_val = val
                best = move
        else:
            if val < best_val:
                best_val = val
                best = move

    return best


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess AI")
    clock = pygame.time.Clock()

    load_images()
    board = chess.Board()

    color = input("Choose your color (white/black): ").strip().lower()
    human_white = True if color == "white" else False
    flip = not human_white

    selected = None
    running = True

    while running:
        human_turn = (board.turn == chess.WHITE and human_white) or \
                     (board.turn == chess.BLACK and not human_white)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if human_turn and event.type == pygame.MOUSEBUTTONDOWN:
                sq = get_square(pygame.mouse.get_pos(), flip)

                if selected is None:
                    piece = board.piece_at(sq)
                    if piece and piece.color == board.turn:
                        selected = sq
                else:
                    move = chess.Move(selected, sq)
                    if move in board.legal_moves:
                        board.push(move)
                    selected = None

        if not human_turn:
            time.sleep(0.5)
            move = best_move(board, 3)
            if move:
                board.push(move)

        draw_board(screen, flip, selected)
        draw_pieces(screen, board, flip)
        pygame.display.flip()

        if board.is_game_over():
            print("Game Over:", board.result())
            time.sleep(3)
            running = False

        clock.tick(FPS)

if __name__ == "__main__":
    main()