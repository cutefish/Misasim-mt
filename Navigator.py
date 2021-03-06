# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

# Modification for multi-core by Xiao Yu, xyu40@gatech.edu

from Tracer import *

class Navigator(Tracer):
    def __init__(Self, CodeBase, StackBase, StartingSP, Analysis=None) :
        super(Navigator, Self).__init__()
        Self.Trace_Index = 0
        Self.Analysis = Analysis
        # Navigator also may have Current_BB and Current_Loop attributes 
        # if there is an Analysis
        Self.Assign_BB_Loop(CodeBase, Analysis)
        Self.Lexical_Address = CodeBase
        Self.CodeBase = CodeBase
        Self.StackBase = StackBase
        Self.StartingSP = StartingSP

    def __repr__(Self) :
        return '[Nav %i Address: %i]' %(Self.Trace_Index, Self.Lexical_Address)

    def Clear(Self) :
        super(Navigator, Self).Clear()
        Self.Trace_Index = 0
        Self.Lexical_Address = Self.CodeBase
        Self.Assign_BB_Loop(Self.CodeBase)

    def Goto_Start_of_Trace(Self):
        Self.Trace_Index = 0
        Self.Lexical_Address = Self.CodeBase
        Self.Assign_BB_Loop(Self.CodeBase)

    def Map_to_Analysis(Self, Analysis) :
        """ 

        This can be used after a CFA has been performed to map an existing
        Navigator state to the BB and Loop (if any) in which Lexical_Address
        occurs.

        """
        Self.Analysis = Analysis
        Self.Assign_BB_Loop(Self.Lexical_Address, Analysis)

    def Assign_BB_Loop(Self, Address, Analysis = None) :
        """

        Assign Current_BB and Current_Loop attributes of navigator to be those
        containing the instruction with Address.

        """
        if Analysis :
            raise NotImplementedError("Analysis not supported in mt yet")
            New_BB = Analysis.Find_BB_w_Inst(Address)
            if New_BB :
                Self.Current_BB = New_BB
                Self.Current_Loop = New_BB.Loop
            elif Analysis :
                Self.Sim.Print_Error(
                    'Cannot find Basic Block containing instruction address %i.'\
                    % Address)
            # else: do nothing (no CFA has been performed)

    def Next_Inst(Self) :
        """
        
        Move to the next instruction in the trace.  If at the end of trace, do
        nothing.

        """
        if len(Self.Trace)-1 <> Self.Trace_Index :
            New_Trace_Index = Self.Trace_Index + 1
            return Self.Move_to_Instruction(New_Trace_Index)
        else :
            return (Self.Trace_Index, 0, {}, {}, {}, {})

    def Prev_Inst(Self) :
        """
        
        Move to the previous instruction in the trace.  If at the start of
        trace, do nothing.

        """
        if not Self.Trace_Index == 0 :
            New_Trace_Index = Self.Trace_Index - 1
            return Self.Move_to_Instruction(New_Trace_Index)
        else :
            return (Self.Trace_Index, 0, {}, {}, {}, {})

    def Move_to_Top(Self) :
        """ Move to the first instruction in the trace. """
        if not Self.Trace_Index == 0 :
            return Self.Move_to_Instruction(0)
        else :
            return (Self.Trace_Index, 0, {}, {}, {}, {})

    def Move_to_Bottom(Self) :
        """ Move to the last instruction in the trace. """
        Last_Trace_Index = len(Self.Trace) - 1
        if not Self.Trace_Index == Last_Trace_Index :
            return Self.Move_to_Instruction(Last_Trace_Index)
        else :
            return (Self.Trace_Index, 0, {}, {}, {}, {})
        
    def Move_to_Instruction(Self, New_Trace_Index) :
        """ 
        
        Update the current trace and lexical indices.  If New_I_Address is
        still within the same Current_BB, then don't change Current BB or
        Current Loop.  Otherwise, find out which BB it is in and whether it is
        in a loop.  Update the register file and memory to reflect the movement
        within the trace.

        Return:
            + the new IP,
            + new trace index,
            + dictionary of changes to registers,
            + dictionary of changes to data memory (static and heap), and
            + dictionary of changes to stack.

        Reg_Changes dictionary: indexed by core id, then by reg number; data is
        a pair consisting of the last value assigned to that register and
        whether the register was newly allocated/deallocated during the move
        w/in the trace.

        Mem_Changes dictionary: indexed by effective addresses of stores that
        occur during the move w/in the trace and each item in the dictionary
        contains the last value stored to that location and whether the
        location is newly allocated/deallocated.

        Stack_Changes dictionary: indexed by effective addresses of stack
        stores; data is of the same type as in Mem_Changes.

        This is the core function that all the other move instructions call.

        """
        CoreID, InstIP, Where, Old, New = \
                Self.Trace[New_Trace_Index]
        #New_Lexical_Address = Instruction.Address
        Old_Trace_Index = Self.Trace_Index
        CurrCore, IP_Changes, Reg_Changes, Mem_Changes = \
                Self.Update_Status(Old_Trace_Index, New_Trace_Index)
        Mem_Changes, Stack_Changes = Self.Classify_Mem_Changes(Mem_Changes)
        Self.Trace_Index = New_Trace_Index
        if Self.Analysis :
            pass
            #if (not Self.Current_BB) or \
            #   (not Self.Current_BB.Member_Instruction(New_Lexical_Address)):
            #    Self.Assign_BB_Loop(New_Lexical_Address, Self.Analysis)
            # else: New_I is in the Current_BB already, 
            # so no need to change Current_BB/Loop
        # else: no need to update BB info since no CFA was performed.
        return (New_Trace_Index, CurrCore, IP_Changes, Reg_Changes, 
                Mem_Changes, Stack_Changes)

    def Update_Status(Self, Old_Trace_Index, New_Trace_Index) :
        CurrCore = None
        IP_Changes = {}
        Reg_Changes = {}
        Mem_Changes = {}
        if Old_Trace_Index > New_Trace_Index :
            Direction = -1
        else : Direction = 1
        while not Old_Trace_Index == New_Trace_Index :
            if Direction == 1 :
                CoreID, InstIP, Where, Old, New = Self.Trace[Old_Trace_Index]
                print 'Navigator.Update_Status', CoreID, InstIP, Where, Old, New
            else :
                CoreID, InstIP, Where, Old, New = Self.Trace[Old_Trace_Index - 1]
                print 'Navigator.Update_Status', CoreID, InstIP, Where, Old, New
            # apply ip changes
            IP_Changes[CoreID] = InstIP
            CurrCore = CoreID
            # update trace index
            Old_Trace_Index = Old_Trace_Index + Direction
            # update changes
            # Where, Old, New should be all None or all have value
            if ((Where is None) and (Old is None) and (New is None)):
                continue
            if ((Where is None) or (Old is None) or (New is None)):
                raise RuntimeError(
                    "Trace is messed up: Where=%s, Old=%s, New=%s" %(
                    Where, Old, New))
            # apply the side-effect of this instruction
            if Where[0] == 'Mem':
                Mem_Changes = Self.Update_Mem(
                    Where[1], Old, New, Direction, Mem_Changes)
            elif Where[0] == 'Reg':
                Reg_Changes = Self.Update_Reg(
                    CoreID, Where[1], Old, New, Direction, Reg_Changes)
            else:
                raise RuntimeError(
                    "Unknown side effect: %s. "
                    "Possibly because interrupt handling not implemented.")
                # Old_Value is actually a dictionary of Memory changes, 
                #  indexed by mem addr
                # New_Value is actually a dictionary of Register changes, 
                #  indexed by reg number
                # Each dictionary entry has a tuple value (Old, New).
                Reg_Changes = Self.Update_swi_Regs(
                    New_Inst, New_Value, Direction, Reg_Changes)
                Mem_Changes = Self.Update_swi_Mem(
                    New_Inst, Old_Value, Direction, Mem_Changes)
                if Direction == 1 :
                    New_Inst.Sim.Handler.Next_SWI(New_Inst.Src1)
                else :
                    New_Inst.Sim.Handler.Prev_SWI(New_Inst.Src1)
        return (CurrCore, IP_Changes, Reg_Changes, Mem_Changes)

    def Update_swi_Regs(Self, New_Inst, Reg_Change_Dictionary, 
                        Direction, Reg_Changes):
        """
        
        Reg_Change_Dictionary is a dictionary of Register changes, indexed by
        register number; each dictionary entry has a tuple value (Old, New).
        Loop through each entry and call Update_Reg.

        """
        raise NotImplementedError("Interrupt Handling not supported in mt yet")
        for Change_Entry in Reg_Change_Dictionary.items() :
            Reg_Num = Change_Entry[0]
            Old_Value, New_Value = Change_Entry[1]
            Reg_Changes = Self.Update_Reg(
                New_Inst, New_Value, Old_Value, Direction, Reg_Changes, Reg_Num)
        return Reg_Changes
    
    def Update_Reg(Self, CoreID, RegNum, Old, New, Direction, Reg_Changes):
        #Interruption handling not considered yet.
        Allocation_Mod = (Reg_Changes.has_key(CoreID) and 
                          Reg_Changes[CoreID].has_key(RegNum) and 
                          Reg_Changes[CoreID][RegNum][1]) \
                         or (Old == 'undefined')
        if Direction == 1 :
            #forward
            if not Reg_Changes.has_key(CoreID):
                Reg_Changes[CoreID] = {}
            Reg_Changes[CoreID][RegNum] = (New, Allocation_Mod)
        else :  
            # reverse
            if not Reg_Changes.has_key(CoreID):
                Reg_Changes[CoreID] = {}
            Reg_Changes[CoreID][RegNum] = (Old, Allocation_Mod)
        return Reg_Changes

    def Update_swi_Mem(Self, New_Inst, Mem_Change_Dictionary, 
                       Direction, Mem_Changes):
        """
        
        Mem_Change_Dictionary is a dictionary of Memory changes, indexed by
        memory address; each dictionary entry has a tuple value (Old, New).
        Loop through each entry and call Update_Mem.

        """
        raise NotImplementedError("Interrupt Handling not supported in mt yet")
        for Change_Entry in Mem_Change_Dictionary.items() :
            Mem_Address = Change_Entry[0]
            Old_Value, New_Value = Change_Entry[1]
            Mem_Changes = Self.Update_Mem(New_Inst, New_Value, Old_Value, 
                                          Direction, Mem_Changes, Mem_Address)
        return Mem_Changes
        
    def Update_Mem(Self, Address, Old, New, Direction, Mem_Changes) :
        #Interruption handling not considered yet.
        Allocation_Mod = (
            Mem_Changes.has_key(Address) and Mem_Changes[Address][1]) \
                         or (Old == 'undefined')
        if Direction == 1 :     # forward
            Mem_Changes[Address] = (New, Allocation_Mod)
        else :  # reverse
            Mem_Changes[Address] = (Old, Allocation_Mod)
        return Mem_Changes

    def Is_Stack_Address(Self, Address):
        return Self.StackBase <= Address <= Self.StartingSP

    def Classify_Mem_Changes(Self, Mem_Changes) :
        """ 
        
        Separate out stack-based memory changes from data memory changes.
        Return two dictionaries: Mem_Changes (original dictionary with data
        memory changes only) and Stack_Changes (entries involving stack
        addresses).

        """
        Stack_Changes = {}
        for Address in Mem_Changes.keys() :
            if Self.Is_Stack_Address(Address) :
                Stack_Changes[Address] = Mem_Changes[Address]
                del Mem_Changes[Address]
        return Mem_Changes, Stack_Changes

    def Move_to_Top_of_BB(Self) :
        """ Move to the top of the current basic block."""
        raise NotImplementedError("Analysis not supported in mt yet")
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
            
    def Move_to_Bottom_of_BB(Self) :
        """ 
        
        Move to the bottom of the current basic block.  If currently at the
        bottom of block, do nothing.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
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
    
    def Move_to_Top_of_Loop(Self) :
        """ 
        
        Move to the top of the current loop.  If not currently in a loop or if
        already at the top, do nothing.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if not Self.Analysis :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        elif Self.Current_Loop :
            Top_Address = Self.Current_Loop.Starting_Address
            New_Trace_Index = Self.Find_Inst(Top_Address, Trace, -1)
            if New_Trace_Index :
                return Self.Move_to_Instruction(New_Trace_Index, Trace)
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Bottom_of_Loop(Self) :
        """ 
        
        Move to the bottom of the current loop.  If not currently in a loop, or
        if already at the bottom, do nothing.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if not Self.Analysis :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        elif Self.Current_Loop :
            Bottom_Address = Self.Current_Loop.Back_Address
            New_Trace_Index = Self.Find_Inst(Bottom_Address, Trace, 1)
            if New_Trace_Index :
                return Self.Move_to_Instruction(New_Trace_Index, Trace)
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
            
    def Move_to_Next_BB(Self) :
        """ 
        
        Move to the bottom of the current basic block and then move to the next
        instruction after. If there are no instructions/basic blocks after the
        current basic block, stay at the end of the current basic block.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        ### Return values not propagated correctly
        if Self.Analysis :
            Self.Move_to_Bottom_of_BB(Trace)
            Self.Next_Inst(Trace)
        else :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Prev_BB(Self) :
        """ 
        
        Move to the top of the current basic block and then move to the
        instruction before. If there are no instructions/basic blocks before
        the current basic block, stay at the top of the current basic block.

        """
         ### Return values not propagated correctly
        raise NotImplementedError("Analysis not supported in mt yet")
        if Self.Analysis :
            Self.Move_to_Top_of_BB(Trace)
            Self.Prev_Inst(Trace)
        else :
            Self.Sim.Print_Warning('No control flow analysis has been performed.')
        return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Next_Occurrence(Self) :
        """ 
        
        Move to the next instance of the current lexical instruction in the
        trace.  If there are no more instances, do nothing. 

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Next_Instance_Index = Self.Find_Inst(Self.Lexical_Address, Trace, 1)
        if Next_Instance_Index :
            return Self.Move_to_Instruction(Next_Instance_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
    
    def Move_to_Prev_Occurrence(Self) :
        """ 
        
        Move to the previous instance of the current lexical instruction in the
        trace.  If there are no earlier instances, do nothing. 

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Prev_Instance_Index = Self.Find_Inst(Self.Lexical_Address, Trace, -1)
        if Prev_Instance_Index :
            return Self.Move_to_Instruction(Prev_Instance_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Address(Self, Inst_Address) :
        """ 
        
        Move to the next occurance in the trace of the specified instruction
        address. If there are no later instances, do nothing. 

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if Inst_Address > Self.Sim.IP :
            Addr_Trace_Index = Self.Find_Inst(Inst_Address, Trace, 1)
        else :
            Addr_Trace_Index = Self.Find_Inst(Inst_Address, Trace, -1)
        if Addr_Trace_Index :
            return Self.Move_to_Instruction(Addr_Trace_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})

    def Move_to_Producer_of_Src1(Self, Register=None) :
        """ 
        
        Move to the Instruction that most recently wrote Register or to the
        current instruction's source1 operand if Register is not provided. 

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if not Register :
            Inst = Self.Trace[Self.Trace_Index][0]
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

    def Move_to_Producer_of_Src2(Self, Register=None) :
        """ 
        
        Move to the Instruction that most recently wrote Register or to the
        current instruction's source2 operand if Register is not provided. 

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if not Register :
            Inst = Self.Trace[Self.Trace_Index][0]
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
            
    def Move_to_Next_Writer_of_Dest(Self, Register=None) :
        """ 
        
        Move to the next instruction that writes to Register or the current
        instruction's destination operand if Register is not provided.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if not Register :
            Inst = Self.Trace[Self.Trace_Index][0]
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

    def Move_to_Consumer_of_Dest(Self, Register=None) :
        """ 
        
        Move to the next instruction that uses Register or the current
        instruction's destination operand if Register is not provided.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        if not Register :
            Inst = Self.Trace[Self.Trace_Index][0]
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

    def Move_to_Next_Control_Transfer(Self) :
        """ 
        
        Move to the next place in Trace where a jump or branch occurred,
        determined solely by a discontinuity in instruction addresses (a
        difference other than 4).

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Control_Transfer_Index = Self.Find_Control_Transfer(Trace, 1)
        if Control_Transfer_Index :
            return Self.Move_to_Instruction(Control_Transfer_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
            
    def Move_to_Prev_Control_Transfer(Self) :
        """ 
        
        Move to the next place in Trace where a jump or branch occurred,
        determined solely by a discontinuity in instruction addresses (a
        difference other than 4).

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Control_Transfer_Index = Self.Find_Control_Transfer(Trace, -1)
        if Control_Transfer_Index :
            return Self.Move_to_Instruction(Control_Transfer_Index, Trace)
        else :
            return (Self.Lexical_Address, Self.Trace_Index, {}, {}, {})
        
    def Find_Control_Transfer(Self, Direction) :
        """ 
        
        Find the trace index of the next place where a jump or branch occurred,
        looking either up (Direction = 1) or down (Direction = -1). Return the
        trace index or None if the Inst_Address is not found.  The transfer of
        control should b determined solely by a discontinuity in instruction
        addresses (a difference other than 4).

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Trace_Length = len(Trace)
        Current_Trace_Index = Self.Trace_Index
        New_Trace_Index = Current_Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) and \
              (0 <= Current_Trace_Index) and (Current_Trace_Index < Trace_Length) :
            Current_Address = Self.Trace[Current_Trace_Index][0].Address
            Next_Address = Self.Trace[New_Trace_Index][0].Address
            Difference = Current_Address - Next_Address
            if abs(Difference) == 4 :
                New_Trace_Index = New_Trace_Index + Direction
                Current_Trace_Index = Current_Trace_Index + Direction
            else :
                return New_Trace_Index 
        return None
        
    def Find_Inst(Self, Inst_Address, Direction) :
        """ 
        
        Find the trace index of the next place Inst_Address occurs in Trace,
        looking either up (Direction = 1) or down (Direction = -1). Return the
        trace index or None if the Inst_Address is not found.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Trace_Length = len(Trace)
        New_Trace_Index = Self.Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) :
            if (Inst_Address == Self.Trace[New_Trace_Index][0].Address) :
                return New_Trace_Index
            else :
                New_Trace_Index = New_Trace_Index + Direction
        return None

    def Find_Inst_w_Dest(Self, Dest_Reg, Direction) :
        """ 
        
        Find the trace index of the next place an instruction with destination
        register Dest occurs in Trace, looking either up (Direction = 1) or
        down (Direction = -1). Return the trace index or None if no such
        instruction is found.

        """
        raise NotImplementedError("Analysis not supported in mt yet")
        Trace_Length = len(Trace)
        New_Trace_Index = Self.Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) :
            Inst = Self.Trace[New_Trace_Index][0]
            if Inst.Has_Dest() :
                Dest = Inst.Dest
                if (Dest_Reg == Dest) :
                    return New_Trace_Index
            New_Trace_Index = New_Trace_Index + Direction
        return None

    def Find_Inst_w_Src(Self, Src, Direction) :
        """ 
        
        Find the trace index of the next place an instruction occurs in Trace
        with Src register as one of its source operands , looking either up
        (Direction = 1) or down (Direction = -1). Return the trace index or
        None if no such instruction is found.

        """ 
        raise NotImplementedError("Analysis not supported in mt yet")
        Trace_Length = len(Trace)
        New_Trace_Index = Self.Trace_Index + Direction
        while (0 <= New_Trace_Index) and (New_Trace_Index < Trace_Length) :
            Inst = Self.Trace[New_Trace_Index][0]
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


