# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Modification for multi-core by Xiao Yu, xyu40@gatech.edu

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
    def __init__(Self, 
                 CodeBase=1000, StackBase=90000, StartingSP=100000,
                 NumCores=2, Tracer=Tracer()):
        #Self.DataLabels = []  # cached for the benefit of the control flow analyzer
        #Self.DataBase = Self.DataEnd = 5000 + (randint(0,250) * 4)
        Self.CodeBase = CodeBase
        Self.StackBase = StackBase
        Self.StartingSP = StartingSP
        Self.ReturnIP = 3000 + (randint(0,250) * 4)
        Self.Cores = []
        Self.Mem = Memory()
        Self.InitMemImage = {}
        Self.Tracer = Tracer
        Self.NumCores = NumCores
        for CoreID in range(Self.NumCores):
            Self.Cores.append(Core(CoreID, Self))
        Self.Mem.AddCores(Self.Cores)
        Self.Arbitrator = DefaultArbitrator()
        Self.CodeLoaded = False
        Self.InitCommands = []
        Self.Restart()

    def Restart(Self) :
        """ This routine restores the simulation to the pre-execution state. """
        Self.Tracer.Clear()
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

    def Load_Code(Self, Code):
        for Core in Self.Cores:
            Core.Load_Code(Code)
        Self.InitCommands = Code.InitCommands
        Self.CodeLoaded = True

    def Simulate(Self, ExeLimit=10000) :
        """ This routine executes a program """
        #init first
        Self.Init_Simulation()
        #execute instructions
        if not Self.CodeLoaded:
            Logger.error('Code not loaded')
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
                len(Self.Tracer.Trace)))
        
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
        Self.Save_Init_Mem_Image()

    def Save_Init_Mem_Image(Self):
        Self.InitMemImage = Self.Mem.Data.copy()

    #for debug
    def Load_Program(Self, InputFileStream):
        Parser = InstParser()
        Code = Parser.Parse_Program(InputFileStream, Self.CodeBase)
        Self.Load_Code(Code)
        Logger.info('Done parsing program')

def Main (FileName='fact-mt', NumCores=2, ExecLimit=10000) :
    Sim = Simulation()
    InputFile = open('%s.asm' % FileName, 'r')
    Sim.Load_Program(InputFile)
    Sim.Simulate(ExecLimit)
    print Sim.Report_Cores_State()
    print Sim.Report_Mem_State()
    #print
    #print Sim.Tracer.Trace

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

