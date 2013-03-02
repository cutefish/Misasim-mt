# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Modification for multi-core by Xiao Yu, xyu40@gatech.edu

import sys

class StdoutBackend:
    def Print_Message(Self, String):
        sys.stdout.write(String)

class Logger:
    def __init__(Self, Name):
        Self.Name = Name
        Self.Backend = StdoutBackend()
        
    def info(Self, Msg):
        InfoMsg = '[%s, %s] %s\n' %('INFO', Self.Name, Msg)
        Self.Backend.Print_Message(InfoMsg)

    def warn(Self, Msg):
        WarnMsg = '[%s, %s] %s\n' %('WARN', Self.Name, Msg)
        Self.Backend.Print_Message(WarnMsg)

    def error(Self, Msg):
        ErrorMsg = '[%s, %s] %s\n' %('ERROR', Self.Name, Msg)
        Self.Backend.Print_Message(ErrorMsg)

    def Config(Self, Backend=StdoutBackend()):
        Self.Backend = Backend

    def CopyConfig(Self, Other):
        Self.Backend = Other.Backend

RootLogger = Logger('')
Loggers = {'' : RootLogger}

class LogFactory:

    @classmethod
    def getLogger(Cls, Name):
        NewLogger = Logger(Name)
        NewLogger.CopyConfig(RootLogger)
        Loggers[Name] = NewLogger
        return NewLogger
