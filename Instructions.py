from Simulator import SimLogger
from ParseUtils import *

class Instruction :
    def __init__(Self, Opcode, Address) :
        Self.Address = Address
        Self.Opcode = Opcode

    def __repr__(Self) :
        return '[%04i: %s]' % (Self.Address, Self.Opcode)

    def Opcode(Self) :
        return Self.Opcode

#    def Adjust_IP(Self, Core) :
#        Core.IP += 4

#    def Log_In_Trace(Self, Result, OldValue) :
#        Self.Sim.Trace.append((Self, Result, OldValue))

    def Has_Dest(Self) :
        if Self.Opcode in \
           ['add', 'sub', 'addi', 'addu', 'subu', 'addiu', 'mfhi', 'mflo',\
            'and', 'or', 'andi', 'ori', 'nor', 'xor', 'xori', 'sll', 'sllv', \
            'srl', 'srlv', 'sra', 'srav', 'lw', 'lb', 'lbu', 'lui', \
            'slt', 'slti', 'sltu', 'sltui'] :
            return True
        else : 
            return False

    def Has_Src1(Self) :
        if Self.Opcode in \
           ['add', 'sub', 'addi', 'addu', 'subu', 'addiu', \
            'mult', 'multu', 'div', 'divu', 'and', \
            'or', 'andi', 'ori', 'nor', 'xor', 'xori', 'sll', 'sllv', \
            'srl', 'srlv', 'sra', 'srav', 'lw', 'lb', 'lbu', 'sw', 'sb', \
            'lui', 'beq', 'bne', 'slt', 'slti', 'sltu', 'sltui', 'jr'] :
            return True
        else : 
            return False

    def Has_Src2(Self) :
        if Self.Opcode in \
           ['add', 'sub', 'addu', 'subu', \
            'mult', 'multu', 'div', 'divu', 'and', \
            'or', 'nor', 'xor', 'sllv', 'srlv', 'srav', \
            'sw', 'sb', 'beq', 'bne', \
            'slt', 'sltu']:
            return True
        else : 
            return False

    def Lookup_Label(Self, Label, Symbols) :
        """ This routine looks up a label in the symbol table and returns the
        corresponding address. """
        if Label in Symbols :
            return Symbols[Label]
        else :
            Self.SimLogger.error('Label %s has not been defined.' % (Label))
            return ''

class Three_Reg(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 3 :
            return ''
        Self.Dest = Parse_Register(Tokens[0])
        Self.Src1 = Parse_Register(Tokens[1])
        Self.Src2 = Parse_Register(Tokens[2])
        Self.Comment = Parse_Comment(Tokens[3:])
        if Self.Dest == '' or Self.Src1 == '' or Self.Src2 == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def RunOn(Self, Executor) :
        Result = Self.Op(Self.Read_Reg(Self.Src1),Self.Read_Reg(Self.Src2))
        OldValue = Self.Write_Reg(Self.Dest, Result)
        return Result, OldValue
    def Print(Self) :
        return '%4i %s %-5s $%02i, $%02i, $%02i      %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Dest, \
                Self.Src1, Self.Src2, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', Print_Label(Self.Label)),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Dest)),
                (None, ', '),
                ('Reg', '$%02i' % (Self.Src1)),
                (None, ', '),
                ('Reg', '$%02i' % (Self.Src2)),
                (None, '     '),
                ('Comment', ' %s' % (Self.Comment)))

class Two_Reg(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 2 :
            return ''
        Self.Src1 = Parse_Register(Tokens[0])
        Self.Src2 = Parse_Register(Tokens[1])
        Self.Comment = Parse_Comment(Tokens[2:])
        if Self.Src1 == '' or Self.Src2 == '' or \
           (not Tokens[2:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec (Self) :
        if Self.Op == Div_Op and Self.Read_Reg(Self.Src2) == 0 :
            Self.Sim.Print_Error('Divide by zero')
        Result = Self.Op(Self.Read_Reg(Self.Src1), Self.Read_Reg(Self.Src2))
        OldValue = Self.Write_Reg('HiLo', Result)
        return Result, OldValue
    def Print(Self) :
        return '%4i %s %-5s $%02i, $%02i           %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Src1, \
                Self.Src2, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', (Print_Label(Self.Label))),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Src1)),
                (None, ', '),
                ('Reg', '$%02i' % (Self.Src2)),
                (None, '          '),
                ('Comment', ' %s' % (Self.Comment)))

