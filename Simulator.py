# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

from Analyzer import *
from Support import *
from os import listdir
from random import seed
from Opcodes import *
from Instructions import *
from Core import *
from ExecArbitrator import *
from Logging import *

class Simulation :
    def __init__(Self, Parent=None) :
        Self.Parent = Parent
        Self.Instructions = []
        Self.DataLabels = []  # cached for the benefit of the control flow analyzer
        Self.CodeBase = 1000
        Self.DataBase = Self.DataEnd = 5000 + (randint(0,250) * 4)
        Self.StackBase = 90000
        Self.StartingSP = 100000
        Self.ReturnIP = 3000 + (randint(0,250) * 4)
        Self.InitialMem = {}
        Self.Handler = Interrupt_Handler(Self)
        Self.Restart()
        Self.Silent = False
        Self.ErrorFile = None
        Self.Cores = []
        for CoreID in range(Parent.NumCores):
            Self.Cores.append(Core(CoreID, Self))
        Self.Arbitrator = DefaultArbitrator()

    def Restart(Self) :
        """ This routine restores the simulation to the pre-execution state. """
        Self.Trace = []
        for Core in Self.Cores:
            Core.Restart()
        Self.Nav = Navigator(Self)
        Self.Mem = Self.InitialMem.copy()
        Self.WECount = 0

    def Goto_Start_of_Trace(Self) :
        """ This routine sets processor state and the navigator to the begining
        of the trace. """
        for Core in Self.Cores:
            Core.Restart()
        Self.Nav.Initialize()
        Self.Mem = Self.InitialMem.copy()

    def Stack_Address(Self, Address) :
        """ Returns True if StackBase <= Address <= StartingSP, otherwise returns False."""
        return Self.StackBase <= Address <= Self.StartingSP

    def Simulate(Self, ExeLimit=10000, WELimit=25) :
        """ This routine executes a program """
        if not Self.Instructions :
            Self.Print_Error('No instructions found')
        else :
            Max_Inst_Address = Self.Instructions[-1].Address
            while ExeLimit > 0 and Self.WECount < WELimit and Self.CodeBase <= Self.IP <= Max_Inst_Address:
                I = Self.Lookup_Instruction(Self.IP)
                if I :
                    Result, OldValue = I.Exec()
                    I.Adjust_IP()
                    I.Log_In_Trace(Result, OldValue)
                    ExeLimit -= 1
                else :
                    Self.Print_Error('Attempt to execute an invalid IP %s' % (Self.IP))
                    break
            if ExeLimit <= 0 :
                Self.Print_Warning('Stopped after %i instructions.  Infinite Loop?' % (len(Self.Trace)))
            elif Self.WECount >= WELimit :
                Self.Print_Warning('Stopped after %i instructions.  Too many warnings and errors' % (len(Self.Trace)))
            elif I.Opcode <> 'jr' :
                Self.Print_Warning('Last executed instruction is %s rather than jr' % (I.Opcode))
            elif not I.Src1 in Self.Regs or Self.Regs[I.Src1] <> Self.ReturnIP :
                Self.Print_Warning('return address not preserved (%d versus %d)' % (Self.Regs[I.Src1], Self.ReturnIP))
            elif Self.Regs[29] <> Self.StartingSP :
                Self.Print_Warning('stack not maintained during execution (%d versus %d)' % (Self.Regs[29], Self.StartingSP))
        return Self.WECount

    def Print_Exe_Stats(Self, Data=None) :
        """ This routine prints execution statistics. """
        if Data :
            StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData = Data
        else :
            StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData = Self.Compute_Exe_Stats()
        Self.Print_Message('static I= %d, dynamic I= %d, reg data= %d, static data= %d, stack data= %d' %
                           (StaticI, DynamicI, RegData, StaticData, StackData))
        Results = ''
        SumCount = 0
        for Value in DynamicMix.values() :
            SumCount += Value
        for  Class, Count in DynamicMix.items() :
            Results += '%s: %2.1f%% ' % (Class, Count * 100.0 /SumCount)
        Self.Print_Message(Results)

    def Compute_Exe_Stats(Self) :
        """ This routine computes the static code length, dynamic code length, dynamic instruction
        mix, static memory used and stack memory used. """
        StaticI = len(Self.Instructions)
        DynamicI = len(Self.Trace)
        DynamicMix = {}
        for Instruction, Result, OldValue in Self.Trace :
            Op = Instruction.Opcode
            for Class, Opcodes in Opcode_Classes.items() :
                if Op in Opcodes :
                    if Class in DynamicMix :
                        DynamicMix[Class] += 1
                    else :
                        DynamicMix[Class] = 1
        SP = Self.StartingSP - 4
        while SP in Self.Mem :
            SP -= 4
        StackData = ((Self.StartingSP - 4) - SP) / 4
        StaticData = len(Self.Mem) - StackData
        RegData = len(Self.Regs) - 3
        if 'HiLo' in Self.Regs :
            RegData -= 1
        return [StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData]

    def Print_Message(Self, String) :
        """ This routine prints a message to the console. If a parent is defined,
        the print is redirected there. """
        if not Self.Silent and not Self.ErrorFile :
            if Self.Parent :
                Self.Parent.Print_Message(String)
            else :
                print "%s\n" % String

    def Print_Warning(Self, String) :
        """ This routine prints a warning to the log file, parent lister, or console.
        It also increments the warning error count. """
        Self.WECount += 1
        if not Self.Silent :
            if Self.ErrorFile :
                if type(Self.ErrorFile) == StringType :
                    Self.ErrorFile = open(Self.ErrorFile, 'w')
                Self.ErrorFile.write("Warning: %s\n" % String)
            elif Self.Parent :
                Self.Parent.Print_Warning(String)
            else :
                print "Warning: %s\n" % String

    def Print_Error(Self, String) :
        """ This routine prints an error to the log file, parent lister, or console.
        It also increments the warning error count. """
        Self.WECount += 1
        if not Self.Silent :
            if Self.ErrorFile :
                if type(Self.ErrorFile) == StringType :
                    Self.ErrorFile = open(Self.ErrorFile, 'w')
                Self.ErrorFile.write("Error: %s\n" % String)
            elif Self.Parent :
                Self.Parent.Print_Error(String)
            else :
                print "Error: %s\n" % String

    def Lookup_Instruction_Position(Self, Address) :
        """ This routine looks up an instruction position using an address. First an index
        is computing into the instruction list. If the instruction does not match, all
        instructions are searched. """
        Position = (Address - Self.CodeBase) / 4
        if Position >= 0 and Position < len(Self.Instructions) :
            if Self.Instructions[Position].Address == Address :
                return Position
            for Position in range(len(Self.Instructions)) :
                I = Self.Instructions[Position]
                if I.Address == Address :
                    return Position
        Self.Print_Error('%s is an invalid instruction address' % Address)
        return ''

    def Lookup_Instruction(Self, Address) :
        """ This routine looks up an instruction using an address. """
        Position = Self.Lookup_Instruction_Position(Address)
        if not Position == '':
            return Self.Instructions[Position]
        else :
            return None

    def Print_Regs(Self) :
        """ This routine prints all defined registers in the register file. """
        if 'HiLo' in Self.Regs :
            Self.Print_Message('HiLo = %i : %i' % Self.Regs['HiLo'])
        for RegNum in range(32) :
            if RegNum in Self.Regs :
                Self.Print_Message('$%02i = %8i' % (RegNum, Self.Regs[RegNum]))

    def Print_Instructions(Self) :
        """ This routine pretty prints a list of instructions. """
        for I in Self.Instructions :
            Self.Print_Message(I.Print())

