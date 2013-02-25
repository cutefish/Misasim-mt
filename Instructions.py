# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Major modification for multi-core by Xiao Yu, xyu40@gatech.edu


from Logging import LogFactory
from Opcodes import *
from Parser import *

Logger = LogFactory.getLogger('Instructions')

class Instruction :
    def __init__(Self, Opcode, Address) :
        Self.Address = Address
        Self.Opcode = Opcode

    def __repr__(Self) :
        return '[%04i: %s]' % (Self.Address, Self.Opcode)

    def Opcode(Self) :
        return Self.Opcode

    def Adjust_IP(Self, Executor) :
        Executor.Inc_IP()

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

    def Print_Address(Self, Address):
        return '%4i' %Address

    def Print_Label (Self, String) :
        """ If string is non-null label, return padded with colon; else return
        padding only. """
        if String == '' :
            return ' ' * 10
        return '%s:%s' % (String, (9 - len(String)) * ' ')

    def Print_Opcode(Self, Opcode):
        return '%-5s' %Opcode

    def Print_Reg(Self, RegNum):
        return '$%02i' %RegNum

    def Print_Immd(Self, Immd):
        return '%-13i' %Immd


    def Print_Offset(Self, Offset, RegNum):
        return '%s($%02i)' %(Offset, RegNum)

    def Print_Args(Self, Arg1, Arg2, Arg3):
        Return = ''
        if Arg1 <> '':
            Return += Arg1
        if Arg2 <> '':
            Return += ', '
            Return += Arg2
        if Arg3 <> '':
            Return += ', '
            Return += Arg3
        return Return.ljust(28)

    def Format(Self, Address, Label, Opcode, Arg1, Arg2, Arg3, Comment):
        Return = ''
        Return += Self.Print_Address(Address) + ' '     #width = 5
        Return += Self.Print_Label(Label) + ' '         #width = 11
        Return += Self.Print_Opcode(Opcode) + ' '       #width = 6
        Return += Self.Print_Args(Arg1, Arg2, Arg3)     #width = 28
        Return += Comment
        return Return

    def __str__(Self):
        return Self.Print()

class Three_Reg(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 3 :
            return ''
        Self.Dest = Parser.Parse_Register(Tokens[0])
        Self.Src1 = Parser.Parse_Register(Tokens[1])
        Self.Src2 = Parser.Parse_Register(Tokens[2])
        Self.Comment = Parser.Parse_Comment(Tokens[3:])
        if Self.Dest == '' or Self.Src1 == '' or Self.Src2 == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor) :
        Result = Self.Op(Executor.Read_Reg(Self.Src1),
                         Executor.Read_Reg(Self.Src2))
        OldValue = Executor.Write_Reg(Self.Dest, Result)
        return ('Reg', Self.Dest), OldValue, Result
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Dest),
                           Self.Print_Reg(Self.Src1),
                           Self.Print_Reg(Self.Src2),
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Dest)),
                (None, ', '),#inc to 27
                ('Reg', Self.Print_Reg(Self.Src1)),
                (None, ', '),#inc to 32
                ('Reg', Self.Print_Reg(Self.Src2)),
                (None, ' '),#inc to 36
                (None, ' '*9), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class Two_Reg(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 2 :
            return ''
        Self.Src1 = Parser.Parse_Register(Tokens[0])
        Self.Src2 = Parser.Parse_Register(Tokens[1])
        Self.Comment = Parser.Parse_Comment(Tokens[2:])
        if Self.Src1 == '' or Self.Src2 == '' or \
           (not Tokens[2:] == [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor) :
        if Self.Op == Div_Op and Executor.Read_Reg(Self.Src2) == 0 :
            Logger.error('Divide by zero')
            raise RuntimeError('Divide by zero')
        Result = Self.Op(Executor.Read_Reg(Self.Src1), 
                         Executor.Read_Reg(Self.Src2))
        OldValue = Executor.Write_Reg('HiLo', Result)
        return ('Reg', 'HiLo'), OldValue, Result
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Src1),
                           Self.Print_Reg(Self.Src2),
                           '',
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Src1)),
                (None, ', '), #inc to 27
                ('Reg', Self.Print_Reg(Self.Src2)),
                (None, ' '), #inc to 31
                (None, ' '*14), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class One_Reg_CoreID(Instruction):
    def Parse(Self, Tokens, Parser):
        if len(Tokens) < 1: 
            return ''
        Self.Reg = Parser.Parse_Register(Tokens[0])
        Self.Comment = Parser.Parse_Comment(Tokens[1:])
        if Self.Reg == '' or (not Tokens[1:] == [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor):
        OldValue = Executor.Write_Reg(Self.Reg, Executor.Core.CoreID)
        return ('Reg', Self.Reg), OldValue, Executor.Core.CoreID
    def Print(Self):
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Reg),
                           '','',
                           Self.Comment)
    def Tagged_Print(Self):
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), # inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Reg)),
                (None, ' '), # inc to 26
                (None, ' '*19), #inc to 45
                ('Comment', '%s' %Self.Comment),
               )

