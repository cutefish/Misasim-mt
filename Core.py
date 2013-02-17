# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

# Modified by Xiao Yu

from Logging import LogFactory

Logger = LogFactory.getLogger('Core')

class Core:
    Running = 0
    Done = 1
    Error = 2
    STATUS_STRINGS = ['Running', 'Done', 'Error']
    
    def __init__(Self, CoreID, Sim):
        Self.StartingSP = Sim.StartingSP
        Self.ReturnIP = Sim.ReturnIP
        Self.NumCores = Sim.NumCores
        Self.Regs = {0:0, 29:Self.StartingSP, 31:Self.ReturnIP}
        Self.SpecRegs = {'Res':False, 'ResAddr':None}
        Self.CoreID = CoreID
        Self.Tracer = Sim.Nav
        Self.IP = 0
        Self.Executor = InstExecutor(Self)
        Self.Mem = Sim.Mem #To do: should be a cache controller.
        Self.Status = Self.Running
        Self.Code = None

    def Load_Code(Self, Code):
        Self.Code = Code
        Self.IP = Self.Code.CodeBase

    def Restart(Self):
        if Self.Code != None:
            Self.IP = Self.Code.CodeBase
        Self.Regs = {0:0, 29:Self.StartingSP, 31:Self.ReturnIP}

    def Next(Self):
        if not (Self.Code.Is_Valid_IP(Self.IP)):
            Logger.error("Invalid IP Address [%s] on Core [%s]" %(
                Self.IP, Self.CoreID))
            Self.Status = Self.Error
            return
        I = Self.Code.Lookup_Instruction(Self.IP)
        if I:
            try:
                Where, Old, New = I.ExecOn(Self.Executor)
                I.Adjust_IP(Self.Executor)
                Self.Tracer.Append((Self.CoreID, I.Address, Where, Old, New))
            except RuntimeError:
                Self.Status = Self.Error
                return
        else:
            Logger.error("Invalid IP Address [%s] on Core [%s]" %(
                Self.IP, Self.CoreID))
            Self.Status = Self.Error
            return
        if (not Self.Code.Is_Valid_IP(Self.IP) or 
            Self.IP == Self.ReturnIP):
            Self.Status = Self.Done

    def Stopped(Self):
        return Self.Status != Self.Running

    def HasError(Self):
        return Self.Status == Self.Error

    def Clear_Mem_Reserve(Self, Address):
        if (Self.SpecRegs['Res'] == True and
            Self.SpecRegs['ResAddr'] == Address):
            Self.SpecRegs['Res'] = False
            Self.SpecRegs['ResAddr'] = None

    def __str__(Self):
        Ret = 'Core('
        Ret += 'ID: %s' %Self.CoreID
        Ret += '; IP: %s' %Self.IP
        Ret += '; Status: %s' %Self.STATUS_STRINGS[Self.Status]
        Ret += '; Regs: [' 
        for RegNum, Value in Self.Regs.items():
            Ret += '$%s: %s' %(RegNum, Value)
            Ret += ', '
        Ret += ']; '
        Ret += ' SpecialRegs: ['
        for Name, Value in Self.SpecRegs.items():
            Ret += '$%s: %s' %(Name, Value)
            Ret += ', '
        Ret += '] '
        Ret += ')'
        return Ret

    #def Print_Regs(Self) :
    #    """ This routine prints all defined registers in the register file. """
    #    if 'HiLo' in Self.Regs :
    #        Self.Print_Message('HiLo = %i : %i' % Self.Regs['HiLo'])
    #    for RegNum in range(32) :
    #        if RegNum in Self.Regs :
    #            Self.Print_Message('$%02i = %8i' % (RegNum, Self.Regs[RegNum]))


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
            return Self.Core.Regs[RegNum]
        if RegNum == 'HiLo' :
            Logger.warn('Core %s: HiLo read before defined' %Self.Core.CoreID)
            return 0, 0
        Logger.warn('Core %s: $%02i read before defined' %(
            Self.Core.CoreID, RegNum))
        return 0

    def Write_Reg(Self, RegNum, Value) :
        """ This routine writes a register value. The replaced value is returned
        for the trace. A warning message is printed if a write to register zero
        is attempted. """
        if RegNum == 0 :
            Logger.error('Core %s; $00 cannot be modified' %Self.Core.CoreID)
            raise RuntimeError('$00 cannot be modified')
            return 0
        if RegNum in Self.Core.Regs :
            OldValue = Self.Core.Regs[RegNum]
        else :
            OldValue = 'undefined'
        Self.Core.Regs[RegNum] = Value
        return OldValue

    #def Unwrite_Reg(Self, RegNum, OldValue) :
    #    """ This routine undoes a register write. If the old value was undefined,
    #    the register entry is removed. """
    #    if OldValue == 'undefined' :
    #        del Self.Core.Regs[RegNum]
    #    else :
    #        Self.Core.Regs[RegNum] = OldValue

    def Read_Mem(Self, Address, Reserve=False) :
        """ This routine returns a value from memory; a warning message is printed
        if the memory location has not been initialized. """
        if Address < 0 :
            Logger.error('Core %s: %i is a negative address' % (
                Self.Core.CoreID, Address))
            raise RuntimeError('Segmentation fault')
        if Reserve == True:
            Self.Core.SpecRegs['Res'] = True
            Self.Core.SpecRegs['ResAddr'] = Address
        return Self.Core.Mem.Read(Address)

    def Write_Mem(Self, Address, Value, Reserve=False) :
        """ This routine writes a value to memory. The replaced value is returned
        for the trace. """
        if Address < 0 :
            Logger.error('Core %s: %i is a negative address' % (
                Self.Core.CoreID, Address))
            raise RuntimeError('Segmentation fault')
        if Reserve == True:
            #check reserve
            if Self.Core.SpecRegs['Res'] == False:
                Self.Core.Regs['HiLo'] = (0, 0)
                Old = Self.Core.Mem.Peek(Address)
                return Old, Old
            if Self.Core.SpecRegs['ResAddr'] != Address:
                Self.Core.Regs['HiLo'] = (0, 0)
                return Old, Old
            #still reserved
            Self.Core.Regs['HiLo'] = (1, 1)
        #actually write to the memory 
        Old = Self.Core.Mem.Write(Address, Value)
        return Old, Value

    #def Unwrite_Mem(Self, Address, OldValue) :
    #    """ This routine undoes a memory write. If the old value was undefined,
    #    the memory entry is removed. """
    #    if Self.NumCores > 1:
    #        raise NotImplementedError('Unwrite_Mem not yet supported in mt mode')
    #    Self.Core.Mem.Unwrite(Address, OldValue)

    def Handle_Interrupt(Self, Interrupt):
        """ This routine handles interrupt."""
        raise NotImplementedError("cannot handle interrupt now");

    def Known_Interrupt(Self, Interrupt):
        raise NotImplementedError("cannot handle interrupt now");



