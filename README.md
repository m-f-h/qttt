# qttt - Quantum tic-tac-toe - (c) 2024 by MFH

Mini-game "quantum tic-tac-toe": see [Wikipedia](https://en.wikipedia.org/wiki/Quantum_tic-tac-toe)

Provides the main class `Board`, and misc classes `Move` and `Square`, both rather for internal use.

A `Board` can be initialized to an arbitrary `size` which by default equals 3. 
Currently only a square board is implemented, but one might implement `size = (m,n)` for rectangular boards,
in which case a row of min(m,n) same pieces aligned in the same direction should win, I guess.

A `Board` has the interactive method `play()` providing a text interface that displays 
the board (through `str(self)`) and invites the players to enter their move (e.g., "a1,c3") 
or decision (e.g., "a1") or ask for help about the rules or other possible commands like
"undo" a move or decision, show the rules, exit the game etc.

These actions use the more elementary methods `push(move: str)` to make a move (or decision),
`undo(number_of_moves: int = 1)`, `help(choice: str = '')`.

It is sufficient to enter `Board().play()` to play a game on a standard sized board.

If the main/module file is executed, it invites to play a game where 3 - 4 moves are already made.
* You can use the "u" = "undo" command to get back to the starting position.
* Use "?" to get information about other commands
* (To-do: add "reset/restart" -- currently "r" = "rules")

Currently there's only a text interface to play. 
To-do:
* graphical interface
* implement possibility to play against a remote opponent (server/client arcitecture).
If anyone is interested to add one of the above, I'd appreciate. Lean code is preferred.
