# qttt - Quantum tic-tac-toe - (c) 2024 by MFH

Mini-game "quantum tic-tac-toe": see [Wikipedia](https://en.wikipedia.org/wiki/Quantum_tic-tac-toe)

Provides the main `class Board(dict)`, and misc `class Move(dict)` and `class Square(str)`, 
both rather for internal use and mainly to encapsulate the related methods/attributes/checks.

A `Board` can be initialized to an arbitrary `size` (= # rows = # columns) which by default equals 3. 
Currently only a square board is implemented, but one might consider `size = (m,n)` for rectangular boards,
in which case I think a row of min(m,n) same pieces aligned in the same direction should win.

A `Board` has the interactive method `play()` providing a text interface with 2D display of 
the board (through `self.__str__`) and inviting the players to enter their move (e.g., "a1,c3") 
or decision (e.g., "a1") or ask for help about the rules or other possible commands like
"undo" a move or decision, show the rules, exit the game etc.

These actions use the more elementary methods `push(move: str)` to make a move (or decision),
`undo(number_of_moves: int = 1)`, `help(choice: str = '')`. There are also many attributes 
including `winner`, `score`, `is_game_over`, `turn`, `symbols`, `cols` (the valid letters), 
`rows` (numerical labels), `groups` (generator of the diagonals, rows and columns), ...

It is sufficient to enter `Board().play()` to play a game on a standard sized board,
or `Board(4).play()` to play on a 4x4 board, etc.

If the main/module file is executed, it invites to play a game where 3 - 4 moves are already made.
* You can use the "u" = "undo" command to get back to the starting position.
* (**TO-DO:** add "reset/restart" -- currently "r" = "rules")
* Use "?" to get information about other commands

## TO-DO:
Currently there's only a text interface to play, and the players must input their moves through the same input stream. It would be nice to 
* implement a graphical interface,
* implement the possibility to play against a remote opponent (server/client architecture),
* implement a computer player (maybe with level/strength = search depth, using a minimax/negamax with
  alpha-beta pruning and some simple heuristics, esp. number of aligned classical / quantum pieces).
  
If anyone is interested to add one of the above, I'd appreciate. (Lean code is preferred.)

I also consider creating a collection of (lean code) modules providing the different components for such games:
- an abstract class `Board` that provides as many generic methods as possible/reasonable
- should a computer player for such a Board game be implemented as a method of the Board, or as a separate class `Engine`?
- same for the possibility of playing a remote opponent: method of Board or separate class/module?
- maybe the computer player could be an instance of a remote opponent?
