# This program computes the factorial of the input in $1. The
# result is returned in $2.
# $1: n
# $2: running product (output n!)

Fact:   addi  $1, $0, 5         # input: n = 5
        addi  $2, $0, 1         # initialize output to 1
Loop:   slti  $3, $1, 2         # if input is less than 2
        bne   $3, $0, Skip      # then skip to return
        mult  $1, $2            # else multiply input and running product
        mflo  $2                # assume small numbers
        addi  $1, $1, -1        # decrement input
        j Loop                  # and loop
Skip:   jr    $31               # return to caller

