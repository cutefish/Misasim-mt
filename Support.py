# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

# This file contains support for class projects.

from Tkinter import *
from tkFileDialog   import *
from random import randint, random, choice, shuffle, randrange
from colorsys import rgb_to_hls, hls_to_rgb
from os import stat, listdir
from math import log, ceil
from copy import copy

# MindSweeper (based on MS "Minesweeper" and Linux "Mines" games)

class P027 :
    def __init__(Self, Handler, Windows=True, Mode=1) :
        Self.Handler = Handler
        Self.Windows = Windows
        Self.Mode = Mode
        Self.FieldWidth = 8  # 16
        Self.FieldHeight = 8  # 16
        Self.FieldArea = Self.FieldWidth * Self.FieldHeight
        Self.MinesDensity = 0.25  # 0.20
        """Field keeps track of the current info the
           student pgm has uncovered or inferred so far.
           Field[XY] = n, where n is
              U: unopened (initial value)
              F: flagged
              n: opened/guessed, n mines nearby
              B: opened/guessed mine blew up"""
        Self.Field = ['U'] * Self.FieldArea
        # Some data representation ideas (those based on sets) come from
        # Beni Cherniavsky-Paskin <cben@users.sf.net>
        # Site: http://cben-hacks.sf.net/python/smartsweeper/
        #
        # These are sets that record positions of ALL guesses, not just the
        # ones encountered so far as step through trace.
        Self.NecessaryGuesses = set()
        Self.UnnecessaryGuesses = set() # if nonempty, student program fails 
        # Set of all squares that are opened deliberately (not as a guess)
        # If any of these positions has B, student program fails.
        Self.Opened = set()
        # Set of all squares that are flagged. At end of program, this
        # set should be a subset of _mines.  (The only positions in _mines
        # that are not in Flagged are NecessaryGuesses that are mines.) 
        Self.Flagged = set()
        # If a square in Field[XY] is not U, it is in exactly one of these
        # four sets.

        # This set records positions that are overwritten.  If nonempty,
        # student program fails.
        Self.Overwrites = set()

        Self._mines = set()  # hidden data
        # FieldStack and CurrentField (stack ptr) are needed for Next/Prev_SWI
        Self.FieldStack = [['U'] * Self.FieldArea]
        Self.CurrentField = 0
        if Windows :
            Self.Window = Toplevel()
            Self.Window.title('Mindsweeper 1.0')
            Self.CellSize = 24
            Self.Offset = 5
            Self.Width = (Self.FieldWidth+1) * Self.CellSize
            Self.Height = (Self.FieldHeight+1) * Self.CellSize
            Self.Canvas = Canvas(Self.Window, width=Self.Width,
                                 height=Self.Height, bg='white')
            Self.Canvas.pack(expand=YES, fill=BOTH)

    def Reset_State(Self) :
        """Reinitialize state that is specific to each trial run."""
        Self.Field = ['U'] * Self.FieldArea
        Self.FieldStack = [['U'] * Self.FieldArea]
        Self.CurrentField = 0
        Self.NecessaryGuesses = set()
        Self.UnnecessaryGuesses = set()
        Self.Opened = set()
        Self.Flagged = set()
        Self.Overwrites = set()
        Self._mines = set()  # hidden data

    # These two are used for any swi's that change state that is visualized.
    # The Stack keeps track of snapshots of state that need to be sequenced
    # through either by forward stepping (Next_SWI) or by backward stepping
    # (Prev_SWI) in the simulation's trace.  These two methods call the
    # GUI method that will update the display.
    def Next_SWI(Self, Interrupt) :
        if Interrupt == 568 and Self.Windows :
            Self.CurrentField += 1
            Self.Display_Mine_Field(Self.FieldStack[Self.CurrentField])

    def Prev_SWI(Self, Interrupt) :
        if Interrupt == 568 and Self.Windows :
            Self.CurrentField -= 1
            Self.Display_Mine_Field(Self.FieldStack[Self.CurrentField])

    # This is an example of a swi that initializes the project state.
    # It begins by reinitializing any state that is specific to each
    # trial run.
    # It ends by opening the GUI canvas and displaying the initial state.
    # It also initializes the Stack used by Next/Prev_SWI.
    # It is not intended to be a swi whose interrupt number triggers
    # Next/Prev_SWI.
    def SWI_Bury_Mines(Self) :
        """ This routine calculates number of mines to bury based on
            Self.MinesDensity.  It then randomly places that number
            of mines, recording their positions in Self.mines.
            It returns the number of mines in register $1"""
        if Self.Windows :
            try:
                Self.Canvas.config(height=Self.Height,
                                   width=Self.Width, bg='white')
            except TclError:
                Self.__init__(Self.Handler, Self.Windows, Self.Mode)
        Self.Reset_State()
        mines_number = int(Self.MinesDensity * Self.FieldArea)
        while len(Self._mines) < mines_number:
            position = randrange(Self.FieldArea)
            Self._mines.add(position)
        Self.FieldStack = [copy(Self.Field)]
        if Self.Windows :
            Self.Display_Mine_Field(Self.FieldStack[Self.CurrentField])
        Regs = Self.Handler.Sim.Regs
        if 1 in Regs :
            OldValue = Regs[1]
        else :
            OldValue = 'undefined'
        Regs[1] = mines_number
        return {1: (OldValue, Regs[1])}, {}

    # This swi triggers Next/Prev_SWI to update the GUI when it is stepped
    # across in the trace.  Therefore, it pushes the updated state snapshot
    # onto the Stack (i.e., it pushes the updated Field onto FieldStack).
    def SWI_Open_Flag_or_Guess_Square(Self) :
        """ Inputs: Register $2 gives square position XY (as linear index).
                Register $3 gives command: -1: guess, 0: open, 1: flag.
        This updates Field[XY], which is initially U (unopened).
        (If Field[XY] is not U, this is an overwrite, which should be
        recorded and treated as an error, causing student program to fail.)
        If command is flag (1), Field[XY] = F.
        If command is open/guess (0/-1), this looks up whether there is a mine
        at that position:
           If mine, Field[XY] = B.
           Otherwise, Field[XY] = n where n = number of mines nearby.

        Then it calls Classify_Move to update the sets NecessaryGuesses, 
        UnnecessaryGuesses, Opened, and Flagged.  Position will be added
        to exactly one of these sets.

        This swi also checks for failure conditions:
        1) command is open and hit a mine
        2) command is unnecessary guess
        3) square specified has already been opened/flagged/guessed.

        Output: Register $4 gives B/n/F indicator (B:-1, n:0-8, F:9).
        """
        Regs = Self.Handler.Sim.Regs
        if 2 in Regs : Position = Regs[2]
        else : Self.Handler.Sim.Print_Error('Position in $2 undefined.')
        if Position < 0 or Position >= Self.FieldArea:
            Self.Handler.Sim.Print_Error('Position in $2 (%d) is out of range' %
                                         (Position))
        if 3 in Regs: Command = Regs[3]
        else : Self.Handler.Sim.Print_Error('Command in $3 undefined.')
        if Command not in [-1, 0, 1] :
            Self.Handler.Sim.Print_Error('Command in $3 (%d) is unknown' %
                                         (Command))
        Self.Record_Any_Overwrites(Position, Command)
        Necessary = Self.Classify_Move(Position, Command)
        if 4 in Regs :
            OldValue = Regs[4]
        else :
            OldValue = 'undefined'
        Regs[4] = Self.Update_Field(Position, Command)
        if (25 in Regs) and Regs[25] == 2035 :  ##TEMP
            Self.Miner_Easter_Egg()  ### TEMP
        Self.FieldStack.append(copy(Self.Field))
        return {4: (OldValue, Regs[4])}, {}

    def Record_Any_Overwrites(Self, Position, Command) :
        if Self.Overwriting(Position, Command) :
            Self.Handler.Sim.Print_Error('Overwriting position %d.' %
                                         (Position))
            Self.Overwrites.add(Position)

    def Overwriting(Self, Position, Command) :
        """If this Position is not U and either the
        Command is a Guess or
        the Command is open/flag and the square at that position
        has not been opened / flagged already, then return True."""
        if Position in range(0, Self.FieldArea) :
            Sq_Value = Self.Field[Position]
            if ((Sq_Value != 'U') and
                ((Command == -1) or
                 ((Command == 1) and (Position not in Self.Flagged)) or
                 ((Command == 0) and (Position not in Self.Opened)))) :
                return True
            else : return False
        else : return False 

    def Update_Field(Self, Position, Command) :
        """This updates Field[XY], which is initially U (unopened).
        If command is flag (1), Field[XY] = F.
        If command is open/guess (0/-1), this looks up whether there is a mine
        at that position:
           If mine, Field[XY] = B.
           Otherwise, Field[XY] = n where n = number of mines nearby."""
        if Position in range(0, Self.FieldArea) :
            if Command == 1 :
                Self.Field[Position] = 'F'
                return 9  # code for flagged
            elif Position in Self._mines :
                Self.Field[Position] = 'B'
                return -1  # code for mine
            else :
                n = Self.Count_Nearby_Mines(Position)
                Self.Field[Position] = n
                return n  # number of neigboring squares with mines

    def Count_Nearby_Mines(Self, Position) :
        """Look up the 8 neighbors around Position and count how
        many of them are mines."""
        neighboring_mines = set((p)
                                for p in Self.Neighbors(Position)
                                if p in Self._mines)
        return len(neighboring_mines)

    def Neighbors(Self, Position) :
        """Return set of positions that are the neighbors of Position.
           This usually contains 8 elements, except on boundaries."""
        x = Position % Self.FieldWidth
        y = (Position - x) / Self.FieldHeight
        xy_neighbors = set((nx+ny*Self.FieldWidth)
                           # 3x3 area
                           for nx in [x-1, x, x+1]
                           for ny in [y-1, y, y+1]
                           # except the center
                           if (nx, ny) != (x, y)
                           # don't go outside the board
                           if 0 <= nx < Self.FieldWidth
                           if 0 <= ny < Self.FieldHeight)
        return xy_neighbors

    def Classify_Move(Self, Position, Command) :
        """Update the sets Flagged, NecessaryGuesses, UnnecessaryGuesses,
           and Opened. Position will be added to exactly one of these sets.
        If command is flag, add to Flagged set.
        If command is open, add to Opened set.
        If command is a guess, this swi checks whether the guess was
        unnecessary (i.e., there are inferences that can still be made
        w/out resorting to guessing).
        Return False if the Move was an unnecessary guess, o.w., True."""
        if Command == 1 :
            Self.Flagged.add(Position)
            return True
        if Command == 0 :
            Self.Opened.add(Position)
            return True
        elif Command == -1 :
            Necessary = Self.Check_Necessity(Position)
            if Necessary and Position in range(0, Self.FieldArea) :
                Self.NecessaryGuesses.add(Position)
            else :
                if Position in range(0, Self.FieldArea) :
                    Self.UnnecessaryGuesses.add(Position)
                    #print "UG: %d" % (Position)
                    #Self.Display_Text_Mine_Field(Self.Field)
            return Necessary
        else : return True

    def Possible_Moves(Self, Position, Count) :
        """Position is the location of a square that has been
        opened and has a Count btwn 0 and 8.
        Look at the neighbors surrounding Position to determine
        if it is possible to open or flag any of them.  Return
        the set of positions that can be opened and the set that
        can be flagged.  If no inference can be made at this position,
        then no moves are possible (and 2 empty sets are returned)."""
        Neighbor_Locs = Self.Neighbors(Position)
        Can_Open = set()
        Can_Flag = set()
        Neighboring_Mines = set()
        Neighboring_Flags = set()
        Neighboring_Unopened = set()
        for p in Neighbor_Locs :
            Sq_Val = Self.Field[p]
            if Sq_Val == 'B' :
                Neighboring_Mines.add(p)
            elif Sq_Val == 'F' :
                Neighboring_Flags.add(p)
            elif Sq_Val == 'U' :
                Neighboring_Unopened.add(p)
        Rem_Mines = Count - len(Neighboring_Mines) - len(Neighboring_Flags)
        if Rem_Mines == 0 :
            Can_Open = Neighboring_Unopened
        if Rem_Mines == len(Neighboring_Unopened) :
            Can_Flag = Neighboring_Unopened
        return Can_Open, Can_Flag            

    def Check_Necessity(Self, Position) :
        """Check whether there are any existing moves (inferences based
        on one square).  If not, then a guess is necessary and this
        should return True, o.w., False.  To check for existing moves,
        look at all opened squares that have a count btwn 0 and 8.
        Check whether any have a possible move (either to open/flag a
        square)."""
        for p in range(0, Self.FieldArea) :
            Count = Self.Field[p]
            if (Count not in ['U', 'B', 'F']) and (0 <= Count <= 8) :
                Can_Open, Can_Flag = Self.Possible_Moves(p, Count)
                if ((len(Can_Open) > 0) | (len(Can_Flag) > 0)) :
                    #Self.Handler.Sim.Print_Error('Inference can be made at %d; guess at %d is unnecessary.' %
                    #                     (p, Position))
                    return False
        return True

    def Miner_Easter_Egg(Self) :
        """If register $25 has 2035 in it, scan each position,
        looking for Possible Moves. If a position is found
        w/ unopened neighbors that can be opened/flagged,
        then open/flag them. Restart scan until no new squares
        are opened/flagged."""
        if Self.Find_Move() :
            Self.Miner_Easter_Egg()

    def Find_Move(Self) :
        for p in range(0, Self.FieldArea) :
            Count = Self.Field[p]
            if (Count not in ['U', 'B', 'F']) and (0 <= Count <= 8) :
                Can_Open, Can_Flag = Self.Possible_Moves(p, Count)
                if len(Can_Open) > 0 :
                    for Position in Can_Open :
                        #if Position in Self._mines :
                        #    print "Find_Move trying to open mine at %d." % Position
                        Self.Opened.add(Position)
                        Self.Update_Field(Position, 0)
                    return True
                if len(Can_Flag) > 0 :
                    for Position in Can_Flag :
                        Self.Flagged.add(Position)
                        Self.Update_Field(Position, 1)
                    return True
        return False

    def Display_Mine_Field(Self, Field) :
        """Update the Mine Field visualization.
         Display the Field grid.  
         Field[XY] = n, where n is
              U: unopened: light blue w/ no text
              F: flagged:  light blue w/ flag (unicode: BLACK FLAG)
              0: opened, 0 mines nearby: no text
            1-8: opened, n mines nearby: text n.
              B: opened/guessed mine blew up: text is unicode: black sun w/ rays
          How to color 0...8 or B cases:
            Look up XY in Self.NecessaryGuesses, UnnecessaryGuesses, and Opened.
            a) If XY in Self.Opened (opened deliberately)
                  if count: white w/ text n (if n=0, no text)
                  if mine: red with bomb (failure)
            b) If XY in Self.NecessaryGuesses,
                  if count: green w/ text n (if n=0, no text)
                  if mine: green with bomb
            c) If XY in Self.UnnecessaryGuesses, (failure)
                  if count: red w/ text n (if n=0, no text)
                  if mine: red with bomb
          This also shows the actual mines by drawing a thin, dashed black
          rectangle inside each square that holds a mine. """
        Self.Canvas.delete('miner_tags')
        Pad = Self.CellSize/2
        Self.Canvas.create_rectangle(Pad, Pad,
                                     Self.Width-Pad,
                                     Self.Height-Pad,
                                     width=2, tag='miner_tags')
        for Y in range(0, Self.FieldHeight) :
            for X in range(0, Self.FieldWidth) :
                 Xmin = X * Self.CellSize + Pad
                 Ymin = Y * Self.CellSize + Pad
                 Xmax = Xmin + Self.CellSize
                 Ymax = Ymin + Self.CellSize
                 position = Y*Self.FieldWidth + X
                 n = Field[position]
                 Color, Text = Self.Square_Appearance(n, position)
                 Self.Draw_Box(Xmin, Ymin, Xmax, Ymax, Color)
                 if position in Self._mines :
                     Self.Draw_Box(Xmin+3, Ymin+3, Xmax-3, Ymax-3, Color,
                                   width=1, dash=(2,))
                 if ((Color != 'lightblue') and (position in Self.UnnecessaryGuesses)) :
                     Self.Canvas.create_line(Xmin, Ymin, Xmax, Ymax, width=2,
                                             tag='miner_tags')
                 Self.Draw_Text(Xmin+Pad, Ymin+Pad, Text)

    def Draw_Box(Self, Xmin, Ymin, Xmax, Ymax, Color, width=2, dash='') :
        Self.Canvas.create_rectangle(Xmin, Ymin, Xmax, Ymax,
                                         width=width, fill=Color, dash=dash,
                                         tag='miner_tags')

    def Draw_Text(Self, Xmin, Ymin, Text, fill='black') :
        Self.Canvas.create_text(Xmin, Ymin, text=Text,
                                font=('helvetica', '12', 'bold'),
                                fill='black', tag='miner_tags')


    def Square_Appearance(Self, n, position) :
        """Compute appropriate color and text for Square n at position."""
        if n == 'U' : return 'lightblue', ''
        elif n == 'F' : return 'lightblue', u'\N{BLACK FLAG}'
        elif position in Self.Opened :
            Text = Self.Square_Text(n)
            if n == 'B' : return 'red', Text
            elif 0 <= n <= 8 : return 'white', Text
            else : return 'orange', '?'
        elif position in Self.NecessaryGuesses :
            return 'green', Self.Square_Text(n)
        elif position in Self.UnnecessaryGuesses :
            return 'red', Self.Square_Text(n)
        else : return  'orange', '?'

    def Square_Text(Self, n) :
        """Compute text for Square n."""
        if n == 0 : return ''
        elif 0 < n <= 8 : return str(n)
        elif n == 'B' : return u'\N{BLACK SUN WITH RAYS}'
        else : return '?'

    def Test(Self, Field) :
        ##TESTING
        Field[5] = 'F'
        Field[7] = 'B'
        Field[8] = 'B'
        Field[9] = 4
        Field[10] = 5
        Field[11] = 3
        Field[12] = 'B'
        Self.Opened.add(9)
        Self.Opened.add(12)
        Self.NecessaryGuesses.add(7)
        Self.UnnecessaryGuesses.add(8)
        Self.NecessaryGuesses.add(10)
        Self.UnnecessaryGuesses.add(11)

    def Display_Text_Mine_Field(Self, Field) :
        """Stub: print out the Field array -- replace
          with visualization showing color-coded squares."""
        for Y in range(0, Self.FieldHeight) :
            print '%d: %s' % (Y, Field[Y*Self.FieldWidth : (Y+1)*Self.FieldWidth])

    def Checker(Self) :
        """ This routine checks the following:
        1) no Unnecessary Guesses
        2) no Overwrites
        3) # Mines = # Flagged + # NecGuesses that are 'B'
           (Note: this catches whether student pgm opened a mine.)
        4) Each Flagged square is in _mines. (All flags are over mines.)
        If all these are True, a value of True is returned, o.w., False."""
        """
        print "|UG| = %d" % (len(Self.UnnecessaryGuesses))
        print "|Ov| = %d" % (len(Self.Overwrites))
        print Self.Overwrites
        print '|F| = %d = |mines| - |B in NG| = %d - %d.' % \
            (len(Self.Flagged),
             len(Self._mines), 
             (len(set((x) for x in Self.NecessaryGuesses
                      if Self.Field[x] == 'B'))))
        print "Flagged: %s" % (Self.Flagged)
        """
        if ((len(Self.UnnecessaryGuesses) == 0) and
            (len(Self.Overwrites) == 0) and
            (len(Self._mines) ==
             (len(Self.Flagged)) +
             (len(set((x) for x in Self.NecessaryGuesses
                  if Self.Field[x] == 'B')))) and
            (Self.Flagged.issubset(Self._mines))) :
            return True
        else :
            """print "|UG| = %d" % (len(Self.UnnecessaryGuesses))
            print "|Ov| = %d" % (len(Self.Overwrites))
            print Self.Overwrites
            print '|F| = %d = |mines| - |B in NG| = %d - %d.' % \
                (len(Self.Flagged),
                 len(Self._mines), 
                 (len(set((x) for x in Self.NecessaryGuesses
                          if Self.Field[x] == 'B'))))
            print "Flagged: %s" % (Self.Flagged)"""
            return False