class One_Reg_CoreID(Instruction):
    def Parse(Self, Tokens):
        if len(Tokens) < 1: 
            return ''
        Self.Reg = Parse_Register(Tokens[0])
        Self.Comment = Parse_Comment(Tokens[1:])
        if Self.Reg == '' or (not Tokens[1:] == [] and Self.Comment == '') :
            return ''
    def Exec(Self, Core):
        Self.Write_Reg(Self.Reg, Core.CoreID)
        return Core.CoreID

class One_Reg(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 1 :
            return ''
        Self.Reg = Parse_Register(Tokens[0])
        Self.Comment = Parse_Comment(Tokens[1:])
        if Self.Reg == '' or (not Tokens[1:] == [] and Self.Comment == '') :
            return ''
        if Self.Opcode == 'jr' :
            Self.Src1 = Self.Reg
        if Self.Opcode in ['mfhi', 'mflo'] :
            Self.Dest = Self.Reg
        return Self
    def Exec (Self) :
        if Self.Opcode == 'jr' :
            return None, None
        elif Self.Opcode == 'mfhi' :
            Result = Self.Read_Reg('HiLo')[0]
        elif Self.Opcode == 'mflo' :
            Result = Self.Read_Reg('HiLo')[1]
        OldValue = Self.Write_Reg(Self.Reg, Result)
        return Result, OldValue
    def Adjust_IP (Self) :
        if Self.Opcode == 'jr' :
            Self.Sim.IP = Self.Read_Reg(Self.Reg)
        else :
            Instruction.Adjust_IP(Self)
    def Print(Self) :
        return '%4i %s %-5s $%02i                %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Reg, \
                Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % Self.Address),
                (None, ' '),
                ('Label', (Print_Label(Self.Label))),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Reg)),
                (None, '               '),
                ('Comment', ' %s' % (Self.Comment)))

class Two_Reg_Sex_Immd(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 3 :
            return ''
        Self.Dest = Parse_Register(Tokens[0])
        Self.Src1 = Parse_Register(Tokens[1])
        Label, Immd = Parse_Label_or_Immediate(Tokens[2])
        if Label :
            Self.Src2 = Self.Lookup_Label(Label)
            Self.Immed_Label = Label
        elif Immd <> '' :
            Self.Src2 = (Immd + 32768) % 65536 - 32768
        else :
            Self.Src2 = Immd
        Self.Comment = Parse_Comment(Tokens[3:])
        if Self.Dest == '' or Self.Src1 == '' or Self.Src2 == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec (Self) :
        Result = Self.Op(Self.Read_Reg(Self.Src1), Self.Src2)
        OldValue = Self.Write_Reg(Self.Dest, Result)
        return Result, OldValue
    def Print(Self) :
        return '%4i %s %-5s $%02i, $%02i, %-8i %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Dest,\
                Self.Src1, Self.Src2, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', (Print_Label(Self.Label))),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Dest)),
                (None, ', '),
                ('Reg', '$%02i' % (Self.Src1)),
                (None, ', '),
                ('Immd', '%-8i' % (Self.Src2)),
                ('Comment', ' %s' % (Self.Comment)))

class Two_Reg_Immd(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 3 :
            return ''
        Self.Dest = Parse_Register(Tokens[0])
        Self.Src1 = Parse_Register(Tokens[1])
        Label,  Immd = Parse_Label_or_Immediate(Tokens[2])
        if Label :
            Self.Src2 = Self.Lookup_Label(Label)
            Self.Immed_Label = Label
        else :
            Self.Src2 = Immd
        Self.Comment = Parse_Comment(Tokens[3:])
        if Self.Dest == '' or Self.Src1 == '' or Self.Src2 == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec (Self) :
        Result = Self.Op(Self.Read_Reg(Self.Src1), Self.Src2)
        OldValue = Self.Write_Reg(Self.Dest, Result)
        return Result, OldValue
    def Print(Self) :
        return '%4i %s %-5s $%02i, $%02i, %-8i %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Dest,\
                Self.Src1, Self.Src2, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', (Print_Label(Self.Label))),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Dest)),
                (None, ', '),
                ('Reg', '$%02i' % (Self.Src1)),
                (None, ', '),
                ('Immd', '%-8i' % (Self.Src2)),
                ('Comment', ' %s' % (Self.Comment)))

