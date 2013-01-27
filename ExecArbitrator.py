import random

class DefaultArbitrator:
    def __init__(Self):
        random.seed()

    def select(Self, Cores):
        return Cores[random.randrange(len(Cores))]

