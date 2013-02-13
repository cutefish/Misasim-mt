# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

# Modified by Xiao Yu

from os import listdir
from random import seed, randint
from copy import copy

from Core import *
from Memory import *
from ExecArbitrator import *
from Logging import LogFactory
from Parser import *
from Tracer import *

Logger = LogFactory.getLogger('Simulation')

class Simulation :
    def __init__(Self, Parent=None) :
        Self.Parent = Parent
        Self.DataLabels = []  # cached for the benefit of the control flow analyzer
        Self.CodeBase = 1000
        Self.DataBase = Self.DataEnd = 5000 + (randint(0,250) * 4)
        Self.StackBase = 90000
        Self.StartingSP = 100000
        Self.ReturnIP = 3000 + (randint(0,250) * 4)
        Self.Cores = []
        Self.Mem = Memory()
        Self.Nav = Navigator()
        Self.NumCores = 2
        if Parent != None:
            Self.NumCores = Parent.NumCores
        for CoreID in range(Self.NumCores):
            Self.Cores.append(Core(CoreID, Self))
        Self.Mem.AddCores(Self.Cores)
        Self.Arbitrator = DefaultArbitrator()
        Self.Instructions = []
        Self.InitCommands = []
        Self.Restart()

    def Restart(Self) :
        """ This routine restores the simulation to the pre-execution state. """
        Self.Nav.Clear()
        for Core in Self.Cores:
            Core.Restart()
        Self.Mem.Clear()


    #def Goto_Start_of_Trace(Self) :
    #    """ This routine sets processor state and the navigator to the begining
    #    of the trace. """
    #    for Core in Self.Cores:
    #        Core.Restart()
    #    Self.Nav.Initialize()
    #    Self.Mem = Self.InitialMem.copy()

    #def Stack_Address(Self, Address) :
    #    """ Returns True if StackBase <= Address <= StartingSP, otherwise returns False."""
    #    return Self.StackBase <= Address <= Self.StartingSP

    def Load_Program(Self, InputFileStream):
        Parser = InstParser()
        Parser.Parse_Program(InputFileStream, Self.CodeBase)
        for Core in Self.Cores:
            Core.Load_Instructions(Parser.Instructions)
        Self.Instructions = Parser.Instructions
        Self.InitCommands = Parser.InitCommands
        Logger.info('Done parsing program')

    def Simulate(Self, ExeLimit=10000) :
        """ This routine executes a program """
        #init first
        Self.Init_Simulation()
        #execute instructions
        if not Self.Instructions:
            Logger.error('Instructions not loaded')
            return

        #make a shallow copy of the cores
        RunningCores = copy(Self.Cores)
        while ExeLimit > 0 and len(RunningCores) > 0:
            Core = Self.Arbitrator.select(RunningCores)
            Core.Next()
            if Core.Stopped():
                RunningCores.remove(Core)
            ExeLimit -= 1

        if ExeLimit <= 0 :
            Logger.warn('Stopped after %i instructions.  Infinite Loop?' % (
                len(Self.Nav.Trace)))
        #To do: check core status
        #elif Self.WECount >= WELimit :
        #    Self.Print_Warning('Stopped after %i instructions.  Too many warnings and errors' % (len(Self.Trace)))
        #elif I.Opcode <> 'jr' :
        #    Self.Print_Warning('Last executed instruction is %s rather than jr' % (I.Opcode))
        #elif not I.Src1 in Self.Regs or Self.Regs[I.Src1] <> Self.ReturnIP :
        #    Self.Print_Warning('return address not preserved (%d versus %d)' % (Self.Regs[I.Src1], Self.ReturnIP))
        #elif Self.Regs[29] <> Self.StartingSP :
        #    Self.Print_Warning('stack not maintained during execution (%d versus %d)' % (Self.Regs[29], Self.StartingSP))
        Logger.info('Done simulation')
        return 0

    def Report_Cores_State(Self):
        Ret = 'Cores: \n'
        for Core in Self.Cores:
            Ret += str(Core)
            Ret += '\n'
        return Ret

    def Report_Mem_State(Self):
        Ret = 'Mem: \n'
        Ret += str(Self.Mem)
        return Ret

    def Init_Simulation(Self):
        for Command, Offset, Len, Value in Self.InitCommands:
            if Command == 'memset':
                for Word in range(Len):
                    Self.Mem.Set(Offset + Word * 4, Value)

def Main (FileName='fact-mt', NumCores=2, ExecLimit=10000) :
    class FakeUI:
        def __init__(Self):
            Self.NumCores = NumCores
    UI = FakeUI()
    Sim = Simulation(UI)
    InputFile = open('%s.asm' % FileName, 'r')
    Sim.Load_Program(InputFile)
    Sim.Simulate(ExecLimit)
    print Sim.Report_Cores_State()
    print Sim.Report_Mem_State()
    #print
    #print Sim.Nav.Trace

import sys

if __name__ == '__main__':
    if len(sys.argv) > 3:
        Main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    elif len(sys.argv) > 2:
        Main(sys.argv[1], int(sys.argv[2]))
    elif len(sys.argv) > 1:
        Main(sys.argv[1])
    else:
        Main()

#def Program_Overlap (FileName='fact') :
#    Sim = Simulation()
#    InputFile = open('U:/scotty/classes/ece3035/Common Class Material/asm/%s.asm' % FileName, 'r')
#    #Sim.Parse_Program(InputFile)
#    for (i,j) in zip(Sim.Instructions, Sim.Instructions) :
#        print i.Opcode
#        print j.Opcode
#        print i.Opcode == j.Opcode
#    InputFile.close()
#    return Sim

