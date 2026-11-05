import copy
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass

EMPTY = "."
FILES = "abcdefgh"
PIECE_VALUES = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}
UNICODE = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656", "B": "\u2657", "N": "\u2658", "P": "\u2659",
    "k": "\u265A", "q": "\u265B", "r": "\u265C", "b": "\u265D", "n": "\u265E", "p": "\u265F",
}

@dataclass(frozen=True)
class Move:
    from_sq: tuple
    to_sq: tuple
    promotion: str = ""

class ChessGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [
            list("rnbqkbnr"), list("pppppppp"), list("........"), list("........"),
            list("........"), list("........"), list("PPPPPPPP"), list("RNBQKBNR")
        ]
        self.turn = "w"
        self.castling = set("KQkq")
        self.en_passant = None
        self.halfmove = 0
        self.fullmove = 1
        self.history = []
        self.move_history = []

    def color_of(self, piece):
        if piece == EMPTY:
            return None
        return "w" if piece.isupper() else "b"

    def save_state(self):
        return (copy.deepcopy(self.board), self.turn, self.castling.copy(), self.en_passant,
                self.halfmove, self.fullmove, list(self.move_history))

    def restore_state(self, state):
        (self.board, self.turn, self.castling, self.en_passant,
         self.halfmove, self.fullmove, self.move_history) = state

    def king_square(self, color):
        king = "K" if color == "w" else "k"
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == king:
                    return (row, col)
        return None

    def is_attacked(self, square, by_color):
        row, col = square
        pawn = "P" if by_color == "w" else "p"
        pawn_source_row = row + 1 if by_color == "w" else row - 1
        for dc in (-1, 1):
            if 0 <= pawn_source_row < 8 and 0 <= col + dc < 8:
                if self.board[pawn_source_row][col + dc] == pawn:
                    return True
        knight = "N" if by_color == "w" else "n"
        for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == knight:
                return True
        king = "K" if by_color == "w" else "k"
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == king:
                    return True
        for dr, dc, kinds in ((-1,0,"qr"),(1,0,"qr"),(0,-1,"qr"),(0,1,"qr"),
                              (-1,-1,"qb"),(1,1,"qb"),(1,-1,"qb"),(-1,1,"qb")):
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = self.board[r][c]
                if piece != EMPTY:
                    if self.color_of(piece) == by_color and piece.lower() in kinds:
                        return True
                    break
                r += dr; c += dc
        return False

    def in_check(self, color=None):
        color = color or self.turn
        square = self.king_square(color)
        return square is not None and self.is_attacked(square, "b" if color == "w" else "w")

    def pseudo_moves(self, row, col):
        piece = self.board[row][col]
        if piece == EMPTY:
            return []
        color = self.color_of(piece)
        kind = piece.lower()
        moves = []

        def add_if_empty_or_capture(r, c):
            if 0 <= r < 8 and 0 <= c < 8:
                target = self.board[r][c]
                if target == EMPTY or self.color_of(target) != color:
                    moves.append(Move((row, col), (r, c)))

        if kind == "p":
            direction = -1 if color == "w" else 1
            start = 6 if color == "w" else 1
            promotion_row = 0 if color == "w" else 7
            one = row + direction
            if 0 <= one < 8 and self.board[one][col] == EMPTY:
                if one == promotion_row:
                    for promotion in "qrbn":
                        moves.append(Move((row, col), (one, col), promotion))
                else:
                    moves.append(Move((row, col), (one, col)))
                    two = row + 2 * direction
                    if row == start and self.board[two][col] == EMPTY:
                        moves.append(Move((row, col), (two, col)))
            for dc in (-1, 1):
                c = col + dc
                if 0 <= one < 8 and 0 <= c < 8:
                    target = self.board[one][c]
                    if target != EMPTY and self.color_of(target) != color:
                        if one == promotion_row:
                            for promotion in "qrbn":
                                moves.append(Move((row, col), (one, c), promotion))
                        else:
                            moves.append(Move((row, col), (one, c)))
                    elif (one, c) == self.en_passant:
                        moves.append(Move((row, col), (one, c)))
        elif kind == "n":
            for dr, dc in ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)):
                add_if_empty_or_capture(row + dr, col + dc)
        elif kind in ("b", "r", "q"):
            directions = []
            if kind in ("b", "q"):
                directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if kind in ("r", "q"):
                directions += [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    target = self.board[r][c]
                    if target == EMPTY:
                        moves.append(Move((row, col), (r, c)))
                    else:
                        if self.color_of(target) != color:
                            moves.append(Move((row, col), (r, c)))
                        break
                    r += dr; c += dc
        elif kind == "k":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr != 0 or dc != 0:
                        add_if_empty_or_capture(row + dr, col + dc)
            enemy = "b" if color == "w" else "w"
            if not self.in_check(color):
                if color == "w" and row == 7 and col == 4:
                    if "K" in self.castling and self.board[7][7].upper() == "R" and self.board[7][5] == self.board[7][6] == EMPTY:
                        if not self.is_attacked((7,5), enemy) and not self.is_attacked((7,6), enemy):
                            moves.append(Move((row,col),(7,6)))
                    if "Q" in self.castling and self.board[7][0].upper() == "R" and all(self.board[7][c] == EMPTY for c in (1,2,3)):
                        if not self.is_attacked((7,3), enemy) and not self.is_attacked((7,2), enemy):
                            moves.append(Move((row,col),(7,2)))
                if color == "b" and row == 0 and col == 4:
                    if "k" in self.castling and self.board[0][7].lower() == "r" and self.board[0][5] == self.board[0][6] == EMPTY:
                        if not self.is_attacked((0,5), enemy) and not self.is_attacked((0,6), enemy):
                            moves.append(Move((row,col),(0,6)))
                    if "q" in self.castling and self.board[0][0].lower() == "r" and all(self.board[0][c] == EMPTY for c in (1,2,3)):
                        if not self.is_attacked((0,3), enemy) and not self.is_attacked((0,2), enemy):
                            moves.append(Move((row,col),(0,2)))
        return moves

    def apply_move(self, move, track=True):
        if track:
            self.history.append(self.save_state())
        fr_row, fr_col = move.from_sq
        to_row, to_col = move.to_sq
        piece = self.board[fr_row][fr_col]
        captured = self.board[to_row][to_col]
        color = self.color_of(piece)
        notation = self.move_notation(move, captured)

        self.board[fr_row][fr_col] = EMPTY
        if piece.lower() == "p" and move.to_sq == self.en_passant and captured == EMPTY:
            self.board[fr_row][to_col] = EMPTY

        placed = piece
        if move.promotion:
            placed = move.promotion.upper() if color == "w" else move.promotion.lower()
        self.board[to_row][to_col] = placed

        if piece.lower() == "k" and abs(to_col - fr_col) == 2:
            if to_col == 6:
                self.board[to_row][5], self.board[to_row][7] = self.board[to_row][7], EMPTY
            else:
                self.board[to_row][3], self.board[to_row][0] = self.board[to_row][0], EMPTY

        if piece == "K": self.castling.discard("K"); self.castling.discard("Q")
        if piece == "k": self.castling.discard("k"); self.castling.discard("q")
        if move.from_sq == (7,0) or move.to_sq == (7,0): self.castling.discard("Q")
        if move.from_sq == (7,7) or move.to_sq == (7,7): self.castling.discard("K")
        if move.from_sq == (0,0) or move.to_sq == (0,0): self.castling.discard("q")
        if move.from_sq == (0,7) or move.to_sq == (0,7): self.castling.discard("k")

        if piece.lower() == "p" and abs(to_row - fr_row) == 2:
            self.en_passant = ((fr_row + to_row) // 2, fr_col)
        else:
            self.en_passant = None
        if piece.lower() == "p" or captured != EMPTY:
            self.halfmove = 0
        else:
            self.halfmove += 1
        if color == "b":
            self.fullmove += 1
        self.turn = "b" if self.turn == "w" else "w"
        if track:
            if self.in_check(self.turn):
                notation += "+"
            self.move_history.append(notation)

    def undo(self):
        if not self.history:
            return False
        state = self.history.pop()
        self.restore_state(state)
        return True

    def legal_moves(self, color=None):
        color = color or self.turn
        result = []
        for row in range(8):
            for col in range(8):
                if self.color_of(self.board[row][col]) == color:
                    for move in self.pseudo_moves(row, col):
                        state = self.save_state()
                        self.apply_move(move, track=False)
                        still_safe = not self.in_check(color)
                        self.restore_state(state)
                        if still_safe:
                            result.append(move)
        return result

    def move_notation(self, move, captured):
        piece = self.board[move.from_sq[0]][move.from_sq[1]]
        name = "" if piece.lower() == "p" else piece.upper()
        destination = FILES[move.to_sq[1]] + str(8 - move.to_sq[0])
        if piece.lower() == "k" and abs(move.to_sq[1] - move.from_sq[1]) == 2:
            return "O-O" if move.to_sq[1] == 6 else "O-O-O"
        if piece.lower() == "p" and captured != EMPTY:
            return FILES[move.from_sq[1]] + "x" + destination
        if piece.lower() == "p" and move.to_sq == self.en_passant:
            return FILES[move.from_sq[1]] + "x" + destination
        return name + ("x" if captured != EMPTY else "") + destination + ("=" + move.promotion.upper() if move.promotion else "")

    def result(self):
        moves = self.legal_moves()
        if moves:
            return None
        if self.in_check():
            return "Checkmate - " + ("Black" if self.turn == "w" else "White") + " wins"
        return "Stalemate - Draw"

    def evaluate(self):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != EMPTY:
                    value = PIECE_VALUES[piece.lower()]
                    score += value if piece.isupper() else -value
        return score

    def minimax(self, depth, alpha, beta, maximizing):
        result = self.result()
        if depth == 0 or result:
            return self.evaluate() if not result else (1000000 if "Black" in result else -1000000)
        moves = self.legal_moves()
        if maximizing:
            value = -100000000
            for move in moves:
                state = self.save_state()
                self.apply_move(move, track=False)
                value = max(value, self.minimax(depth - 1, alpha, beta, False))
                self.restore_state(state)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        value = 100000000
        for move in moves:
            state = self.save_state()
            self.apply_move(move, track=False)
            value = min(value, self.minimax(depth - 1, alpha, beta, True))
            self.restore_state(state)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    def choose_ai_move(self, depth=2):
        moves = self.legal_moves("b")
        if not moves:
            return None
        best_move = moves[0]
        best_score = 100000000
        for move in moves:
            state = self.save_state()
            self.apply_move(move, track=False)
            score = self.minimax(depth - 1, -100000000, 100000000, True)
            self.restore_state(state)
            if score < best_score:
                best_score = score
                best_move = move
        return best_move

class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess")
        self.root.resizable(False, False)
        self.game = ChessGame()
        self.selected = None
        self.legal_targets = set()
        self.flipped = False
        self.ai_mode = tk.BooleanVar(value=True)

        self.square_size = 72
        self.canvas = tk.Canvas(root, width=576, height=576, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=12, pady=12)
        self.canvas.bind("<Button-1>", self.on_click)

        side = tk.Frame(root, width=210)
        side.grid(row=0, column=1, sticky="ns", padx=(0,12), pady=12)
        self.status = ttk.Label(side, text="White to move", font=("Segoe UI", 12, "bold"))
        self.status.pack(anchor="w", pady=(0,10))
        ttk.Checkbutton(side, text="Play vs computer (Black)", variable=self.ai_mode,
                        command=self.on_mode_change).pack(anchor="w")
        button_frame = ttk.Frame(side)
        button_frame.pack(fill="x", pady=10)
        ttk.Button(button_frame, text="New Game", command=self.new_game).grid(row=0,column=0,padx=(0,6),pady=4)
        ttk.Button(button_frame, text="Flip Board", command=self.flip_board).grid(row=0,column=1,pady=4)
        ttk.Button(side, text="Undo", command=self.undo).pack(fill="x")
        ttk.Separator(side).pack(fill="x", pady=12)
        ttk.Label(side, text="Move history", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.history = tk.Text(side, width=24, height=25, font=("Consolas", 10), state="disabled")
        self.history.pack(fill="both", expand=True)
        self.draw()

    def display_square(self, row, col):
        return (7-row, 7-col) if self.flipped else (row, col)

    def board_square(self, x, y):
        col, row = x // self.square_size, y // self.square_size
        if self.flipped:
            return (7-row, 7-col)
        return (row, col)

    def draw(self):
        self.canvas.delete("all")
        for display_row in range(8):
            for display_col in range(8):
                row, col = self.display_square(display_row, display_col)
                x1, y1 = display_col*self.square_size, display_row*self.square_size
                color = "#EEEED2" if (row + col) % 2 == 0 else "#769656"
                if self.selected == (row,col):
                    color = "#F5F682"
                elif (row,col) in self.legal_targets:
                    color = "#BACA44" if self.game.board[row][col] == EMPTY else "#DE7A68"
                self.canvas.create_rectangle(x1,y1,x1+self.square_size,y1+self.square_size, fill=color, outline=color)
                piece = self.game.board[row][col]
                if piece != EMPTY:
                    self.canvas.create_text(x1+36,y1+35,text=UNICODE[piece],font=("Segoe UI Symbol",44),fill="#F9F7EF" if piece.islower() else "#2D2D2D")
        result = self.game.result()
        if result:
            self.status.configure(text=result)
        else:
            self.status.configure(text=("White" if self.game.turn == "w" else "Black") + " to move" + (" - Check" if self.game.in_check() else ""))
        self.update_history()

    def update_history(self):
        self.history.configure(state="normal")
        self.history.delete("1.0","end")
        moves = self.game.move_history
        for i in range(0,len(moves),2):
            white = moves[i]
            black = moves[i+1] if i+1 < len(moves) else ""
            self.history.insert("end",f"{i//2+1}. {white:<9} {black}\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def on_click(self, event):
        if self.game.result():
            return
        if self.ai_mode.get() and self.game.turn == "b":
            return
        row, col = self.board_square(event.x, event.y)
        piece = self.game.board[row][col]
        if self.selected:
            move = next((m for m in self.game.legal_moves(self.game.turn)
                         if m.from_sq == self.selected and m.to_sq == (row,col)), None)
            if move:
                self.make_human_move(move)
                return
        if self.game.color_of(piece) == self.game.turn:
            self.selected = (row,col)
            self.legal_targets = {m.to_sq for m in self.game.legal_moves(self.game.turn) if m.from_sq == self.selected}
        else:
            self.selected = None
            self.legal_targets.clear()
        self.draw()

    def make_human_move(self, move):
        if move.promotion:
            move = Move(move.from_sq,move.to_sq,self.choose_promotion())
        self.game.apply_move(move)
        self.selected = None
        self.legal_targets.clear()
        self.draw()
        if self.ai_mode.get() and self.game.turn == "b" and not self.game.result():
            self.root.after(250, self.make_ai_move)

    def choose_promotion(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Promote pawn")
        dialog.resizable(False,False)
        dialog.grab_set()
        choice = tk.StringVar(value="q")
        for symbol,label in (("q","Queen"),("r","Rook"),("b","Bishop"),("n","Knight")):
            tk.Radiobutton(dialog,text=label,variable=choice,value=symbol,padx=12,pady=4).pack(anchor="w")
        def accept(): dialog.destroy()
        ttk.Button(dialog,text="Promote",command=accept).pack(pady=8)
        self.root.wait_window(dialog)
        return choice.get()

    def make_ai_move(self):
        if self.game.result() or self.game.turn != "b":
            return
        move = self.game.choose_ai_move()
        if move:
            if move.promotion:
                move = Move(move.from_sq, move.to_sq, "q")
            self.game.apply_move(move)
        self.draw()

    def new_game(self):
        self.game.reset()
        self.selected = None
        self.legal_targets.clear()
        self.draw()

    def flip_board(self):
        self.flipped = not self.flipped
        self.draw()

    def undo(self):
        if self.ai_mode.get():
            self.game.undo()
            self.game.undo()
        else:
            self.game.undo()
        self.selected = None
        self.legal_targets.clear()
        self.draw()

    def on_mode_change(self):
        if self.ai_mode.get() and self.game.turn == "b":
            self.root.after(250,self.make_ai_move)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.mainloop()