class Two_Reg_Label(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 3 :
            return ''
        Self.Src1 = Parse_Register(Tokens[0])
        Self.Src2 = Parse_Register(Tokens[1])
        Self.Target = Parse_Label_Ref(Tokens[2])
        if Self.Target == '' :
            Self.Offset = Parse_Immediate(Tokens[2])
        else :
            Self.Offset = False
        Self.Comment = Parse_Comment(Tokens[3:])
        if Self.Src1 == '' or Self.Src2 == '' or \
           (Self.Target == '' and Self.Offset == '') or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec (Self) :
        return None, None
    def Adjust_IP (Self) :
        if Self.Target == '' :
            Target = Self.Sim.IP + 4 + (Self.Offset * 4)
        else :
            Target = Self.Lookup_Label(Self.Target)
        Predicate = Self.Read_Reg(Self.Src1) == Self.Read_Reg(Self.Src2)
        if Self.Opcode == 'bne' :
            Predicate = Predicate ^ 1
        if Predicate :
            Self.Sim.IP = Target
        else :
            Instruction.Adjust_IP(Self)
    def Print(Self) :
        return '%4i %s %-5s $%02i, $%02i, %-8s %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Src1,\
                Self.Src2, (Self.Offset or Self.Target), Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', Print_Label(Self.Label)),
                ('Opcode', ' %-5s ' % Self.Opcode),
                ('Reg', '$%02i' % (Self.Src1)),
                (None, ', '),
                ('Reg', '$%02i' % (Self.Src2)),
                (None, ', '),
                ('Label', '%-8s' % (Self.Offset or Self.Target)),
                ('Comment', ' %s' % (Self.Comment)))

class One_Reg_Immd(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 2 :
            return ''
        Self.Dest = Parse_Register(Tokens[0])
        Self.Src1 = Parse_Immediate(Tokens[1])
        Self.Comment = Parse_Comment(Tokens[2:])
        if Self.Dest == '' or Self.Src1 == '' or \
           (not Tokens[2:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec(Self) :    # lui instruction
        Result = int(((Self.Src1 << 16) + 2**31) % 2**32 - 2**31)
        OldValue = Self.Write_Reg(Self.Dest, Result)
        return Result, OldValue
    def Print(Self) :
        return '%4i %s %-5s $%02i, %-13i %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Dest,\
                Self.Src1, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', Print_Label(Self.Label)),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Dest)),
                (None, ', '),
                ('Immd', '%-13i' % (Self.Src1)),
                ('Comment', ' %s' % (Self.Comment)))

