# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

# Modified by Xiao Yu

from Instructions import *
from Opcodes import *
from Logging import RootLogger as Logger

class InstParser:
    def __init__(Self):
        Self.Symbols = {}
        Self.Instructions = []

    def Tokenize (Self, Line) :
        """ This routine scans a list of space or comma delimited tokens with comments """
        Comment = []
        Line = Line.strip()                 # strip leading and trialing whitespace
        CN = Line.find('#')                 # find comment string
        if CN <> -1 :
            Comment = [Line[CN:]]           # create comment token
            Line = Line[:CN]                # remove comment from line
        return Line.replace(',', ' ').split() + Comment  # tokenize line with whitespace or comma

    def Parse_Label_Def (Self, String) :
        """ This routine parses a colon terminated alphnumeric label. It
        returns the valid label without the colon, or else it returns an
        empty string. """
        if String[-1] <> ':' :
            return ''
        Label = String[:-1]                 # strip colon
        if Label.isalnum() and Label[0].isalpha() :
            return Label
        return ''

    def Parse_Label_Ref (Self, String) :
        """ This routine parses an alphanumeric label. It returns the valid
        label, or else it returns an empty string. """
        if String.isalnum() and String[0].isalpha() :
            return String
        return ''

    def Parse_Label_or_Immediate(Self, String) :
        """ String is either a label reference or an integer.  Try to parse
        it as an immediate first. If it's an immediate, return ('', immediate).
        Otherwise, try to parse it as a label reference (i.e., as an
        alphanumberic label with at least its first character a letter) and
        return the tuple (label, ''). """
        Immediate = Self.Parse_Immediate(String)
        Label = ''
        if Immediate == '' :
            Label = Self.Parse_Label_Ref(String)
        return (Label, Immediate)

    def Parse_Opcode (Self, String) :
        """ This routine parses a MIPS opcode. It returns the validated
        opcode or else an empty string. """
        Opcode = String.lower()
        if Opcode in MIPS_Opcodes :
            return Opcode
        return ''

    def Parse_Directive_Cmd (Self, String) :
        """ This routine parses an assembler directive. It returns the validated
        directive or else an empty string. """
        Directive_Cmd = String.lower()
        if Directive_Cmd in Directives :
            return Directive_Cmd
        return ''

    def Parse_Register (Self, String) :
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

    def Parse_Immediate (Self, String) :
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

    def Parse_Address (Self, String) :
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
        Register = Self.Parse_Register (RegisterString)
        if Register == '' :                 # if register parses badly, error
            return ['','']
        Offset = Self.Parse_Immediate (OffsetString)
        if Offset == '' :
            Offset = Self.Parse_Label_Ref (OffsetString)
            if Offset == '' :
                return ['','']
        return [Offset, Register]

    def Parse_Comment (Self, Tokens) :
        """ This routine parses and returns an optional comment token. The
        first character must be a '#'. Otherwise a null string is returned."""
        if Tokens <> [] and Tokens[0][0] == '#' :
            return Tokens[0]
        else :
            return ''

    def Lookup_Label(Self, Label) :
        """ This routine looks up a label in the symbol table and returns the
        corresponding address. """
        if Label in Self.Symbols :
            return Self.Symbols[Label]
        else :
            Logger.error('Label %s has not been defined.' % (Label))
            return ''

    def Parse_Token_List (Self, Tokens, Address) :
        """ This routine determine the instruction format from the opcode
        and properly parses the token list.  """
        CommentOnly = Self.Parse_Comment(Tokens)
        if CommentOnly <> '' :
            return 'COMMENT'        # comment only line
        Label = Self.Parse_Label_Def(Tokens[0])
        if Label <> '' :
            Tokens = Tokens[1:]
        if len(Tokens) == 0 :
            Logger.warning('Label-only lines not permitted')
            return ''               # label only line (error)
        Directive_Cmd = Self.Parse_Directive_Cmd(Tokens[0])
        if Directive_Cmd <> '' :
            Self.Parse_Directive(Label, Directive_Cmd, Tokens[1:])
            return 'DIRECTIVE'      # directive line
        Opcode = Self.Parse_Opcode(Tokens[0])
        if Opcode == '' :
            return ''
        if Opcode in Three_Reg_Opcodes :
            I = Three_Reg(Opcode, Address)
        elif Opcode in Two_Reg_Sex_Immd_Opcodes :
            I = Two_Reg_Sex_Immd(Opcode, Address)
        elif Opcode in Two_Reg_Immd_Opcodes :
            I = Two_Reg_Immd(Opcode, Address)
        elif Opcode in One_Reg_Addr_Opcodes :
            I = One_Reg_Addr(Opcode, Address)
        elif Opcode in Two_Reg_Opcodes :
            I = Two_Reg(Opcode, Address)
        elif Opcode in One_Reg_Opcodes :
            I = One_Reg(Opcode, Address)
        elif Opcode in One_Reg_Immd_Opcodes :
            I = One_Reg_Immd(Opcode, Address)
        elif Opcode in One_Label_Opcodes :
            I = One_Label(Opcode, Address)
        elif Opcode in Two_Reg_Label_Opcodes :
            I = Two_Reg_Label(Opcode, Address)
        elif Opcode in One_Immd_Opcodes :
            I = One_Immd(Opcode, Address)
        elif Opcode in One_Reg_CoreID_Opcodes:
            I = One_Reg_CoreID(Opcode, Address)
        else :
            return ''
        I.Label = Label
        I = I.Parse(Tokens[1:], Self)
        return I

    def Parse_Directive(Self, Label, Directive_Cmd, Tokens) :
        """ If Directive_Cmd is .data or .text, do nothing, just doc.
        If it's .alloc, then take next integer (must be positive),
        multiply it by the word size and add to the current DataAddress.
        If it's .word, then take each integer in Tokens and add
        word size to DataAddress and initialize the word to the integer."""
        if Directive_Cmd not in ['.text', '.data'] :
            DataAddress = Self.DataEnd
            if Label != '' :
                if Self.Symbols.has_key(Label) and \
                   Self.Symbols[Label] <> DataAddress :
                    Logger.error('Label %s is associated with address %i and %i.' % \
                                     (Label, Self.Symbols[Label], DataAddress))
                else :
                    Self.DataLabels.append(Label)
                    Self.Symbols[Label] = DataAddress
            if Directive_Cmd == '.alloc' :
                New_DataEnd = Self.Parse_Alloc(Tokens)
            elif Directive_Cmd == '.word' :
                New_DataEnd = Self.Parse_Word(Tokens)
            else :
                Logger.warning('Unrecognized directive %s.' % (Directive_Cmd))
                New_DataEnd = Self.DataEnd  # no change
            Self.DataEnd = New_DataEnd

    def Parse_Alloc(Self, Tokens) :
        """ This parses a .alloc assembler directive.  Format:
        optional_label: .alloc <int>"""
        Num_Words = Parse_Immediate(Tokens[0])
        Comment = Parse_Comment(Tokens[1:])
        if (Num_Words == '') or not(Num_Words > 0) :
            Logger.error('.alloc %s must be an integer > 0' % (Num_Words))
        elif (not Tokens[1:] == [] and Comment == ''):
            Logger.warning('text following .alloc is being ignored.')
        else :
            Self.DataEnd = Self.DataEnd + (Num_Words * 4) # word size
        return Self.DataEnd

    def Parse_Word(Self, Tokens) :
        """ This parses a .word assembler directive.  Format:
        optional_label: .word <int>, <int>,..., <int> """
        for Token in Tokens :
            DataValue = Parse_Immediate(Token)
            if DataValue == '' :
                break
