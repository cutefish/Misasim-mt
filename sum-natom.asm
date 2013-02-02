# This program parallelly computes the summation of sequence 1 to n
# $10: n
#
# Use memory for synchronization. 
# Memory usage:
#  0x0000: final Value
#  0x0004: core 1 compute range start
#  0x0008: core 1 compute range end
#  0x000C: core 1 compute sub sum
#  0x0010: core 2 compute range start
#  ...
@memset 0x0000, 24, 0           # init memory: 0x0000 - 0x005C 24 words for 8 cores
Init:   addi  $10, $0, 100      # input: n = 100
        cid   $11               # put id in 11
        nc    $12               # put number of cores in 12
        addi  $2, $0, 12        # shift = 12 = 3 word
        mult  $11, $2           # mem sync offset  = id * shift
        mflo  $13               # put offset into 13
        slt   $3, $0, $11       # if id larger than 0
        bne   $3, $0, Slave     # jmp to Slave
MInit:  div   $10, $12          # n / #cores
        mflo  $4                # quotient into 4
        mfhi  $5                # remainder into 5
        addi  $6, $0, 1         # sub sum range
        addi  $7, $12, 0        # core id number
        addi  $7, $7, -1        # core id number
        mult  $7, $2            # id * shift
        mflo  $7                # memory offset
Loop0:  sw    $6, 4($7)         # store range start
        add   $6, $6, $4        # add quotient
        slt   $3, $0, $5        # if still have remainder
        bne   $3, $0, WEnd      # then write range end
        addi  $6, $6, -1        # else decrement range end
WEnd:   addi  $7, $7, 4         # increment offset
        sw    $6, 4($7)         # store range end
        addi  $5, $5, -1        # decrement remainder
        addi  $6, $6, 1         # increment range start
        addi  $7, $7, -16       # decrement offset to next core
        slti  $3, $7, 0         # if address less than 0
        beq   $3, $0, Loop0     # not loop from Loop0
Slave:  addi  $13,$13, 4        # shift offset to range end
SWait:  lw    $8, 4($13)        # load range end into 8
        beq   $8, $0, SWait     # if range end is zero, jmp back
        addi  $1, $0, 0        # clear 1
        add   $1, $1, $8        # add range end into 1
        addi  $13,$13, -4       # shift offset to range start
        lw    $9, 4($13)        # load range start into 9
Sum:    addi  $8, $8, -1        # decrement element
        add   $1, $1, $8        # add into 1
        bne   $8, $9, Sum       # loop until reach range start
        addi  $13, $13, 8       # shift offset to value
        sw    $1, 4($13)        # write value 
        slt   $3, $0, $11       # if id larger than 0
        bne   $3, $0, Ret       # return
MWait:  and   $1, $1, $0        # clear 1 for final summation
        addi  $7, $12, 0        # core id number
        addi  $7, $7, -1        # core id number
        mult  $7, $2            # id * shift
        mflo  $7                # memory offset
        addi  $7, $7, 8         # value offset
Loop1:  lw    $8, 4($7)         # load value
        beq   $8, $0, MWait     # if value is zero, wait
        add   $1, $1, $8        # add into 1
        addi  $7, $7, -12       # shift offset
        slti  $3, $7, 0         # if offset less than 0
        beq   $3, $0, Loop1     # not loop from Loop1
        sw    $1, 0($0)         # write final result
Ret:    jr    $31