class One_Reg_NumCores(Instruction):
    def Parse(Self, Tokens, Parser):
        if len(Tokens) < 1: 
            return ''
        Self.Reg = Parser.Parse_Register(Tokens[0])
        Self.Comment = Parser.Parse_Comment(Tokens[1:])
        if Self.Reg == '' or (not Tokens[1:] == [] and Self.Comment == ''):
            return ''
        return Self
    def ExecOn(Self, Executor):
        OldValue = Executor.Write_Reg(Self.Reg, Executor.Core.NumCores)
        return ('Reg', Self.Reg), OldValue, Executor.Core.NumCores
    def Print(Self):
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Reg),
                           '','',
                           Self.Comment)
    def Tagged_Print(Self):
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), # inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Reg)),
                (None, ' '), # inc to 26
                (None, ' '*19), #inc to 45
                ('Comment', '%s' %Self.Comment),
               )

class One_Reg(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 1 :
            return ''
        Self.Reg = Parser.Parse_Register(Tokens[0])
        Self.Comment = Parser.Parse_Comment(Tokens[1:])
        if Self.Reg == '' or (not Tokens[1:] == [] and Self.Comment == ''):
            return ''
        if Self.Opcode == 'jr' :
            Self.Src1 = Self.Reg
        if Self.Opcode in ['mfhi', 'mflo'] :
            Self.Dest = Self.Reg
        return Self
    def ExecOn(Self, Executor) :
        if Self.Opcode == 'jr' :
            return None, None, None
        elif Self.Opcode == 'mfhi' :
            Result = Executor.Read_Reg('HiLo')[0]
        elif Self.Opcode == 'mflo' :
            Result = Executor.Read_Reg('HiLo')[1]
        OldValue = Executor.Write_Reg(Self.Reg, Result)
        return ('Reg', Self.Reg), OldValue, Result
    def Adjust_IP(Self, Executor):
        if Self.Opcode == 'jr' :
            Executor.Jmpto_IP(Executor.Read_Reg(Self.Reg))
        else:
            Instruction.Adjust_IP(Self, Executor);
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Reg),
                           '', '',
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Reg)),
                (None, ' '),#inc to 26
                (None, ' '*19), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class Two_Reg_Sex_Immd(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 3 :
            return ''
        Self.Dest = Parser.Parse_Register(Tokens[0])
        Self.Src1 = Parser.Parse_Register(Tokens[1])
        Self.RefTarget = Reference()
        Label, Immd = Parser.Parse_Label_or_Immediate(Tokens[2])
        if Immd <> '':
            Self.RefTarget.Value = (Immd + 32768) % 65536 - 32768
            Self.RefTarget.Alias = 'immd'
            Self.RefTarget.Solved = True
        elif Label <> '':
            Self.RefTarget.Alias = Label #will be solved later
        else :
            #should never be here
            Logger.error('Syntax error: %s, no immediate.' %(Tokens))
            raise SyntaxError('no immediate')
        Self.Comment = Parser.Parse_Comment(Tokens[3:])
        if Self.Dest == '' or Self.Src1 == '' or Self.RefTarget.Alias == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor):
        Result = Self.Op(Executor.Read_Reg(Self.Src1), Self.RefTarget.Value)
        OldValue = Executor.Write_Reg(Self.Dest, Result)
        return ('Reg', Self.Dest), OldValue, Result
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Dest),
                           Self.Print_Reg(Self.Src1),
                           Self.RefTarget.Print(),
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Dest)),
                (None, ', '), #inc to 27
                ('Reg', Self.Print_Reg(Self.Src1)),
                (None, ', '), #inc to 32
                ('Immd', '%s' % (Self.RefTarget.Print())), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class Two_Reg_Immd(Instruction):
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 3 :
            return ''
        Self.Dest = Parser.Parse_Register(Tokens[0])
        Self.Src1 = Parser.Parse_Register(Tokens[1])
        Self.RefTarget = Reference()
        Label,  Immd = Parser.Parse_Label_or_Immediate(Tokens[2])
        if Immd <> '':
            Self.RefTarget.Value = Immd
            Self.RefTarget.Alias = 'immd'
            Self.RefTarget.Solved = True
        elif Label <> '':
            Self.RefTarget.Alias = Label #will be solved later
        else :
            Logger.error('Syntax error: %s, no immediate.' %(Tokens))
            raise SyntaxError('no immediate')
        Self.Comment = Parser.Parse_Comment(Tokens[3:])
        if Self.Dest == '' or Self.Src1 == '' or Self.RefTarget.Alias == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor) :
        Result = Self.Op(Executor.Read_Reg(Self.Src1), Self.RefTarget.Value)
        OldValue = Executor.Write_Reg(Self.Dest, Result)
        return ('Reg', Self.Dest), OldValue, Result
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Dest),
                           Self.Print_Reg(Self.Src1),
                           Self.RefTarget.Print(),
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Dest)),
                (None, ', '),#inc to 27
                ('Reg', Self.Print_Reg(Self.Src1)),
                (None, ', '),#inc to 32
                ('Immd', '%s' % (Self.RefTarget.Print())), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class Two_Reg_Label(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 3 :
            return ''
        Self.Src1 = Parser.Parse_Register(Tokens[0])
        Self.Src2 = Parser.Parse_Register(Tokens[1])
        Self.RefTarget = Reference()
        Label, Immd = Parser.Parse_Label_or_Immediate(Tokens[2])
        if Immd <> '':
            Self.RefTarget.Value = Self.Address + Immd * 4
            Self.RefTarget.Alias = 'immd'
            Self.RefTarget.Solved = True
        elif Label <> '':
            Self.RefTarget.Alias = Label #will be solved later
        else :
            #should never be here
            Logger.error('Syntax error: %s, no immediate.' %(Tokens))
            raise SyntaxError('no immediate')
        Self.Comment = Parser.Parse_Comment(Tokens[3:])
        if Self.Src1 == '' or Self.Src2 == '' or \
           Self.RefTarget.Alias == '' or \
           (not Tokens[3:] == [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor) :
        Self.Predicate = (Executor.Read_Reg(Self.Src1) 
                          == Executor.Read_Reg(Self.Src2))
        if Self.Opcode == 'bne' :
            Self.Predicate = Self.Predicate ^ 1
        return None, None, None
    def Adjust_IP(Self, Executor):
        if Self.Predicate :
            Executor.Jmpto_IP(Self.RefTarget.Value)
        else :
            Instruction.Adjust_IP(Self, Executor)
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Src1),
                           Self.Print_Reg(Self.Src2),
                           Self.RefTarget.Print(),
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Src1)),
                (None, ', '),#inc to 27
                ('Reg', Self.Print_Reg(Self.Src2)),
                (None, ', '),#inc to 32
                ('Label', '%s' % (Self.RefTarget.Print())), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class One_Reg_Immd(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 2 :
            return ''
        Self.Dest = Parser.Parse_Register(Tokens[0])
        Self.Src1 = Parser.Parse_Immediate(Tokens[1])
        Self.Comment = Parser.Parse_Comment(Tokens[2:])
        if Self.Dest == '' or Self.Src1 == '' or \
           (not Tokens[2:] == [] and Self.Comment == '') :
            return ''
        return Self
    def Exec(Self) :    # lui instruction
        Result = int(((Self.Src1 << 16) + 2**31) % 2**32 - 2**31)
        OldValue = Self.Write_Reg(Self.Dest, Result)
        return Result, OldValue
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Dest),
                           Self.Print_Reg(Self.Src1),
                           '',
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Dest)),
                (None, ', '), #inc to 27
                ('Immd', Self.Print_Immd(Self.Src1)), #inc to 40
                (None, ' '*5), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class One_Reg_Addr(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 2 :
            return ''
        Self.Data = Parser.Parse_Register(Tokens[0])
        Offset, Self.Reg = Parser.Parse_Address(Tokens[1])
        Self.RefTarget = Reference()
        Label,  Immd = Parser.Parse_Label_or_Immediate(Offset)
        if Immd <> '':
            Self.RefTarget.Value = Immd
            Self.RefTarget.Alias = 'immd'
            Self.RefTarget.Solved = True
        elif Label <> '':
            Self.RefTarget.Alias = Label #will be solved later
        else :
            Logger.error('Syntax error: %s, no immediate.' %(Tokens))
            raise SyntaxError('no immediate')
        Self.Comment = Parser.Parse_Comment(Tokens[2:])
        if Self.Data == '' or Self.RefTarget.Alias == '' or Self.Reg == '' or \
           (not Tokens[2:] == [] and Self.Comment == '') :
            return ''
        if Self.Opcode in ('lw', 'lb', 'lbu', 'llw') :
            Self.Dest = Self.Data
            Self.Src1 = Self.Reg
        if Self.Opcode in ('sw', 'sb', 'swc') :
            Self.Src1 = Self.Data
            Self.Src2 = Self.Reg
        return Self
    def ExecOn(Self, Executor) :
        Address = Executor.Read_Reg(Self.Reg) + Self.RefTarget.Value
        if Self.Opcode in ('lb', 'lbu') :   # lb, lbu instructions
            Shift = 8 * (Address % 4)
            Address &= -4
            Result = Executor.Read_Mem(Address)
            Result >>= Shift
            Result &= 255
            if Self.Opcode == 'lb' :
                Result = (Result + 128) % 256 - 128
            OldValue = Executor.Write_Reg(Self.Data, Result)
            return ('Reg', Self.Data), OldValue, Result
        if Self.Opcode == 'sb' :            # sb instruction
            Shift = 8 * (Address % 4)
            Address &=  -4
            OldValue = Executor.Read_Mem(Address)
            NewByte = Executor.Read_Reg(Self.Data) % 256
            Result = (OldValue & ((255 << Shift) ^ -1)) | NewByte << Shift
            Result = int((Result + 2**31) % 2**32 - 2**31)
            OldValue, NewValue = Executor.Write_Mem(Address, Result)
            return ('Mem', Address), OldValue, NewValue
        if Address % 4 <> 0 :
            Logger.error(
                'Effective Address = %d; '
                'memory addresses must be word aligned' % (Address))
            raise SyntaxError(
                'Memory addresses must be word aligned: %d' %(Address))
            Address &= -4
        if Self.Opcode == 'lw':        # lw instruction
            Result = Executor.Read_Mem(Address)
            OldValue = Executor.Write_Reg(Self.Data, Result)
            return ('Reg', Self.Data), OldValue, Result
        if Self.Opcode == 'sw':      # sw instruction
            Result = Executor.Read_Reg(Self.Data)
            OldValue, NewValue = Executor.Write_Mem(Address, Result)
            return ('Mem', Address), OldValue, NewValue
        if Self.Opcode == 'llw':
            Result = Executor.Read_Mem(Address, True)
            OldValue = Executor.Write_Reg(Self.Data, Result)
            return ('Reg', Self.Data), OldValue, Result
        if Self.Opcode == 'stcw':      # sw instruction
            Result = Executor.Read_Reg(Self.Data)
            OldValue, NewValue = Executor.Write_Mem(Address, Result, True)
            return ('Mem', Address), OldValue, NewValue
    def Print(Self):
        return '%4i %s %-5s $%02i, %s($%02i)     %s' % \
               (Self.Address, Self.Print_Label(Self.Label), 
                Self.Opcode, Self.Data,\
                Self.RefTarget.Print(), Self.Reg, Self.Comment)
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Reg(Self.Data),
                           Self.Print_Offset(Self.RefTarget.Print(), Self.Reg),
                           '',
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Reg', Self.Print_Reg(Self.Data)),
                (None, ', '), #inc to 27
                ('Immd', '%04i' % (Self.RefTarget.Value)), #inc to 31
                (None, '('), #inc to 32
                ('Reg', Self.Print_Reg(Self.Reg)),
                (None, ')'), #inc to 36
                (None, ' '*9), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class One_Label(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 1 :
            return ''
        Self.RefTarget = Reference()
        Self.RefTarget.Alias = Parser.Parse_Label_Ref(Tokens[0])
        Self.Comment = Parser.Parse_Comment(Tokens[1:])
        if Self.RefTarget.Alias == '' or \
           (not Tokens[1:] == [] and Self.Comment == ''):
            return ''
        return Self
    def ExecOn(Self, Executor) :
        if Self.Opcode == 'j' :         # j instruction
            return None, None, None
        elif Self.Opcode == 'jal' :     # jal instruction
            Result = Executor.Core.IP + 4
            OldValue = Executor.Write_Reg(31, Result)
            return ('Reg', 31), OldValue, Result
    def Adjust_IP(Self, Executor):
        Executor.Jmpto_IP(Self.RefTarget.Value)
    def Print(Self) :
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.RefTarget.Print(),
                           '', '',
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Label', '%s' %(Self.RefTarget.Print())), #inc to 35
                (None, ' '*10), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class One_Immd(Instruction) :
    def Parse(Self, Tokens, Parser) :
        if len(Tokens) < 1 :
            return ''
        Self.Src1 = Parser.Parse_Immediate(Tokens[0])
        Self.Comment = Parser.Parse_Comment(Tokens[1:])
        if Self.Src1 == '' or (Tokens[1:] <> [] and Self.Comment == '') :
            return ''
        return Self
    def ExecOn(Self, Executor) :                    # swi instruction
        if Executor.Known_Interrupt(Self.Src1) :
            return Executor.Handle_Interrupt(Self.Src1)
        else :
            Logger.error('%i is an undefined software interrupt.' %(Self.Src1))
            raise RuntimeError('undefined software interrupt.')
            return {}, {}
    def Print(Self) :
        return '%4i %s %-5s %i                %s' % \
               (Self.Address, Self.Print_Label(Self.Label), 
                Self.Opcode, Self.Dest, Self.Src1, Self.Comment)
        return Self.Format(Self.Address, Self.Label, Self.Opcode,
                           Self.Print_Immd(Self.Src1),
                           '', '',
                           Self.Comment)
    def Tagged_Print(Self) :
        return (('Address', Self.Print_Address(Self.Address)),
                (None, ' '), #inc to 5
                ('Label', Self.Print_Label(Self.Label)),
                (None, ' '), #inc to 16
                ('Opcode', Self.Print_Opcode(Self.Opcode)),
                (None, ' '), #inc to 22
                ('Immd', Self.Print_Immd(Self.Src1)), #inc to 35
                (None, ' '*10), #inc to 45
                ('Comment', '%s' % (Self.Comment)))

class Reference:
    def __init__(Self):
        Self.Solved = False
        Self.Alias = ''
        Self.Value = ''

    def Print(Self):
        Return = None
        if not Self.Solved:
            Return = '%s(unsolved)' %(Self.Alias)
        if Self.Alias == 'immd':
            Return = '%04i' %(Self.Value)
        else:
            Return = '%s(%04i)' %(Self.Alias, Self.Value)
        return Return.ljust(13)
