# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Major modification for multi-core by Xiao Yu, xyu40@gatech.edu


MIPS_Opcodes = ['add', 'sub', 'addi', 'addu', 'subu', 'addiu', \
                'mult', 'multu', 'div', 'divu', 'mfhi', 'mflo', 'and', \
                'or', 'andi', 'ori', 'nor', 'xor', 'xori', 'sll', 'sllv', \
                'srl', 'srlv', 'sra', 'srav', 'lw', 'sw', 'lb', 'lbu', 'sb', \
                'lui', 'beq', 'bne', 'slt', 'slti', 'sltu', 'sltui', 'j', \
                'jr', 'jal', 'swi', 'cid', 'nc', 'llw', 'stcw']

Directives = ['.data', '.text', '.alloc', '.word']

Three_Reg_Opcodes = ['add', 'sub', 'addu', 'subu', 'and', 'or', 'nor', 'xor', \
                     'sllv', 'srlv', 'srav', 'slt', 'sltu']

Two_Reg_Sex_Immd_Opcodes = ['addi', 'slti']

Two_Reg_Immd_Opcodes = ['addiu', 'andi', 'ori', 'xori', 'sll', 'srl', 'sra', 'sltiu']

Two_Reg_Opcodes = ['mult', 'multu', 'div', 'divu']

One_Reg_Opcodes = ['mfhi', 'mflo', 'jr']

One_Reg_Immd_Opcodes = ['lui']

One_Reg_Addr_Opcodes = ['sw', 'lw', 'lb', 'lbu', 'sb', 'llw', 'stcw']

One_Label_Opcodes = ['j', 'jal']

Two_Reg_Label_Opcodes = ['beq', 'bne']

One_Immd_Opcodes = ['swi']

#Multi-thread instruction:

#put the core id into a register.
#this is to simplify the complex thread scheduling done by OS instead of
#injecting context switch code, we mimic it using a static one on one
#assignement of threads to core.
One_Reg_CoreID_Opcodes = ['cid']
One_Reg_NumCores_Opcodes = ['nc']
#llw and stcw


Opcode_Classes = {'Arith' : ('add', 'sub', 'addi', 'addu', 'subu', 'addiu', \
                             'mult', 'multu', 'div', 'divu', 'slt', 'slti', \
                             'sltu', 'sltui'),
                  'Logic' : ('and', 'or', 'andi', 'ori', 'nor', 'xor', 'xori'),
                  'Shift' : ('sll', 'sllv', 'srl', 'srlv', 'sra', 'srav'),
                  'Branch' : ('beq', 'bne'),
                  'Jump' : ('j', 'jr', 'jal', 'swi'),
                  'Load' :  ('lw', 'lb', 'lbu', 'llw'),
                  'Store' : ('sw', 'sb', 'stcw'),
                  'Xfer' : ('mfhi', 'mflo', 'lui'),
                  'MT' : ('cid', 'nc'),
                 }


def Add_Op (X, Y) :
    return X + Y

def Sub_Op (X, Y) :
    return X - Y

def And_Op (X, Y) :
    return X & Y

def Or_Op (X, Y) :
    return X | Y

def Xor_Op (X, Y) :
    return X ^ Y

def Nor_Op (X, Y) :
    return  ~(X | Y)

def Sll_Op (X, Y) :
    return  (X << (Y & 31))

def Sra_Op (X, Y) :
    return  X >> (Y & 31)

def Srl_Op (X, Y) :
    return  Sra_Op(X, Y) & (pow(2, 32 - (Y & 31)) - 1)

def Slt_Op (X, Y) :
    return (X < Y) & 1 or 0

def Mult_Op (X, Y) :
    """    Result = X * Y
    Lo = Result % pow(2, 32)
    Hi = (Result >> 32) & 0xffffffff """
    Lo = X * Y
    Hi = 0
    return (Hi, Lo)

def Div_Op (X, Y) :
    if Y == 0 :
        return (0, 0)
    Lo = X / Y
    Hi = X % Y
    return (Hi, Lo)

Op_Table = {'add': Add_Op, 'addi': Add_Op, 'addu': Add_Op, 'addiu': Add_Op, \
            'sub': Sub_Op, 'subu': Sub_Op, 'and': And_Op, 'andi': And_Op, \
            'or' : Or_Op, 'ori' : Or_Op, \
            'xor': Xor_Op, 'xori': Xor_Op, 'nor': Nor_Op, 'sll': Sll_Op, \
            'sllv': Sll_Op, 'srl': Srl_Op, 'srlv': Srl_Op, 'sra': Sra_Op, \
            'srav': Sra_Op, 'slt': Slt_Op, 'slti': Slt_Op, 'sltu': Slt_Op, \
            'sltui': Slt_Op, 'mult': Mult_Op, 'multu': Mult_Op, 'div': Div_Op, \
            'divu': Div_Op}


