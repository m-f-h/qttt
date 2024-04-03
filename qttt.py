#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" qttt.py - Quantum Tic-Tac-Toe

    14.3.-2.4.2024 by MFH
    
    Dedicated to Nonore.

    Ref.: https://en.wikipedia.org/wiki/Quantum_tic-tac-toe
"""
__version__ = "1.240402"
__author__ = "M. F. Hasler"
__copyright__ = "Copyright 2024 by M. F. Hasler"

class Move(dict):
    """A dict whose entry 'squares' gives a 2-tuple (square1, square2) with the
    two squares (e.g., "a1","b2") on which the quantum piece is to be placed
    on the board. 
    Upon initialisation (see Move.__init__ for signature), it MAY have entries:
    'squares' (str, str): 2-tuple of the squares on which the Piece is placed
    'board' (Board): the board on which this move is considered
            (allows to check for legal coordinates and "entanglement")
    'pending' (bool): move requires a decision to be made by the next player
            (if square1 & square2 are already "entangled" prior to the move)
    """
    def __repr__(self): # return f"Move({super().__repr__()})"
        return f"Move('{','.join(self['squares'])}'"+(
            ", pending=True"if self.get('pending')else'')+(
            ", board=<Board at 0x{id(self['board']):x}>"
            if'board'in self else'')+")"
    def __init__(self, *args, **kwargs) -> 'Board':
        """The args can be:
    squares: (str | tuple[str] | None): either a 2-tuple (sq1,sq2) where
            strings sq1, sq2 are coordinates of the squares (e.g.: "a1", "b2")
            or a string starting with sq1 and ending with sq2. 
    board: ('Board' | None) = None: the board on which the move is made.
    Each of these args can also be given as kwargs, e.g.: squares=(sq1,sq2), or
    as a dict with entries 'squares' and/or 'board'. Only 'squares' is required.
        """
        def check_duplicate(item):
            """Check whether arg 'item' already given earlier/ elsewhere."""
            if item in kwargs:
                raise ValueError(f"Got argument '{arg}', but "# of type {type(arg)}
                                 f"{item}={kwargs[item]} is already defined.")
            kwargs[item] = arg
            # return None
            
        for arg in args:
            if isinstance(arg, (str,tuple,list)):
                check_duplicate("squares")
            elif isinstance(arg, Board):
                check_duplicate("board")                
            elif isinstance(arg, dict): # includes type(arg)==Move (which may
                # contain 'board' in addition to 'squares'), but not type Board
                any(map(check_duplicate, arg))
            else:
                raise ValueError("Unexpected argument {arg}")
        self |= kwargs
        
        ### validity check of 'squares'

        if 'squares' not in self:
            raise ValueError("No squares given.")
        
        if isinstance(self['squares'], str):
            # arg (expected of the form "a1,b2") will be split in 2 squares
            move = self['squares'].strip() # remove whitespace
            if len(move)<4:
                raise ValueError(f"Move must be of the form 'a1,a2', got '{move}'")

            # To allow for multi-digit row specification, we increase
            # the length of the first or last substring to 3 when the
            # 3rd (resp. 2nd-last) character is a digit
            self['squares'] = (move[:2+move[2].isdigit()],
                               move[-2-move[-2].isdigit():])
            
        # by now, self['squares'] should be of type tuple or list
        if len(self['squares']) != 2:
            raise ValueError(f"Expected exactly 2 squares, got {self['squares']}")

        for s in self['squares']:
            if not Square(s).is_valid_format:
                raise ValueError(f"'{s}' is not a valid square specification.")
        if s==self['squares'][0]:
            raise ValueError(f"Squares must be different, got {self['squares']}")

        # if a board was given, check whether coordinates are legal
        if board := self.get('board'):
            if not all(map(board.is_valid_square, self['squares'])):
                raise ValueError(f"Coordinates {self['squares']} out of range")
                #                f" must be in {{{board.cols}}} x {board.rows}")
            if board.debug > 3:
                print(f"OK - {repr(self)} is initialized.")

class Square(str):
    "A square specification of the form 'a1' or 'z99'."
    @property
    def is_valid_format(s: str):
        return 1<len(s)<4 and s[0].isalpha() and s[1:].isdigit() and int(s[1:])
    
class Board(dict):
    """A board for playing quantum Tic-tac-toe:
    The board is square, of size N x N with N = 3 by default.
    The squares can be empty or occupied with exactly one classical X or O
    or with any number of quantum X's or O's.

    The 2 players take turns placing a quantum X or a quantum O's
    on any *two* squares by specifying their coordinates, e.g.: "a1-b2".

    Each such quantum X or O entangle the two squares.
    Classically, the X or O exist on only one of the two squares,
    but until the quantum pieces "collapse", we don't know on which
    square they are.
    The "collapse" happens when entangled squares form a loop.
    At that moment, the particles on all of the linked squares reduce to
    classical ones that can be on exactly one of the two squares.
    The player who did NOT create the loop chooses the outcome, i.e.,
    to which square one of the quantum particle reduces, which fixes the
    position of all other particles on linked squares.