#                Self.Print_Warning('.word must be followed only by integers: %s' % (Token))
            else :
                Self.InitialMem[Self.DataEnd] = DataValue
                Self.Mem[Self.DataEnd] = DataValue
                Self.DataEnd += 4
        return Self.DataEnd

    def Solve_Labels(Self) :
        """ This checks that all labels that are referenced (as
        an immediate, branch/jump or call target) are in the symbol table
        and if not prints an error message. """
        NumErrors = 0
        for I in Self.Instructions :
            if hasattr(I, 'RefTarget'):
                Ref = I.RefTarget
                if Ref.Solved == True:
                    continue
                if Ref.Alias == '':
                    continue #no label set
                try:
                    I.RefTarget.Value = Self.Symbols[Ref.Alias]
                    I.RefTarget.Solved = True
                except KeyError:
                    NumErrors += 1
                    Logger.error('%s is referenced, but not defined.' % Ref.Alias)
        return NumErrors

    def Assign_Op_Functions(Self) :
        """ This routine assigned the appropriate operation function to each
        instruction in list. """
        for I in Self.Instructions :
            I.Op = Op_Table.get(I.Opcode, 'undefined')

    def Parse_Program (Self, InputFile, CodeBase) :
        """ This routine reads, tokenizes, and parses the program file. This is
        called from the User Interface when Load command is given."""
        Address = CodeBase             # define base IP
        LineNum = 0                         # line number (for error reports)
        for Line in InputFile :
            LineNum += 1
            Tokens = Self.Tokenize (Line)
            if Tokens :
                I = Self.Parse_Token_List(Tokens, Address)
                if I == '' :
                   Logger.error("Error in line #%03i: '%s'" % (LineNum, Line[0:-1]))
                elif not I in ['COMMENT', 'DIRECTIVE'] :
                    Address += 4
                    Self.Instructions.append(I)
                    if not I.Label == '' :
                        if Self.Symbols.has_key(I.Label) and \
                           Self.Symbols[I.Label] <> I.Address :
                            Logger.error("Label %s is associated with address %i and %i" %  \
                                             (I.Label, Self.Symbols[I.Label], I.Address))
                        Self.Symbols[I.Label] = I.Address
        Self.Solve_Labels()
        Self.Assign_Op_Functions()

def Main(FileName='fact-mt'):
    InputFile = open('%s.asm' %FileName, 'r')
    Parser = InstParser()
    Parser.Parse_Program(InputFile, 1000)
    for I in Parser.Instructions:
        print I

import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        Main(sys.argv[1])
    else:
        Main()
