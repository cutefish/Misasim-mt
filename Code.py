# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Major modification for multi-core by Xiao Yu, xyu40@gatech.edu

class Code:
    """

    Code objects are parsed assemblies. Each assembly code has a bunch of
    InitCommands and Instructions with a CodeBase.  
   
    """

    def __init__(Self, InitCommands, Instructions, CodeBase=1000):
        Self.CodeBase = CodeBase
        Self.Instructions = Instructions
        Self.InitCommands = InitCommands

    def Is_Valid_IP(Self, IP):
        return Self.CodeBase <= IP <= Self.Instructions[-1].Address

    def Lookup_Instruction(Self, Address) :
        """ This routine looks up an instruction using an address. """
        Position = Self.Lookup_Instruction_Position(Address)
        if not Position == '':
            return Self.Instructions[Position]
        else :
            return None

    def Lookup_Instruction_Position(Self, Address) :
        """ 

        This routine looks up an instruction position using an address. First
        an index is computing into the instruction list. If the instruction
        does not match, all instructions are searched. 

        """
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