Methods:
    play(queue=[]): interactively play a game, starting with input listed in 'queue'
    push(move): make a move, must be a string of the form "a1,b2" (where "," may be any string),
        or just "a1" if a "decision" is awaited (see 'pending' below)
    undo(N=1): undo the N last moves/decisions
    __str__(): return ASCI representation of board & status information.
Attributes:
    symbols: (default: "XO") symbols representing the player's pieces
    size: (default: 3) size (# rows & columns) of the board. Can only be set at initialization.
    rows: (default: "123"): symbols of rows
    cols: (default: "abc"): symbols of columns
    squares: list of squares = [c+r for c in cols for r in rows]
    groups: generator of generators of the sequence of squares that form diagonals, rows & cols
    turn: symbol of the player who has to make the next move
    is_game_over: true if game is over
    score: > 0 or < 0 if the first or second player won, 0 if frawn, 'None' if game isn't over
    winner: symbol of the player who won ('X'/'O' by default), '-' if draw, None if game isn't over
    moves: list of moves (of class 'Move') made so far
    pending: tuple of 0 or 2 strings of the form 'a1' specifying a square of the board.
        If nonzero, a decision is awaited, on where the last placed quantum piece will
        collapse to a classical piece.
    """
    symbols = 'XO' # symbols used by the (two(?)) players, and symbol for "no winner/drawn"

    def __missing__(self, key):
        if self.is_valid_square(key):
            return set() # empty set for squares that don't have a piece yet
        getattr(self,key) # mainly winner, score
        
    def __init__(self, *args, **kwargs):
        "Initialize a quantum tic-tac-toe board. (kw)args include: size, other info/board to copy."
        for arg in args:
            if isinstance(arg, int):
                if 'size' in kwargs:
                    raise ValueError(f"Got integer argument '{arg}' but size ="
                                     f" {kwargs['size']} was already defined.")
                kwargs['size']=arg
            elif isinstance(arg, dict): kwargs |= arg
            else:
                raise ValueError(f"Don't know what to do with argument '{arg}'.")
        self.moves = []
        self.backups = []
        self.used_pieces = set()
        super().__init__(**kwargs)
    @property
    def debug(self): return self.get('debug', False)
    @property
    def size(self): return self.get('size', 3)
    @property
    def pending(self): return self.get('pending', ())
    @property
    def cols(self):
        """Return string 'abc...' of letters allowed as column specifier."""
        if not hasattr(self,'_cols'):
            self._cols = str(bytes(range(97, 97+self.size)), encoding='ascii')
        return self._cols
    @property
    def rows(self):
        """Tuple ('1','2','3',...) of valid row specifiers (may exceed '9'!)."""
        if not hasattr(self,'_rows'):
            self._rows = tuple(map(str, range(1, self.size+1)))
            #self._rows = [str(i+1)for i in range(self.size)]
        return self._rows
    @property
    def squares(self):
        """Return list of all squares 'a1', 'a2', ..., 'c3' in order from
        top left to bottom right, i.e., a3, b3, c3; a2, b2, c2; a1, b1, c1
        (or similar for larger boards)."""
        if not hasattr(self,'_squares'):
            self._squares = [col+row for row in self.rows[::-1]
                                     for col in self.cols]
        return self._squares
    def is_valid_square(self, s: str):
        """Whether 's' is a valid square specifier, i.e., between 'a1' and 'z#',
        where # = board size and 'z' is the corresponding letter."""
        return s[1:] in self.rows and s[0] in self.cols
    @property
    def groups(self):
        "A sequence of generators of the diagonal & horizontal & vertical rows."
        cols,rows = self.cols,self.rows
        yield(c+r for c,r in zip(cols,rows))    # main diagonal
        yield(c+r for c,r in zip(cols,rows[::-1])) # antidiagonal
        for c in cols: yield(c+r for r in rows) # vertical files
        for r in rows: yield(c+r for c in cols) # horizontal ranks
    @property
    def is_game_over(self):
        return self.score is not None # equivalent: isinstance(score, int)
    @property
    def winner(self):
        """Return the winner's id ('X' or 'O'),'-' if game is drawn, or None if game hasn't ended yet."""
        return self.symbols[s<0] if (s:=self.score) else'-'if s==0 else None
    @property
    def score(self):
        """None if game not over, 0 if draw, > 0 or < 0 if 1st or 2nd player has won."""
        if self.get('score', False) is False:
            self['score'] = self.compute_score()
        return self['score']

    def compute_score(self):
        if self.pending: return # if there is a pending decision, there's no winner yet
        winner = ''
        for group in self.groups:
            player = ''
            for square in group:
                if not self.is_classical(square): break
                if not player: player = min(self[square])
                elif player != min(self[square]): break
            else: # reached the end of a group => found a winning group
                # if we already have a winner, then their score grows
                # if it's the same, or the game is drawn ("both won").
                if winner and player != winner[0]:
                    return 0        # "both win": draw
                winner += player
            # otherwise (i.e., a break occurred) proceed with next group
        if winner:
            return len(winner)if winner[0]==self.symbols[0] else-len(winner)
        # no winner found => draw if the game is over (board full), else None
        return 0 if all(self.is_classical(s) for s in self.squares) else None
    @property
    def turn(self):
        "Return the player ('X' or 'O') whose turn it is."
        return self.symbols[len(self.moves)&1]
    @property
    def row_height(self):
        """Number of text rows (& 'columns') needed to fit in all pieces in the
        fullest cell: ceil(sqrt(max_pieces_per_square)): 1=>1, 2..4=>2, 5..9=>3..."""
        return int(self.max_pieces_per_square**.5-1e-3)+1
    MPPS='max_pieces_per_square'
    @property
    def max_pieces_per_square(self):
        if self.debug>9:
            print(f"{self.MPPS}: {self.get(self.MPPS,'undefined')}")
        if type(self.get(self.MPPS, None))!=int:# WARNING: isinstance(False,int)=True!
            self[self.MPPS] = max((len(self[square]) for square in self
                                   if self.is_valid_square(square)), default=0)
            if self.debug > 4:
                print(f"{self.MPPS}: set to {self[self.MPPS]}")
        return self[self.MPPS]
    
    def __str__(self) -> str:
        """Return str(self)."""
        # each piece uses 2 characters + inter-piece space ("X1 X2", ...)
        self.cell_width = self.row_height * 3 - 1 # subsequent functions use this
        bar = '-' * self.cell_width
        row_separator = "\n" + bar . join('+' * (self.size+1)) + "\n"
        return row_separator . join(self . text_rows())

    def text_rows(self):
            """Generate the sequence of text rows for a 2D character display of self.
            First and last row give information about the current status of the game.
            These and the intermediate rows of the board are separated by a row_separator.
            Each row of the board corresponds to self.row_height rows of text, which
            are concatenated and sent as whole, to yield a result of the form:
              " Board after move 0:
                +--+--+--+
                |  |  |  |
                +--+--+--+
                |  |  |  |
                +--+--+--+
                |  |  |  |
                +--+--+--+
                Player 'X' to play. "
            """
            yield f"Board after move {len(self.moves)}: (score: {self.score})"
            cols = self.cols ; row_height = self.row_height
            row_mask = f'|{{:^{self.cell_width}}}' * len(cols) + '| {}' 
            for r in self.rows[::-1]:
                # First, compute the contents for all cells of this row.
                cells = [self.cell(c+r) for c in cols]
                # Then send the text rows (with the i-th row of each cell) one by one
                yield "\n".join(row_mask.format(*(cell[i] for cell in cells),
                                                r if i==row_height//2 else'')
                                for i in range(row_height))
            # now the last 2 rows: labels of columns, and status line (player to move...)
            yield ''.join(" "+c.center(self.cell_width) for c in cols) + '\n' + self.status()
    def cell(self, square) -> list:
            """Return a list of 'row_height' strings which represent the pieces on square."""
            nr = self.row_height ; c = [''] * nr ; r = nr//2 # start in the middle
            for piece in self[square]:
                c[r] += " " + piece if c[r] else piece
                r = (r+1) % nr
            return c
    def status(self) -> str:
        """Return string describing the game status (drawn, decision awaited, who to play/has won/lost)."""
        return "The game is drawn." if self.score==0 else f"Player '{self.turn}' " + (
                f"must decide about {self.moves[-1]['piece']}: {' or '.join(self.pending)} ?"
                if self.pending else "to play." if self.score is None
                else f"has {'won'if self.winner==self.turn else'lost'}.")

    def is_classical(self, square) -> bool:
        """True iff this square is occupied by a classical piece."""
        return len(self[square])==1 and min(self[square]).is_classical

    def entangled(self, src, dest):
        """Are the two squares entangled?"""
        queue = {src}; visited = set()
        while queue:
            square = queue.pop()
            assert square not in visited # shouldn't happen
            visited |= {square}
            for piece in self[square]:
                if piece.other == dest: return True
                if piece.other not in visited:
                    queue |= {piece.other}

    def push(self, move: (str,tuple,Move)):
        """Make a move (= place a quantum piece on two squares) or decision."""
        
        if self.pending: # is a decision pending? (then move = choice)
            return self.decide(move)

        if isinstance(move, (str,tuple)): # probably always 'str'
            move = Move(move, board=self)
        squares = move['squares']
    
        if any(self.is_classical(s) for s in squares):
            raise ValueError("Both squares must be free of classical pieces.")
        
        # if the 2 squares are entangled, the move leads to classical collapse:
        if self.entangled(*squares):    # then next player decides how/where
            self['pending'] = squares       # quantum pieces will collapse 
            move['pending'] = True
        elif 'pending' in move: # else no decision awaited
            del move['pending']
        
        # now create the quantum piece(s) on the two squares
        piece_name = self.get_piece_name()
        for i in (0,1):
            piece = Piece(piece_name); piece.other = squares[1-i]
            self[squares[i]] |= {piece}
        move['piece'] = piece ; self.moves.append(move)
            
        # check whether max_pieces_per_square must be updated
        
        M = max(len(self[s]) for s in squares)
        if M > self['max_pieces_per_square']:
            self['max_pieces_per_square'] = M

        self.pop('score',0) # must recompute.
        if self.debug > 2: print(f"OK - push({move}) done.")

    def get_piece_name(self):
        """Return next available name for a quantum piece. (Currently just
        'X'/'O'+(move number) - To do: better manage (un)used numbers."""
        m = len(self.moves)
        #self.used_pieces |= {piece_name}
        return self.symbols[m&1] + str(m//2+1)
        
    def decide(self, choice):
        if choice not in self.pending:
            raise Exception("No decision awaited/possible.") if not self.pending\
                else ValueError(f"Incorrect decision: must be one of {self.pending}.")
        self.backup_current_state() # for undo()
        piece = self.moves[-1]['piece']
        print(f"Decision is: piece {piece} must go on square {choice}.")
        self.make_classical(choice, piece)
        del self['pending']
        self.pop('score',0)
        self.pop('max_pieces_per_square',0)

    def backup_current_state(self):
        self.backups.append(self.copy())# could be more economical
    def restore_backup(self):
        "Replace all content of self with backup pop()'d off self.backups."
        if not self.backups:
            raise Exception("Error: no backup information available for undo()")
        self.clear()
        self |= self.backups.pop()
        assert not self.pending
        #if debug>2: print("***WARNING: after restore_backup, "
        #        "position is not pending:\n", repr(self))

    def make_classical(self, square, piece):
        """Reduce 'piece' on 'square' to classical state and recursively "push"
        the other pieces here to collapse on their respective 'other' square."""
        
        if piece not in self[square]:
            # piece was queued for removal but has already been removed
            if self.debug > 3:
                print(f"mk: Piece '{piece}' no more on square '{square}'.")
            return
        self.used_pieces -= {piece}     # "free" this piece label
        
        # To make recursion more efficient and avoid loops, we remove all pieces
        # on this square and keep their list separately, before going recursive.
        pieces = self[square]
        self[square] = {Piece(piece[0])} # first letter (i.e., X or O) only
        for p in pieces:
            # All of the pieces on this square should be quantum pieces,
            # although the partner of some of them might already have disappeared
            if p != piece:
                #assert hasattr(p,'other') # always True: only quantum pieces here
                self.make_classical(p.other, p) # implies the above assert
    
    def undo(self, number_of_moves: int = 1):
        """Undo the given number of moves or 'decisions'."""
        while number_of_moves > 0:
            if not self.moves:
                raise Exception("Error: no move to undo!")

            # Must we rather undo a decision? This is the case when the last
            # move did require one, but not the board, i.e., it's already made.
            if self.moves[-1].get('pending') and not self.pending:
                self.restore_backup()
            else:
                move = self.moves.pop()
                for s in move['squares']:
                    self[s] -= {move['piece']}
                if 'pending' in move:
                    del self['pending']
                self.pop(self.MPPS,0)

            number_of_moves -= 1    # one less remaining to undo
        #end undo

    def help(self, choice):
        if choice and choice[0] in'Rr':
            print("""Welcome to QTTT : Quanum Tic-Tac-Toe.
Players 'X' and 'O' take turns to play a move.
A move consists in choosing *two* squares on which you put your quantum piece (X or O).
You can enter "a1,b2" or similar (instead of "," there can be anything or nothing).
Both squares may contain nothing or any number of quantum pieces, but no classical piece.
A quantum pieces exists simultaneausly on two squares;
it has a number attached to the 'X' or 'O' in order to know which/where the "other part" is.
The quantum piece you place will collapse to one single classical piece on one of the squares,
if the two squares you chose were already directly or indirectly connected through other
quantum pieces. It is your opponent who decides, after you have played your move, on which
of the two squares your quantum piece will collapse. This will induce a chain reaction,
because the other quantum piece(s) on that square can no more exist here and must collapse on
their "other" square, and so on). The opponent enters his choice as a single square (e.g., "a1").
Once the quantum pieces have collapsed, the game will end if one of the players has a complete
row or diagonal of classical pieces. If this is the case for both players,
or for none of the players but all squares are filled with classical pieces,
then the game is drawn.""")
            input("\t(Hit 'Enter' to continue.)")
        else: # if choice[0]=='?':
            print("Commands: '?' = this. 'u' = undo last move/decision. 'r' = rules of the game.\n"
                "'q'/'x'/'exit' = quit game. 'a1-%s' = place quantum piece on the given squares."
                % (self.cols[-1]+self.rows[-1]))
    #end of help()
    def play(self, queue=None):
        """You can supply a 'queue' = list of initial moves (and/or "decisions") which will
        be read and interpreted as if you entered them interactively."""
        while not self.is_game_over:
            print(self)
            if queue:
                print("Choice is", move := queue.pop(0))
            else:
                move = input("What is the choice ('?' for help): ")
            move = move.strip().lower()
            if not move or move[0] in'?r':
                    self.help(move); continue
            if move[0]=='u':
                    self.undo(); continue
            if move[0] in 'qx' or move=="exit":
                    move=input("Are you sure you want to quit? ")
                    if move and move[0].upper() != 'N': break
                    continue
            try:
                if self.debug>5:
                    print(f"try push({move}): mpps={self.get(self.MPPS,'undef')}")
                self.push(move)
                if self.debug>4: print("OK - play({move}) done.")
            except ValueError as E:
                print("Error:", E) # offer help again, here?
        print(self, "\nBye-bye! I hope you enjoyed the game!"
              "\nTo play again, just enter Board().play()"
              "\nTo play on a larger board, do e.g.: Board(4).play()")
    #end play()
#end class Board()
        
class Piece(str):
    """A piece on a quantum TTT board. The object itself is its name,
    e.g., 'X', 'O' (or 'X1', 'O2', ... for quantum pieces in the current implementation
    -- in a graphical implementation one might not need the numerical index).
(Possible) attributes:
    other: label of the *other* square on which this quantum piece is (also/
        possibly) located. No 'other' <=> classical piece <=> len(self)==1.
    """
    @property
    def is_classical(self):
        """Return whether this a classical piece, located on only ONE well defined square."""
        #return len(self)==1 # simpler but not necessarily valid in other implementations 
        return not getattr(self, 'other', None)

if __name__=='__main__':
    print("""Welcome to Quantum Tic-Tac-Toe!
    In this example game, the first 4 moves are pre-programmed.
    Enter '?' for help, 'r' for rules, 'x' to exit this example game.""")
    ttt = Board(debug=2)
    ttt.play(queue = ["a1-b2",'a3b3','b2b3','a1a3'])

#EOF
