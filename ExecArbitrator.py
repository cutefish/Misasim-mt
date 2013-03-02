# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# Modification for multi-core by Xiao Yu, xyu40@gatech.edu

import random

class DefaultArbitrator:
    def __init__(Self):
        random.seed()

    def select(Self, Cores):
        return Cores[random.randrange(len(Cores))]