# Number Sorting

class P018 :
    def __init__(Self, Handler, Windows=True, Mode=1) :
        Self.Handler = Handler
        Self.Windows = Windows
        Self.Mode = Mode
        Self.Array = []
        # Self.Base = False

    def Next_SWI(Self, Interrupt) :
        return None

    def Prev_SWI(Self, Interrupt) :
        return None

    def SWI_Random(Self) :
        """ This routine creates 100 random numbers and stores in an array specified
        by the base address in $1. """
        Self.Array = []
        Mem = Self.Handler.Sim.Mem
        MemMods = {}
        Self.Base = Pointer_Check(1, Self.Handler.Sim)
        if Self.Base :
            for I in range(100) :
                Value = randint(-999, 999)
                Self.Array.append(Value)
                Address = I * 4 + Self.Base
                if Address in Mem :
                    OldValue = Mem[Address]
                else :
                    OldValue = 'undefined'
                Mem[Address] = Value
                MemMods[Address] = (OldValue, Value)
        return {}, MemMods

    def SWI_Random_Duplicates(Self) :
        """ This routine creates an array of 100 random numbers (between 1 and
        1000), many of which are duplicates,
        and stores them in an array specified by the base address in $1.
        It also keeps track of the most frequently occurring number in ModeValue
        and its frequency in MaxFreq.  If there are two numbers with the same
        frequency, the larger one is the ModeValue."""
        Self.Array = []
        Self.ModeValue = 0
        Self.MaxFreq = 0
        Self.UserMode = -1
        Mem = Self.Handler.Sim.Mem
        MemMods = {}
        Self.Base = Pointer_Check(1, Self.Handler.Sim)
        FreqRange = randrange(1, 11, 3)  # 1 or 4 or 7 or 10
        if Self.Base :
            Index = 0
            while Index < 100 :
                Freq = randint(1, min(100-Index, FreqRange))
                Value = randint(1, 1000)
                if Value not in Self.Array :
                    for I in range(Freq) :
                        Self.Array.append(Value)
                    Index += Freq
                    if Self.MaxFreq == Freq :
                        Self.ModeValue = max(Value, Self.ModeValue)
                    elif Self.MaxFreq < Freq :
                        Self.ModeValue = Value
                        Self.MaxFreq = Freq
            shuffle(Self.Array)
            for I in range(100) :
                Value = Self.Array[I]              
                Address = I * 4 + Self.Base
                if Address in Mem :
                    OldValue = Mem[Address]
                else :
                    OldValue = 'undefined'
                Mem[Address] = Value
                MemMods[Address] = (OldValue, Value)
            # TEMP
            #EggAddr = 400 + Self.Base
            #if EggAddr in Mem:
            #    OldValue = Mem[EggAddr]
            #else :
            #    OldValue = 'undefined'
            #Mem[EggAddr] = Self.ModeValue
            #MemMods[EggAddr] = (OldValue, Self.ModeValue)
            # TEMP
        return {}, MemMods

    def SWI_ModeValue(Self) :
        """ This routine receives the mode in $2. It also
        returns the correct answer in $3. """
        Regs = Self.Handler.Sim.Regs
        if 2 in Regs :
            if Self.UserMode == -1 :  
                Self.UserMode = Regs[2]
        else :
            Self.Handler.Sim.Print_Error('Mode result in $2 undefined')
        if 3 in Regs :
            OldValue = Regs[3]
        else :
            OldValue = 'undefined'
        Regs[3] = Self.ModeValue
        return {3: (OldValue, Self.ModeValue)}, {}
    
    def Checker(Self) :
        """ This routine (in Mode 1) evaluates whether the 100 integers beginning at
        the specified base address match the sorted list generated initially. In
        mode 2, it checks for the median in register 2.  In mode 3, it checks whether
        the mode is in register 2."""
        Mem = Self.Handler.Sim.Mem
        Regs = Self.Handler.Sim.Regs
        if not Self.Base :
            return False
        if Self.Mode == 1 :
            Self.Array.sort()
            Address = Self.Base
            for RefValue in Self.Array :
                Value = Mem[Address]
                if Value <> RefValue :
                    return False
                Address += 4
            return True
        elif Self.Mode == 2 :
            Self.Array.sort()
            Median = int((Self.Array[49] + Self.Array[50]) / 2)
            if 2 in Regs and Regs[2] == Median :
                return True
            else :
                return False
        elif Self.Mode == 3 :
            if 2 in Regs and Regs[2] == Self.ModeValue :
                return True
            else :
                return False

