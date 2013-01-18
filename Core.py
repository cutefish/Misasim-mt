#MiSaSim-mt Core
#Written by Xiao Yu

from Simulator import SimLogger

class Core:
    Running = 1
    Idling = 2
    
    def __init__(Self, CoreID, Parent):
        Self.Regs = {0:0, 29:Parent.StratingSP, 31:Parent.ReturnIP}
        Self.CoreID = CoreID
        Self.CodeBase = Parent.CodeBase
        Self.IP = 0
        Self.Instructions = Parent.Instructions
        Self.Executor = InstExecutor(Self, Parent)
        Self.Mem = Parent.Mem #should be a memory agent, simplified here.
        Self.Max_Inst_Address = Self.Instructions[-1].Address
        Self.Status = Self.Running


    def Restart(Self):
        Self.IP = Parent.CodeBase
        Self.Regs = {0:0, 29:Self.StartingSP, 31:Self.ReturnIP}

    def NextStep(Self):
        if not (Self.CodeBase <= Self.IP <= Self.Max_Inst_Address):
            SimLogger.error("Invalid IP Address [%s] on Core [%s]" %(
                Self.IP, Self.CoreID))
        I = Self.Lookup_Instruction(Self.IP)
        if I:
            Result, OldValue = I.ExecOn(Self.Executor)
            Self.Executor.Inc_IP()
            SimLogger.traceInst(I, Result, OldValue)
            return 0
        else:
            SimLogger.error('Attempt to execute an invlaid IP %s' %(Self.IP))
            return -1
        if Self.IP == Self.Max_Inst_Address + 4:
            Self.Status = Self.Idling

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
            SimLogger.warning('HiLo read before defined')
            return 0, 0
        SimLogger.warning('$%02i read before defined' % RegNum)
        return 0

    def Write_Reg(Self, RegNum, Value) :
        """ This routine writes a register value. The replaced value is returned
        for the trace. A warning message is printed if a write to register zero
        is attempted. """
        if RegNum == 0 :
            SimLogger.error('$00 cannot be modified')
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
            SimLogger.warning('%i is a negative address' % (Address))
        if Address in Self.Core.Mem :
            return Self.Core.Mem[Address]
        SimLogger.warning('mem[%04i] read before defined' % (Address))
        return 0

    def Write_Mem(Self, Address, Value) :
        """ This routine writes a value to memory. The replaced value is returned
        for the trace. """
        if Address < 0 :
            SimLogger.warning('%i is a negative address' % (Address))
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



