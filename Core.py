#MiSaSim-mt Core
#Written by Xiao Yu

class Core:
    def __init__(Self, CoreID, Parent):
        Self.Regs = {0:0, 29:Parent.StratingSP, 31:Parent.ReturnIP}
        Self.CoreID = CoreID
        Self.IP = 0
        Self.Executor = InstrExecutor(Self, Parent)
        Self.Mem = Parent.Mem


    def Restart(Self):
        Self.IP = Parent.CodeBase
        Self.Regs = {0:0, 29:Self.StartingSP, 31:Self.ReturnIP}

class InstrExecutor:
    def __init__(Self, Core, Listener):
        Self.Core = Core
        Self.Listener = Listener

    def Inc_IP(Self):
        Self.Core.IP += 4

    def Read_Reg(Self, RegNum) :
        """ This routine returns a register value; a warning message is printed
        if the register has not been initialized. """
        if RegNum in Self.Core.Regs :
            return Core.Regs[RegNum]
        if RegNum == 'HiLo' :
            Self.Listener.warning('HiLo read before defined')
            return 0, 0
        Self.Listener.warning('$%02i read before defined' % RegNum)
        return 0

    def Write_Reg(Self, RegNum, Value) :
        """ This routine writes a register value. The replaced value is returned
        for the trace. A warning message is printed if a write to register zero
        is attempted. """
        if RegNum == 0 :
            Self.Listener.error('$00 cannot be modified')
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
            Self.Listener.warning('%i is a negative address' % (Address))
        if Address in Self.Core.Mem :
            return Self.Core.Mem[Address]
        Self.Listener.warning('mem[%04i] read before defined' % (Address))
        return 0

    def Write_Mem(Self, Address, Value) :
        """ This routine writes a value to memory. The replaced value is returned
        for the trace. """
        if Address < 0 :
            Self.Listener.warning('%i is a negative address' % (Address))
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



