# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Modification for multi-core by Xiao Yu, xyu40@gatech.edu


class Tracer(object):
    """Traces instruction execution. """
    def __init__(Self):
        Self.Trace = []

    def Clear(Self):
        Self.Trace = []

    def Append(Self, Update):
        Self.Trace.append(Update)

    def Compute_Exe_Stats(Self):
        raise NotImplementedError

    def HasTrace(Self):
        return Self.Trace != []

    #def Print_Exe_Stats(Self, Data=None) :
    #    """ This routine prints execution statistics. """
    #    if Data :
    #        StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData = Data
    #    else :
    #        StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData = Self.Compute_Exe_Stats()
    #    Logger.report('static I= %d, dynamic I= %d, reg data= %d, static data= %d, stack data= %d' %
    #                  (StaticI, DynamicI, RegData, StaticData, StackData))
    #    Results = ''
    #    SumCount = 0
    #    for Value in DynamicMix.values() :
    #        SumCount += Value
    #    for  Class, Count in DynamicMix.items() :
    #        Results += '%s: %2.1f%% ' % (Class, Count * 100.0 /SumCount)
    #    Self.Print_Message(Results)
    #
    #def Compute_Exe_Stats(Self) :
    #    """ This routine computes the static code length, dynamic code length, dynamic instruction
    #    mix, static memory used and stack memory used. """
    #    StaticI = len(Self.Instructions)
    #    DynamicI = len(Self.Trace)
    #    DynamicMix = {}
    #    for Instruction, Result, OldValue in Self.Trace :
    #        Op = Instruction.Opcode
    #        for Class, Opcodes in Opcode_Classes.items() :
    #            if Op in Opcodes :
    #                if Class in DynamicMix :
    #                    DynamicMix[Class] += 1
    #                else :
    #                    DynamicMix[Class] = 1
    #    SP = Self.StartingSP - 4
    #    while SP in Self.Mem :
    #        SP -= 4
    #    StackData = ((Self.StartingSP - 4) - SP) / 4
    #    StaticData = len(Self.Mem) - StackData
    #    RegData = len(Self.Regs) - 3
    #    if 'HiLo' in Self.Regs :
    #        RegData -= 1
    #    return [StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData]


