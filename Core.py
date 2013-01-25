#MiSaSim-mt Core
#Written by Xiao Yu

from Logging import RootLogger as Logger

class Core:
    Running = 1
    Done = 2
    Error = 3
    
    def __init__(Self, CoreID, Parent):
        Self.Regs = {0:0, 29:Parent.StratingSP, 31:Parent.ReturnIP}
        Self.CoreID = CoreID
        Self.CodeBase = Parent.CodeBase
        Self.Instructions = None
        Self.IP = 0
        Self.Executor = InstExecutor(Self, Parent)
        Self.Mem = Parent.Mem #should be a memory agent, simplified here.
        Self.Max_Inst_Address = Self.Instructions[-1].Address
        Self.Status = Self.Running


    def Restart(Self):
        Self.IP = Parent.CodeBase
        Self.Regs = {0:0, 29:Self.StartingSP, 31:Self.ReturnIP}

    def Next(Self):
        if not (Self.CodeBase <= Self.IP <= Self.Max_Inst_Address):
            Logger.error("Invalid IP Address [%s] on Core [%s]" %(
                Self.IP, Self.CoreID))
            Self.Status = Self.Error
            return
        I = Self.Lookup_Instruction(Self.IP)
        if I:
            try:
                Result, OldValue = I.ExecOn(Self.Executor)
                I.Adjust_IP(Self.Executor)
                #Logger.traceInst(I, Result, OldValue)
            except RuntimeError:
                Self.Status = Self.Error
                return
        else:
            Logger.error('Attempt to execute an invlaid IP %s' %(Self.IP))
            Self.Status = Self.Error
            return
        if Self.IP == Self.Max_Inst_Address + 4:
            Self.Status = Self.Done

    def Stopped(Self):
        return Self.Status != Self.Running

    def Done(Self):
        return Self.Status == Self.Done

    def HasError(Self):
        return Self.Status == Self.Error

    def Lookup_Instruction(Self, Address) :
        """ This routine looks up an instruction using an address. """
        Position = Self.Lookup_Instruction_Position(Address)
        if not Position == '':
            return Self.Instructions[Position]
        else :
            return None

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

class InstExecutor:
    def __init__(Self, Core):
        Self.Core = Core

    def Inc_IP(Self):
        Self.Core.IP += 4

    def Jmpto_IP(Self, IP):
        Self.Core.IP = IP

    def Read_Reg(Self, RegNum) :
        """ This routine returns a register value; a warning message is printed
        if the register has not been initialized. """
        if RegNum in Self.Core.Regs :
            return Core.Regs[RegNum]
        if RegNum == 'HiLo' :
            Logger.warn('HiLo read before defined')
            return 0, 0
        Logger.warn('$%02i read before defined' % RegNum)
        return 0

    def Write_Reg(Self, RegNum, Value) :
        """ This routine writes a register value. The replaced value is returned
        for the trace. A warning message is printed if a write to register zero
        is attempted. """
        if RegNum == 0 :
            Logger.error('$00 cannot be modified')
            raise RuntimeError('$00 cannot be modified')
            return 0
        if RegNum in Self.Core.Regs :
            OldValue = Self.Core.Regs[RegNum]
        else :
            OldValue = 'undefined'
        Self.Core.Regs[RegNum] = Value
        return OldValue

    def Unwrite_Reg(Self, RegNum, OldValue) :
        """ This routine undoes a register write. If the old value was undefined,
        the register entry is removed. """
        if OldValue == 'undefined' :
            del Self.Core.Regs[RegNum]
        else :
            Self.Core.Regs[RegNum] = OldValue

    def Read_Mem(Self, Address) :
        """ This routine returns a value from memory; a warning message is printed
        if the memory location has not been initialized. """
        if Address < 0 :
            Logger.error('%i is a negative address' % (Address))
            raise RuntimeError('Segmentation fault')
        if Address in Self.Core.Mem :
            return Self.Core.Mem[Address]
        Logger.warn('mem[%04i] read before defined' % (Address))
        return 0

    def Write_Mem(Self, Address, Value) :
        """ This routine writes a value to memory. The replaced value is returned
        for the trace. """
        if Address < 0 :
            Logger.error('%i is a negative address' % (Address))
            raise RuntimeError('Segmentation fault')
        if Address in Self.Core.Mem :
            OldValue = Self.Core.Mem[Address]
        else :
            OldValue = 'undefined'
        Self.Core.Mem[Address] = Value
        return OldValue

    def Unwrite_Mem(Self, Address, OldValue) :
        """ This routine undoes a memory write. If the old value was undefined,
        the memory entry is removed. """
        if OldValue == 'undefined' :
            del Self.Core.Mem[Address]
        else :
            Self.Core.Mem[Address] = OldValue

    def Handle_Interrupt(Self, Interrupt):
        """ This routine handles interrupt."""
        raise NotImplementedError("cannot handle interrupt now");

    def Known_Interrupt(Self, Interrupt):
        raise NotImplementedError("cannot handle interrupt now");



