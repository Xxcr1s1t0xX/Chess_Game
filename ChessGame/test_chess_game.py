import unittest
from chess_game import ChessGame, Move

class ChessGameTests(unittest.TestCase):
    def empty_board(self):
        game = ChessGame()
        game.board = [['.' for _ in range(8)] for _ in range(8)]
        game.turn = 'w'
        game.castling = set()
        game.en_passant = None
        return game

    def test_opening_has_twenty_moves(self):
        self.assertEqual(len(ChessGame().legal_moves('w')), 20)

    def test_legal_move_cannot_expose_king(self):
        game = self.empty_board()
        game.board[7][4] = 'K'
        game.board[7][0] = 'r'
        game.board[6][5] = 'P'
        self.assertFalse(Move((6,5),(5,5)) in game.legal_moves('w'))

    def test_en_passant(self):
        game = self.empty_board()
        game.board[3][4] = 'P'
        game.board[3][3] = 'p'
        game.en_passant = (2,3)
        self.assertIn(Move((3,4),(2,3)), game.legal_moves('w'))

    def test_promotion(self):
        game = self.empty_board()
        game.board[1][0] = 'P'
        game.board[0][0] = '.'
        moves = game.legal_moves('w')
        promotions = {m.promotion for m in moves if m.from_sq == (1,0) and m.to_sq == (0,0)}
        self.assertEqual(promotions, {'q','r','b','n'})

    def test_castling(self):
        game = self.empty_board()
        game.board[7][4] = 'K'
        game.board[7][7] = 'R'
        game.castling = {'K'}
        self.assertIn(Move((7,4),(7,6)), game.legal_moves('w'))

    def test_stalemate(self):
        game = self.empty_board()
        game.board[0][7] = 'k'
        game.board[1][5] = 'K'
        game.board[2][6] = 'Q'
        game.turn = 'b'
        self.assertEqual(game.result(), 'Stalemate - Draw')

    def test_checkmate(self):
        game = ChessGame()
        for move in (
            Move((6,5),(5,5)), Move((1,4),(3,4)),
            Move((6,6),(4,6)), Move((0,3),(4,7)),
        ):
            game.apply_move(move, track=False)
        self.assertEqual(game.result(), 'Checkmate - Black wins')

if __name__ == '__main__':
    unittest.main()