class One_Reg_Addr(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 2 :
            return ''
        Self.Data = Parse_Register(Tokens[0])
        Offset, Self.Reg = Parse_Address(Tokens[1])
        Label,  Immd = Parse_Label_or_Immediate(Offset)
        if not Label and Immd == '' :
            return ''
        if Label :
            Self.Offset = Self.Lookup_Label(Label)
            Self.Immed_Label = Label
        else :
            Self.Offset = Immd
        Self.Comment = Parse_Comment(Tokens[2:])
        if Self.Data == '' or Self.Offset == '' or Self.Reg == '' or \
           (not Tokens[2:] == [] and Self.Comment == '') :
            return ''
        if Self.Opcode in ('lw', 'lb', 'lbu') :
            Self.Dest = Self.Data
            Self.Src1 = Self.Reg
        if Self.Opcode in ('sw', 'sb') :
            Self.Src1 = Self.Data
            Self.Src2 = Self.Reg
        return Self
    def Exec(Self) :
        Address = Self.Read_Reg(Self.Reg) + Self.Offset
        if Self.Opcode in ('lb', 'lbu') :   # lb, lbu instructions
            Shift = 8 * (Address % 4)
            Address &= -4
            Result = Self.Read_Mem(Address)
            Result >>= Shift
            Result &= 255
            if Self.Opcode == 'lb' :
                Result = (Result + 128) % 256 - 128
            OldValue = Self.Write_Reg(Self.Data, Result)
            return Result, OldValue
        if Self.Opcode == 'sb' :            # sb instruction
            Shift = 8 * (Address % 4)
            Address &=  -4
            OldValue = Self.Read_Mem(Address)
            NewByte = Self.Read_Reg(Self.Data) % 256
            Result = (OldValue & ((255 << Shift) ^ -1)) | NewByte << Shift
            Result = int((Result + 2**31) % 2**32 - 2**31)
            OldValue = Self.Write_Mem(Address, Result)
            return Result, OldValue
        if Address % 4 <> 0 :
            Self.Sim.Print_Error('Effective Address = %d; memory addresses must be word aligned' % (Address))
            Address &= -4
        if Self.Opcode == 'lw' :        # lw instruction
            Result = Self.Read_Mem(Address)
            OldValue = Self.Write_Reg(Self.Data, Result)
            return Result, OldValue
        elif Self.Opcode == 'sw' :      # sw instruction
            Result = Self.Read_Reg(Self.Data)
            OldValue = Self.Write_Mem(Address, Result)
            return Result, OldValue
    def Print(Self) :
        return '%4i %s %-5s $%02i, %4i($%02i)     %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Data,\
                Self.Offset, Self.Reg, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', (Print_Label(Self.Label))),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Reg', '$%02i' % (Self.Data)),
                (None, ', '),
                ('Immd', '%4i' % (Self.Offset)),
                (None, '('),
                ('Reg', '$%02i' % (Self.Reg)),
                (None, ')    '),
                ('Comment', ' %s' % (Self.Comment)))

class One_Label(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 1 :
            return ''
        Self.Target = Parse_Label_Ref(Tokens[0])
        Self.Comment = Parse_Comment(Tokens[1:])
        if Self.Target == '' or (not Tokens[1:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec(Self) :
        if Self.Opcode == 'j' :         # j instruction
            return None, None
        elif Self.Opcode == 'jal' :     # jal instruction
            Result = Self.Sim.IP+4
            OldValue = Self.Write_Reg(31, Result)
            return Result, OldValue
    def Adjust_IP(Self) :
        Self.Sim.IP = Self.Lookup_Label(Self.Target)
    def Print(Self) :
        return '%4i %s %-5s %-18s %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Target, \
                Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', (Print_Label(Self.Label))),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Label', '%-18s' % (Self.Target)),
                ('Comment', ' %s' % (Self.Comment)))

class One_Immd(Instruction) :
    def Parse(Self, Tokens) :
        if len(Tokens) < 1 :
            return ''
        Self.Src1 = Parse_Immediate(Tokens[0])
        Self.Comment = Parse_Comment(Tokens[1:])
        if Self.Src1 == '' or (Tokens[1:] <> [] and Self.Comment == '') :
            return ''
        return Self
    def Exec(Self) :                    # swi instruction
        if Self.Sim.Handler.Known_Interrupt(Self.Src1) :
            return Self.Sim.Handler.Call(Self.Src1)
        else :
            Self.Sim.Print_Error('%i is an undefined software interrupt.' % (Self.Src1))
            return {}, {}
    def Print(Self) :
        return '%4i %s %-5s %i                %s' % \
               (Self.Address, Print_Label(Self.Label), Self.Opcode, Self.Dest,\
                Self.Src1, Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', '%4i' % (Self.Address)),
                (None, ' '),
                ('Label', Print_Label(Self.Label)),
                ('Opcode', ' %-5s ' % (Self.Opcode)),
                ('Immd', '%i' % (Self.Src1)),
                (None, '               '),
                ('Comment', ' %s' % (Self.Comment)))