# Interrupt List

Interrupts = {542: (P018, 'SWI_Random'),
              554: (P018, 'SWI_Random_Duplicates'),
              555: (P018, 'SWI_ModeValue'),
              567: (P027, 'SWI_Bury_Mines'),
              568: (P027, 'SWI_Open_Flag_or_Guess_Square')}

class Interrupt_Handler :
    def __init__(Self, Sim) :
        Self.Sim = Sim
        Self.Classes = {}
        Self.Handlers = {}

    def Known_Interrupt(Self, Interrupt) :
        """ This routine determines whether the handler code is known. If it is
        not defined, False is returned. It it is defined, but not installed, a
        class is instantiated and cached, and the the bound method is installed
        in the interrupt handler. """
        if Interrupt in Self.Handlers :
            return True
        elif not Interrupt in Interrupts :
            return False
        else :
            Class = Interrupts[Interrupt][0]
            if not Class in Self.Classes :
                Self.Classes[Class] = Class(Self)
            Instance = Self.Classes[Class]
            Handler = Interrupts[Interrupt][1]
            Self.Handlers[Interrupt] = eval('Instance.%s' % Handler)
            return True

    def Call(Self, Interrupt) :
        """ This routine calls a interrupt handler. The handler returns a
        pair of dictionaries summarizing register and memory mods. Each mod
        includes old and new value pairs. """
        return Self.Handlers[Interrupt]()

    def Next_SWI(Self, Interrupt) :
        """ This routine performs display state changes when the next SWI
        is executed. """
        Class = Interrupts[Interrupt][0]
        if not Class in Self.Classes :
            Self.Classes[Class] = Class(Self)
        Instance = Self.Classes[Class]
        Instance.Next_SWI(Interrupt)

    def Prev_SWI(Self, Interrupt) :
        """ This routine performs display state changes when the prev SWI
        is executed. """
        Class = Interrupts[Interrupt][0]
        if not Class in Self.Classes :
            Self.Classes[Class] = Class(Self)
        Instance = Self.Classes[Class]
        Instance.Prev_SWI(Interrupt)

# support functions

def Pointer_Check(RegNum, Sim) :
    """ This function checks the specified register number to see if it (a) is defined
    in the register file, and (b) contains a pointer in the data space of memory (i.e.,
    between the start of static space and the starting stack pointer. If the pointer is
    properly positioned, it is returned; otherwise None is returned. """
    if RegNum in Sim.Regs and Sim.DataBase <= Sim.Regs[RegNum] < Sim.StartingSP :
        return Sim.Regs[RegNum]
    else :
        Sim.Print_Error('Invalid pointer specified in $%d' % (RegNum))
        return None

def Scramble(List) :
    """ This routine creates a new list that has the same elements of the input
    list, but in random (scrambled) order. """
    from random import randint
    OldList = List[:]
    NewList = []
    Length = len(OldList)
    while Length > 0 :
        I = randint(0, Length - 1)
        if I == (Length - 1) :
            NewList.append(OldList.pop())
        else :
            NewList.append(OldList[I])
            OldList[I:I+1] = []
        Length -= 1
    return NewList

def LengthCompare(ListA, ListB) :
    """ This routine compares two lists based on their lengths. """
    return cmp(len(ListA), len(ListB))
