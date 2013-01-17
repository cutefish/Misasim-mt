
MIPS_Opcodes = ['add', 'sub', 'addi', 'addu', 'subu', 'addiu', \
                'mult', 'multu', 'div', 'divu', 'mfhi', 'mflo', 'and', \
                'or', 'andi', 'ori', 'nor', 'xor', 'xori', 'sll', 'sllv', \
                'srl', 'srlv', 'sra', 'srav', 'lw', 'sw', 'lb', 'lbu', 'sb', \
                'lui', 'beq', 'bne', 'slt', 'slti', 'sltu', 'sltui', 'j', \
                'jr', 'jal', 'swi']

Directives = ['.data', '.text', '.alloc', '.word']

Three_Reg_Opcodes = ['add', 'sub', 'addu', 'subu', 'and', 'or', 'nor', 'xor', \
                     'sllv', 'srlv', 'srav', 'slt', 'sltu']

Two_Reg_Sex_Immd_Opcodes = ['addi', 'slti']

Two_Reg_Immd_Opcodes = ['addiu', 'andi', 'ori', 'xori', 'sll', 'srl', 'sra', 'sltiu']

Two_Reg_Opcodes = ['mult', 'multu', 'div', 'divu']

#Special instruction to put the core id into a register.
#this is to simplify the complex thread scheduling done by OS instead of
#injecting context switch code, we mimic it using a static one on one
#assignement of threads to core.
One_Reg_CoreID_Opcodes = ['coreid']

One_Reg_Opcodes = ['mfhi', 'mflo', 'jr']

One_Reg_Immd_Opcodes = ['lui']

One_Reg_Addr_Opcodes = ['sw', 'lw', 'lb', 'lbu', 'sb']

One_Label_Opcodes = ['j', 'jal']

Two_Reg_Label_Opcodes = ['beq', 'bne']

One_Immd_Opcodes = ['swi']

Opcode_Classes = {'Arith' : ('add', 'sub', 'addi', 'addu', 'subu', 'addiu', \
                             'mult', 'multu', 'div', 'divu', 'slt', 'slti', \
                             'sltu', 'sltui'),
                  'Logic' : ('and', 'or', 'andi', 'ori', 'nor', 'xor', 'xori'),
                  'Shift' : ('sll', 'sllv', 'srl', 'srlv', 'sra', 'srav'),
                  'Branch' : ('beq', 'bne'),
                  'Jump' : ('j', 'jr', 'jal', 'swi'),
                  'Load' :  ('lw', 'lb', 'lbu'),
                  'Store' : ('sw', 'sb'),
                  'Xfer' : ('mfhi', 'mflo', 'lui'),
                  'Spec' : ('coreid'),
                 }


