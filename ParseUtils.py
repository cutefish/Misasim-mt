

def Tokenize (Line) :
    """ This routine scans a list of space or comma delimited tokens with comments """
    Comment = []
    Line = Line.strip()                 # strip leading and trialing whitespace
    CN = Line.find('#')                 # find comment string
    if CN <> -1 :
        Comment = [Line[CN:]]           # create comment token
        Line = Line[:CN]                # remove comment from line
    return Line.replace(',', ' ').split() + Comment  # tokenize line with whitespace or comma

def Parse_Label_Def (String) :
    """ This routine parses a colon terminated alphnumeric label. It
    returns the valid label without the colon, or else it returns an
    empty string. """
    if String[-1] <> ':' :
        return ''
    Label = String[:-1]                 # strip colon
    if Label.isalnum() and Label[0].isalpha() :
        return Label
    return ''

def Parse_Label_Ref (String) :
    """ This routine parses an alphanumeric label. It returns the valid
    label, or else it returns an empty string. """
    if String.isalnum() and String[0].isalpha() :
        return String
    return ''

def Parse_Label_or_Immediate(String) :
    """ String is either a label reference or an integer.  Try to parse
    it as an immediate first. If it's an immediate, return ('', immediate).
    Otherwise, try to parse it as a label reference (i.e., as an
    alphanumberic label with at least its first character a letter) and
    return the tuple (label, ''). """
    Immediate = Parse_Immediate(String)
    Label = ''
    if Immediate == '' :
        Label = Parse_Label_Ref(String)
    return (Label, Immediate)

def Parse_Opcode (String) :
    """ This routine parses a MIPS opcode. It returns the validated
    opcode or else an empty string. """
    Opcode = String.lower()
    if Opcode in MIPS_Opcodes :
        return Opcode
    return ''

def Parse_Directive_Cmd (String) :
    """ This routine parses an assembler directive. It returns the validated
    directive or else an empty string. """
    Directive_Cmd = String.lower()
    if Directive_Cmd in Directives :
        return Directive_Cmd
    return ''

def Parse_Register (String) :
    """ This routine parses a register speicfied in '$x' where x is
    the register number. Register numbers must be between 0 and 31.
    An empty string is returned for an invalid string. """
    if String == '' or String[0] <> '$':
        return ''
    Number = String[1:]                 # strip '$'
    if not Number.isdigit() :
        return ''
    Number = int(Number)                # convert to integer
    if Number >= 0 and Number < 32 :    # valid register number?
        return Number
    return ''

def Parse_Immediate (String) :
    """ This routine parses an immediate integer string with optional
    + or - indicator and hexidecimal prefix '0x' or '0X'. It truncates
    to 16 bits and returns the unsigned integer value or and empty
    string on an error. """
    try :
        return int(String)
    except ValueError :
        try :
            if (len(String)>1 and String[0:2] in ['0x', '0X']) :
               return int(String, 16) & 65535
            else :
               return ''
        except ValueError :
            return ''

def Parse_Address (String) :
    """ This routine parses a register plus offset effective address.
    The register is group with paratheses (no space) and the offset
    preceedes the register. A offset and register list is returned.
    A bad parse returns an a list of empty strings. """
    Length = len(String)
    Index = 0
    while Index < Length and not String[Index] == '(' :
        Index += 1                      # skip offset
    if Index == Length :                # if nothing else, return error
        return ['','']
    OffsetString = String[:Index]       # isolate offset string
    if not String[-1] == ')' :          # if missing ), return error
        return ['','']
    RegisterString = String[Index+1:-1] # isolate register string
    Register = Parse_Register (RegisterString)
    if Register == '' :                 # if register parses badly, error
        return ['','']
    Offset = Parse_Immediate (OffsetString)
    if Offset == '' :
        Offset = Parse_Label_Ref (OffsetString)
        if Offset == '' :
            return ['','']
    return [Offset, Register]

def Parse_Comment (Tokens) :
    """ This routine parses and returns an optional comment token. The
    first character must be a '#'. Otherwise a null string is returned."""
    if Tokens <> [] and Tokens[0][0] == '#' :
        return Tokens[0]
    else :
        return ''

def Print_Label (String) :
    """ If string is non-null label, return padded with colon; else return
    padding only. """
    if String == '' :
        return ' ' * 10
    return '%s:%s' % (String, (9 - len(String)) * ' ')

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


