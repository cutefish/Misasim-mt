# This program parallelly computes the summation of sequence 1 to n
# However, it does not work because of no atomic functionality support
#
# Use memory for synchronization. 
# Memory usage:
#  0x0000: current front element to add to the summation
#  0x0004: current summation
@memset 0x0000, 1, 100          # init memory: 0x0000 n = 100
@memset 0x0004, 1, 0            # init memory: 0x0004 sum = 0
Init:   addi  $10, $0, 10       # input: step = $10 = 10
Pull:   lw    $1,  0($0)        # load front value as subsum upper bound
        beq   $1,  $0, Ret      # if zero 
        sub   $2,  $1, $10      # subs the step to get subsum lower bound
        slt   $3,  $0, $2       # is lower bound greater than 0?
        bne   $3,  $0, Store    # if no, store
        add   $2,  $0, $0       # set lower bound to 0
Store:  sw    $2,  0($0)        # store the lower bound
        addi  $4,  $0, 0        # init subsum
Loop:   addi  $2,  $2, 1        # inc lower bound
        add   $4,  $4, $2       # add to subsum
        bne   $2,  $1, Loop     # if not reach upper bound, loop
Sum:    lw    $5,  4($0)        # load sum value
        add   $5,  $5, $4       # add subsum
        sw    $5,  4($0)        # store the subsum
        j     Pull              # ask for more work to do
Ret:    jr    $31