class Navigator :
    def __init__(Self, Sim, Analysis = None) :
        Self.Trace_Index = 0
        Self.Sim = Sim
        Self.Lexical_Address = Sim.CodeBase
        Self.Analysis = Analysis
        # Navigator also may have Current_BB and Current_Loop attributes if there is an Analysis
        Self.Assign_BB_Loop(Sim.CodeBase, Analysis)

    def __repr__(Self) :
        return '[Nav %i Address: %i]' % (Self.Trace_Index, Self.Lexical_Address)

    def Initialize(Self) :
        """ This resets the lexical address and trace index to the starting state.
        It is used when we already have a trace and possibly an Analysis that we
        don't want to lose."""
        Self.Trace_Index = 0
        Self.Lexical_Address = Self.Sim.CodeBase
        Self.Assign_BB_Loop(Self.Sim.CodeBase)

    def Map_to_Analysis(Self, Analysis) :
        """ This can be used after a CFA has been performed to map an existing
        Navigator state to the BB and Loop (if any) in which Lexical_Address
        occurs. """
        Self. Analysis = Analysis
        Self.Assign_BB_Loop(Self.Lexical_Address, Analysis)

    def Assign_BB_Loop(Self, Address, Analysis = None) :
        """ Assign Current_BB and Current_Loop attributes of navigator to be those containing
        the instruction with Address."""
        if Analysis :
            New_BB = Analysis.Find_BB_w_Inst(Address)
            if New_BB :
                Self.Current_BB = New_BB
                Self.Current_Loop = New_BB.Loop
            elif Analysis :
                Self.Sim.Print_Error('Cannot find Basic Block containing instruction address %i.' \
                                     % Address)
            # else: do nothing (no CFA has been performed)

    def Next_Inst(Self, Trace) :
        """Move to the next instruction in the trace.  If at the end of trace,
        do nothing. """
        if len(Trace)-1 <> Self.Trace_Index :
            New_Trace_Index = Self.Trace_Index + 1
            return Self.Move_to_Instruction(New_Trace_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Prev_Inst(Self, Trace) :
        """Move to the previous instruction in the trace.  If at the start of trace,
        do nothing. """
        if not Self.Trace_Index == 0 :
            New_Trace_Index = Self.Trace_Index - 1
            return Self.Move_to_Instruction(New_Trace_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Top(Self, Trace) :
        """ Move to the first instruction in the trace. """
        if not Self.Trace_Index == 0 :
            return Self.Move_to_Instruction(0, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Bottom(Self, Trace) :
        """ Move to the last instruction in the trace. """
        Last_Trace_Index = len(Trace) - 1
        if not Self.Trace_Index == Last_Trace_Index :
            return Self.Move_to_Instruction(Last_Trace_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
        
    def Move_to_Instruction(Self, New_Trace_Index, Trace) :
        """ Update the current trace and lexical indices.  If New_I_Address is still within
        the same Current_BB, then don't change Current BB or Current Loop.  Otherwise,
        find out which BB it is in and whether it is in a loop.
        Update the register file and memory to reflect the movement within the trace.
        Return:
            + the new IP,
            + new trace index,
            + dictionary of changes to registers,
            + dictionary of changes to data memory (static and heap), and
            + dictionary of changes to stack.
        Reg_Changes dictionary: indexed by reg number; data is a pair consisting of
            the last value assigned to that register and whether the register was newly
            allocated/deallocated during the move w/in the trace.
        Mem_Changes dictionary: indexed by effective addresses of stores that occur
            during the move w/in the trace and each item in the dictionary
            contains the last value stored to that location and whether the location is
            newly allocated/deallocated.
        Stack_Changes dictionary: indexed by effective addresses of stack stores; data
            is of the same type as in Mem_Changes.
        This is the core function that all the other move instructions call. """
        New_Lexical_Address = Trace[New_Trace_Index][0].Address 
        Old_Trace_Index = Self.Trace_Index
        Reg_Changes, Mem_Changes = \
                     Self.Update_Storage(Old_Trace_Index, New_Trace_Index, Trace)
        Mem_Changes, Stack_Changes = Self.Classify_Mem_Changes(Mem_Changes)
        Self.Trace_Index = New_Trace_Index
        Self.Lexical_Address = New_Lexical_Address
        Self.Sim.IP = New_Lexical_Address
        if Self.Analysis :
            if (not Self.Current_BB) or (not Self.Current_BB.Member_Instruction(New_Lexical_Address)) :
                Self.Assign_BB_Loop(New_Lexical_Address, Self.Analysis)
            # else: New_I is in the Current_BB already, so no need to change Current_BB/Loop
        # else: no need to update BB info since no CFA was performed.
        return (New_Lexical_Address, New_Trace_Index, Reg_Changes, Mem_Changes, Stack_Changes)

    def Update_Storage(Self, Old_Trace_Index, New_Trace_Index, Trace) :
        Reg_Changes = {}
        Mem_Changes = {}
        if Old_Trace_Index > New_Trace_Index :
            Direction = -1
        else : Direction = 1
        while not Old_Trace_Index == New_Trace_Index :
            if Direction == 1 :
                New_Inst, New_Value, Old_Value = Trace[Old_Trace_Index]
            else :
                New_Inst, New_Value, Old_Value = Trace[Old_Trace_Index-1]
            Opcode = New_Inst.Opcode
            if New_Value <> None :      # New_Value is None for jumps, branches
                if Opcode in ('sw', 'sb') :
                    Mem_Changes = Self.Update_Mem(New_Inst, New_Value, Old_Value, \
                                                  Direction, Mem_Changes)
                elif Opcode == 'swi' :      # software interrupt (Old/New_Values = dictionaries)
                    # Old_Value is actually a dictionary of Memory changes, indexed by mem addr
                    # New_Value is actually a dictionary of Register changes, indexed by reg number
                    # Each dictionary entry has a tuple value (Old, New).
                    Reg_Changes = Self.Update_swi_Regs(New_Inst, New_Value, Direction, Reg_Changes)
                    Mem_Changes = Self.Update_swi_Mem(New_Inst, Old_Value, Direction, Mem_Changes)
                    if Direction == 1 :
                        New_Inst.Sim.Handler.Next_SWI(New_Inst.Src1)
                    else :
                        New_Inst.Sim.Handler.Prev_SWI(New_Inst.Src1)
                else :
                    Reg_Changes = Self.Update_Reg(New_Inst, New_Value, Old_Value, \
                                                  Direction, Reg_Changes)
            Old_Trace_Index = Old_Trace_Index + Direction
        return (Reg_Changes, Mem_Changes)

    def Update_swi_Regs(Self, New_Inst, Reg_Change_Dictionary, Direction, Reg_Changes) :
        """Reg_Change_Dictionary is a dictionary of Register changes, indexed by
        register number; each dictionary entry has a tuple value (Old, New).
        Loop through each entry and call Update_Reg."""
        for Change_Entry in Reg_Change_Dictionary.items() :
            Reg_Num = Change_Entry[0]
            Old_Value, New_Value = Change_Entry[1]
            Reg_Changes = Self.Update_Reg(New_Inst, New_Value, Old_Value, Direction, \
                                          Reg_Changes, Reg_Num)
        return Reg_Changes
    
    def Update_Reg(Self, New_Inst, New_Value, Old_Value, Direction, Reg_Changes, Reg_Num=None) :
        """ Reg_Num will be provided by updates due to software interrupts.  If none
        is provided, the Reg_Num is determined from the instruction."""
        Opcode = New_Inst.Opcode
        if not Reg_Num :
            if Opcode in ['mult', 'multu', 'div', 'divu'] :
                Reg_Num = 'HiLo'
            elif Opcode == 'jal' :
                Reg_Num = 31
            elif New_Inst.Has_Dest() :
                Reg_Num = New_Inst.Dest
            else :
                Self.Sim.Print_Error('Instruction %s gets new value, but has no Dest.' \
                                      % New_Inst)
                return Reg_Changes
        Allocation_Mod = (Reg_Changes.has_key(Reg_Num) and Reg_Changes[Reg_Num][1]) \
                         or (Old_Value == 'undefined')
        if Direction == 1 :  # forward
            New_Inst.Write_Reg(Reg_Num, New_Value)
            Reg_Changes[Reg_Num] = (New_Value, Allocation_Mod)
        else :  # reverse
            New_Inst.Unwrite_Reg(Reg_Num, Old_Value)
            Reg_Changes[Reg_Num] = (Old_Value, Allocation_Mod)
        return Reg_Changes

    def Update_swi_Mem(Self, New_Inst, Mem_Change_Dictionary, Direction, Mem_Changes) :
        """Mem_Change_Dictionary is a dictionary of Memory changes, indexed by
        memory address; each dictionary entry has a tuple value (Old, New).
        Loop through each entry and call Update_Mem."""
        for Change_Entry in Mem_Change_Dictionary.items() :
            Mem_Address = Change_Entry[0]
            Old_Value, New_Value = Change_Entry[1]
            Mem_Changes = Self.Update_Mem(New_Inst, New_Value, Old_Value, Direction, \
                                          Mem_Changes, Mem_Address)
        return Mem_Changes
        
    def Update_Mem(Self, New_Inst, New_Value, Old_Value, Direction, Mem_Changes, \
                   Address=None) :
        """ Address will be provided by updates due to software interrupts.  If none
        is provided, the Address is computed from the instruction."""
        if not Address :
            Address = New_Inst.Read_Reg(New_Inst.Reg) + New_Inst.Offset
            Address &= -4       # make word address
        Allocation_Mod = (Mem_Changes.has_key(Address) and Mem_Changes[Address][1]) \
                         or (Old_Value == 'undefined')
        if Direction == 1 :     # forward
            New_Inst.Write_Mem(Address, New_Value)
            Mem_Changes[Address] = (New_Value, Allocation_Mod)
        else :  # reverse
            New_Inst.Unwrite_Mem(Address, Old_Value)
            Mem_Changes[Address] = (Old_Value, Allocation_Mod)
        return Mem_Changes

    def Classify_Mem_Changes(Self, Mem_Changes) :
        """ Separate out stack-based memory changes from data memory changes.
        Return two dictionaries: Mem_Changes (original dictionary with data memory
        changes only) and Stack_Changes (entries involving stack addresses)."""
        Stack_Changes = {}
        for Address in Mem_Changes.keys() :
            if Self.Sim.Stack_Address(Address) :
                Stack_Changes[Address] = Mem_Changes[Address]
                del Mem_Changes[Address]
        return Mem_Changes, Stack_Changes        

    def Move_to_Top_of_BB(Self, Trace) :
        """ Move to the top of the current basic block."""
        if Self.Analysis :
            if Self.Current_BB :
                Top_Address = Self.Current_BB.Addr
                if not Self.Lexical_Address == Top_Address :
                    New_Trace_Index = Self.Find_Inst(Top_Address, Trace, -1)
                    if New_Trace_Index :
                        return Self.Move_to_Instruction(New_Trace_Index, Trace)
#               else : currently at the Top
            else :
                Self.Sim.Print_Error('No current basic block is selected.')
        else :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
            
    def Move_to_Bottom_of_BB(Self, Trace) :
        """ Move to the bottom of the current basic block.  If currently at
        the bottom of block, do nothing."""
        if Self.Analysis :
            if Self.Current_BB :
                Bottom_Address = Self.Current_BB.Ending_Addr
                if not Self.Lexical_Address == Bottom_Address :
                    New_Trace_Index = Self.Find_Inst(Bottom_Address, Trace, 1)
                    if New_Trace_Index :
                        return Self.Move_to_Instruction(New_Trace_Index, Trace)
#               else : currently at the bottom of BB
            else :
                Self.Sim.Print_Error('No current basic block is selected.')
        else :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Top_of_Loop(Self, Trace) :
        """ Move to the top of the current loop.  If not currently in a loop
        or if already at the top, do nothing."""
        if not Self.Analysis :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        elif Self.Current_Loop :
            Top_Address = Self.Current_Loop.Starting_Address
            New_Trace_Index = Self.Find_Inst(Top_Address, Trace, -1)
            if New_Trace_Index :
                return Self.Move_to_Instruction(New_Trace_Index, Trace)
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Bottom_of_Loop(Self, Trace) :
        """ Move to the bottom of the current loop.  If not currently in a loop,
        or if already at the bottom, do nothing."""
        if not Self.Analysis :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        elif Self.Current_Loop :
            Bottom_Address = Self.Current_Loop.Back_Address
            New_Trace_Index = Self.Find_Inst(Bottom_Address, Trace, 1)
            if New_Trace_Index :
                return Self.Move_to_Instruction(New_Trace_Index, Trace)
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
            
    def Move_to_Next_BB(Self, Trace) :
        """ Move to the bottom of the current basic block and then move to the
        next instruction after. If there are no instructions/basic blocks after
        the current basic block, stay at the end of the current basic block."""
        ### Return values not propagated correctly
        if Self.Analysis :
            Self.Move_to_Bottom_of_BB(Trace)
            Self.Next_Inst(Trace)
        else :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Prev_BB(Self, Trace) :
        """ Move to the top of the current basic block and then move to the
        instruction before. If there are no instructions/basic blocks before
        the current basic block, stay at the top of the current basic block."""
         ### Return values not propagated correctly
        if Self.Analysis :
            Self.Move_to_Top_of_BB(Trace)
            Self.Prev_Inst(Trace)
        else :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Next_Occurrence(Self, Trace) :
        """ Move to the next instance of the current lexical instruction in
        the trace.  If there are no more instances, do nothing. """
        Next_Instance_Index = Self.Find_Inst(Self.Lexical_Address, Trace, 1)
        if Next_Instance_Index :
            return Self.Move_to_Instruction(Next_Instance_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Prev_Occurrence(Self, Trace) :
        """ Move to the previous instance of the current lexical instruction in
        the trace.  If there are no earlier instances, do nothing. """
        Prev_Instance_Index = Self.Find_Inst(Self.Lexical_Address, Trace, -1)
        if Prev_Instance_Index :
            return Self.Move_to_Instruction(Prev_Instance_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Address(Self, Trace, Inst_Address) :
        """ Move to the next occurance in the trace of the specified instruction
        address. If there are no later instances, do nothing. """
        if Inst_Address > Self.Sim.IP :
            Addr_Trace_Index = Self.Find_Inst(Inst_Address, Trace, 1)
        else :
            Addr_Trace_Index = Self.Find_Inst(Inst_Address, Trace, -1)
        if Addr_Trace_Index :
            return Self.Move_to_Instruction(Addr_Trace_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Producer_of_Src1(Self, Trace, Register=None) :
        """ Move to the Instruction that most recently wrote Register or to the
        current instruction's source1 operand if Register is not provided. """
        if not Register :
            Inst = Trace[Self.Trace_Index][0]
            if Inst.Has_Src1() :
                Register = Inst.Src1
            else :
                Self.Sim.Print_Warning('%s has no source 1 operand.' % Inst)
                return ''
        New_Index = Self.Find_Inst_w_Dest(Register, Trace, -1)
        if New_Index :
            return Self.Move_to_Instruction(New_Index, Trace)
        else :
            Self.Sim.Print_Warning('No producer of register %i found.' % Register)
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Producer_of_Src2(Self, Trace, Register=None) :
        """ Move to the Instruction that most recently wrote Register or to the
        current instruction's source2 operand if Register is not provided. """
        if not Register :
            Inst = Trace[Self.Trace_Index][0]
            if Inst.Has_Src2() :
                Register = Inst.Src2
            else :
                Self.Sim.Print_Warning('%s has no source 2 operand.' % Inst)
                return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
        New_Index = Self.Find_Inst_w_Dest(Register, Trace, -1)
        if New_Index :
            return Self.Move_to_Instruction(New_Index, Trace)
        else :
            Self.Sim.Print_Warning('No producer of register %i found.' % Register)
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
            
    def Move_to_Next_Writer_of_Dest(Self, Trace, Register=None) :
        """ Move to the next instruction that writes to Register or the current
        instruction's destination operand if Register is not provided."""
        if not Register :
            Inst = Trace[Self.Trace_Index][0]
            if Inst.Has_Dest() :
                Register = Inst.Dest
            else :
                Self.Sim.Print_Warning('%s has no destination operand.' % Inst)
                return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
        New_Index = Self.Find_Inst_w_Dest(Register, Trace, 1)
        if New_Index :
            return Self.Move_to_Instruction(New_Index, Trace)
        else :
            Self.Sim.Print_Warning('No subsequent writer of register %i found.' % Register)
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Consumer_of_Dest(Self, Trace, Register=None) :
        """ Move to the next instruction that uses Register or the current
        instruction's destination operand if Register is not provided."""
        if not Register :
            Inst = Trace[Self.Trace_Index][0]
            if Inst.Has_Dest() :
                Register = Inst.Dest
            else :
                Self.Sim.Print_Warning('%s has no destination operand.' % Inst)
                return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
        New_Index = Self.Find_Inst_w_Src(Register, Trace, 1)
        if New_Index :
            return Self.Move_to_Instruction(New_Index, Trace)
        else :
            Self.Sim.Print_Warning('No consumer of register %i found.' % Register)
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Next_Control_Transfer(Self, Trace) :
        """ Move to the next place in Trace where a jump or branch occurred,
        determined solely by a discontinuity in instruction addresses (a difference
        other than 4)."""
        Control_Transfer_Index = Self.Find_Control_Transfer(Trace, 1)
        if Control_Transfer_Index :
            return Self.Move_to_Instruction(Control_Transfer_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
            
    def Move_to_Prev_Control_Transfer(Self, Trace) :
        """ Move to the next place in Trace where a jump or branch occurred,
        determined solely by a discontinuity in instruction addresses (a difference
        other than 4)."""
        Control_Transfer_Index = Self.Find_Control_Transfer(Trace, -1)
        if Control_Transfer_Index :
            return Self.Move_to_Instruction(Control_Transfer_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
        
    def Find_Control_Transfer(Self, Trace, Direction) :
        """ Find the trace index of the next place where a jump or branch occurred,
        looking either up (Direction = 1) or down (Direction = -1). Return the trace index
        or None if the Inst_Address is not found.  The transfer of control should b
        determined solely by a discontinuity in instruction addresses (a difference
        other than 4)."""
        Trace_Length = len(Trace)
        Current_Trace_Index = Self.Trace_Index
        New_Trace_Index = Current_Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) and \
              (0 <= Current_Trace_Index) and (Current_Trace_Index < Trace_Length) :
            Current_Address = Trace[Current_Trace_Index][0].Address
            Next_Address = Trace[New_Trace_Index][0].Address
            Difference = Current_Address - Next_Address
            if abs(Difference) == 4 :
                New_Trace_Index = New_Trace_Index + Direction
                Current_Trace_Index = Current_Trace_Index + Direction
            else :
                return New_Trace_Index 
        return None
        
    def Find_Inst(Self, Inst_Address, Trace, Direction) :
        """ Find the trace index of the next place Inst_Address occurs in Trace,
        looking either up (Direction = 1) or down (Direction = -1). Return the trace index
        or None if the Inst_Address is not found.
        """
        Trace_Length = len(Trace)
        New_Trace_Index = Self.Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) :
            if (Inst_Address == Trace[New_Trace_Index][0].Address) :
                return New_Trace_Index
            else :
                New_Trace_Index = New_Trace_Index + Direction
        return None

    def Find_Inst_w_Dest(Self, Dest_Reg, Trace, Direction) :
        """ Find the trace index of the next place an instruction with
        destination register Dest occurs in Trace,
        looking either up (Direction = 1) or down (Direction = -1). Return
        the trace index or None if no such instruction is found.
        """
        Trace_Length = len(Trace)
        New_Trace_Index = Self.Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) :
            Inst = Trace[New_Trace_Index][0]
            if Inst.Has_Dest() :
                Dest = Inst.Dest
                if (Dest_Reg == Dest) :
                    return New_Trace_Index
            New_Trace_Index = New_Trace_Index + Direction
        return None

    def Find_Inst_w_Src(Self, Src, Trace, Direction) :
        """ Find the trace index of the next place an instruction occurs
        in Trace with Src register as one of its source operands ,
        looking either up (Direction = 1) or down (Direction = -1). Return
        the trace index or None if no such instruction is found.
        """ 
        Trace_Length = len(Trace)
        New_Trace_Index = Self.Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) :
            Inst = Trace[New_Trace_Index][0]
            if Inst.Has_Src1() :
                Src1 = Inst.Src1
                if (Src == Src1) :
                    return New_Trace_Index
            if Inst.Has_Src2() :
                Src2 = Inst.Src2
                if (Src == Src2) :
                    return New_Trace_Index
            New_Trace_Index = New_Trace_Index + Direction
        return None

def Main (FileName='fact') :
    Sim = Simulation()
    InputFile = open('U:/scotty/classes/ece3035/Common Class Material/asm/%s.asm' % FileName, 'r')
    #Sim.Parse_Program(InputFile)
    Sim.Simulate()
    Sim.Print_Instructions()
    return Sim

def Program_Overlap (FileName='fact') :
    Sim = Simulation()
    InputFile = open('U:/scotty/classes/ece3035/Common Class Material/asm/%s.asm' % FileName, 'r')
    #Sim.Parse_Program(InputFile)
    for (i,j) in zip(Sim.Instructions, Sim.Instructions) :
        print i.Opcode
        print j.Opcode
        print i.Opcode == j.Opcode
    InputFile.close()
    return Sim

