from Logging import LogFactory

Logger = LogFactory.getLogger('Memory')

class Memory:
    """Memory Unit."""
    def __init__(Self):
        Self.Data = {} # Data is stored in the granularity of word
        Self.Cores = [] # To do: should be a list of cache controllers

    def AddCores(Self, Cores):
        Self.Cores = Cores

    def Peek(Self, Address):
        assert (Address % 4) == 0, 'Memory address not word aligned'
        if Address in Self.Data:
            return Self.Data[Address]
        return 'undefined'

    def Set(Self, Address, Value):
        assert (Address % 4) == 0, 'Memory address not word aligned'
        Self.Data[Address] = Value

    def Clear(Self):
        Self.Data.clear()

    def Read(Self, Address):
        assert (Address % 4) == 0, 'Memory address not word aligned'
        if Address in Self.Data:
            return Self.Data[Address]
        Logger.warn('mem[%04i] read before defined' % (Address))
        return 0

    def Write(Self, Address, Value):
        assert (Address % 4) == 0, 'Memory address not word aligned'
        if Address in Self.Data:
            OldValue = Self.Data[Address]
        else :
            OldValue = 'undefined'
        for Core in Self.Cores:
            Core.Clear_Mem_Reserve(Address)
        Self.Data[Address] = Value
        return OldValue

    #def Unwrite(Self, Address, OldValue):
    #    assert (Address % 4) == 0, 'Memory address not word aligned'
    #    if OldValue == 'undefined' :
    #        del Self.Data[Address]
    #    else :
    #        Self.Data[Address] = OldValue

    def __str__(Self):
        Ret = '{'
        for Addr in sorted(Self.Data):
            Value = Self.Data[Addr]
            Ret += '0x%04X: %s, ' %(Addr, Value)
        Ret += '}'
        return Ret

