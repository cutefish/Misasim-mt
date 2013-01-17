# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills

from Simulator import *

Loop_Colors = ['skyblue', 'mistyrose','indianred', 'yellowgreen' \
               'yellowgreen', 'orange', 'turquoise', 'yellow', 'green']

Color_Index = 0

class Analysis :
    def __init__(Self, Simulation) :
        Self.Sim = Simulation
        Self.CFGs = {}
        Self.Removed_Joins = []  # for bookkeeping and checking whether all labels are reached.

    def Find_BB_w_Inst(Self, Address) :
        for CFG in Self.CFGs.values() :
            BB = CFG.Find_BB_Containing(Address)
            if BB :
                return BB
        return ''
    def Create_CFGs(Self, Instructions, Symbols):
        """ This first partitions Instructions into subsequences of instructions that belong to
	separate subroutines.  It then takes each subsequence and creates a CFG for it and adds
	it to the CFGs dictionary indexed by the label of the first instruction in the subsequence.
	This assumes that all subroutines (including the topmost -- e.g., Main) have a labeled first
	instruction."""
        Subsequences = {}
        Current_Subsequence = []
        First_Label = None
        for I in Instructions :
            if not First_Label :
                if I.Label == '' :
                    First_Label = '__Top%i__' % (I.Address)
                    print 'Error: First instruction %s in subroutine must have a label. Temporarily using %s' % (I, First_Label)
                else :
                    First_Label = I.Label
            Current_Subsequence.append(I)
            if I.Opcode == 'jr' :
                Subsequences[First_Label] = Current_Subsequence
                Current_Subsequence = []
                First_Label = None
        for Label_Subsequence_Pair in Subsequences.items() :   # (Label, Instruction_Sequence)
            New_CFG = CFG(Self)
            Self.CFGs[Label_Subsequence_Pair[0]] = New_CFG
            New_CFG.Create_CFG(Label_Subsequence_Pair[1], Symbols)

        """Print a warning if Symbols contains any Labels that are not Data labels, or
        called as subroutines, branched to or jumped to."""
        for (Label, Address) in Symbols.items() :
            Label_Used = Self.Check_Labels(Label, Address)
            if not Label_Used :
                print 'Warning: Label %s (Address %i) is not reached within this program.' % \
                      (Label, Address)

    def Check_Labels(Self, Label, Address) :
        """ This routine might be unnecessary now that Error_Check_Labels has
        been added to the Simulator."""
        if Label in Self.Sim.DataLabels :
            return True
        for J in Self.Removed_Joins :
            if J.Label == Label :
                return True
        for (Subrt_Label, CFG) in Self.CFGs.items() : 
            if Subrt_Label == Label :
                return True
            elif (CFG.Joins.has_key(Address)) :      # check whether there is a Join associated with Address
                return True
        return False

class Basic_Block :
    def __init__(Self, Starting_IP) :
        Self.Node_Type = 'BB'
        Self.Addr = Starting_IP
        Self.Ending_Addr = 0      # this is changed as instructions are added.  If it's 0, the BB is empty.
        Self.In = None
        Self.Out = None
        Self.Loop = None          # innermost loop that contains node
    def __repr__(Self) :
        return '[BB %i : %i]' % (Self.Addr, Self.Ending_Addr)
    def Add_Instruction(Self, Instruction) :
        Self.Ending_Addr = Instruction.Address
    def Member_Instruction(Self, Address) :
        if Address >= Self.Addr and Address <= Self.Ending_Addr :
            return True
        else : return False
    def Connect_In(Self, Source) :
        Self.In = Source
    def Connect_Out(Self, Target) :
        Self.Out = Target
    def Reconnect_Out(Self, Old_Target, New_Target) :
        if Old_Target == Self.Out :
            Self.Out = New_Target
        else :
            print 'Error: %s is not connected to %s' % (Self, Old_Target)
    def Reconnect_In(Self, Old_Source, New_Source) :
        Self.In = New_Source
    def Dot_Node_Label(Self) :
        return "B%i_%i" % (Self.Addr, Self.Ending_Addr)
    def Dot_Node_Shape(Self) :
        return 'box'
     
class Join :
    def __init__(Self, IP, Label) :
        Self.Node_Type = 'Join'
        Self.Addr = IP
        Self.Label = Label
        Self.Ins = []
        Self.Out = None
        Self.Loop = None          # innermost loop that contains node
    def __repr__(Self) :
        return '[J %i %s]' % (Self.Addr, Self.Label)
    def Connect_In(Self, Source) :
        Self.Ins.append(Source)
    def Connect_Out(Self, Target) :
        Self.Out = Target
    def Reconnect_Out(Self, Old_Target, New_Target) :
        if Old_Target == Selt.Out :
            Self.Out = New_Target
        else :
            print 'Error: %s is not connected to %s' % (Self, Old_Target)
    def Reconnect_In(Self, Old_Source, New_Source) :
        Self.In = New_Source
    def Reconnect_In(Self, Old_Source, New_Source) :
        New_Inputs = [New_Source]
        for Input in Self.Ins :
            if not (Old_Source == Input) :
                New_Inputs.append(Input)
        Self.Ins = New_Inputs
    def Dot_Node_Label(Self) :
        return "J%i%s" % (Self.Addr, Self.Label)
    def Dot_Node_Shape(Self) :
        return 'invtriangle'

class Split :
    def __init__(Self, IP, Condition, Target_Label) :
        Self.Node_Type = 'Split'
        Self.Addr = IP
        Self.Condition = Condition
        Self.Target = Target_Label
        Self.In = None
        Self.T_Out = None
        Self.F_Out = None
        Self.Loop = None          # innermost loop that contains node
    def __repr__(Self) :
        return '[S %i %s %s]' % (Self.Addr, Self.Condition, Self.Target)
    def Connect_In(Self, Source) :
        Self.In = Source
    def Connect_from_T(Self, True_Target) :
        Self.T_Out = True_Target
    def Connect_from_F(Self, False_Target) :
        Self.F_Out = False_Target
    def Reconnect_In(Self, Old_Source, New_Source) :
        Self.In = New_Source
    def Reconnect_Out(Self, Old_Target, New_Target) :
        if (Self.T_Out == Old_Target) :
            Self.T_Out = New_Target
        elif (Self.F_Out == Old_Target) :
            Self.F_Out = New_Target
        else :
            print 'Error: %s is not connected to %s' % (Self, Old_Target)
    def Dot_Node_Label(Self) :
        return "S%i%s" % (Self.Addr, Self.Condition)
    def Dot_Node_Shape(Self) :
        return 'diamond'

class Call :
    def __init__(Self, IP, Subroutine_Name) :
        Self.Node_Type = 'Call'
        Self.Addr = IP
        Self.Subroutine_Name = Subroutine_Name
        Self.In = None
        Self.Out = None
        Self.Loop = None          # innermost loop that contains node
    def __repr__(Self) :
        return '[Call %i %s]' % (Self.Addr, Self.Subroutine_Name)
    def Connect_In(Self, Source) :
        Self.In = Source
    def Connect_Out(Self, Target) :
        Self.Out = Target
    def Reconnect_In(Self, Old_Source, New_Source) :
        Self.In = New_Source
    def Reconnect_Out(Self, Old_Target, New_Target) :
        if Old_Target == Selt.Out :
            Self.Out = New_Target
        else :
            print 'Error: %s is not connected to %s' % (Self, Old_Target)
    def Dot_Node_Label(Self) :
        return "C%i%s" % (Self.Addr, Self.Subroutine_Name)
    def Dot_Node_Shape(Self) :
        return 'octagon'

class Loop :
    def __init__(Self, Join, Back_Edge_Sources) :
        Self.Join = Join
        Self.Back_Edge_Sources = Back_Edge_Sources # typically there is only 1
        Self.Starting_Address = Join.Addr
        Self.Back_Address = Max_Back_Edge(Back_Edge_Sources)
        Self.Body_Nodes = []
        Self.Dot_Color = Self.Assign_Color()
    def __repr__(Self) :
        return '[Loop %i %i]' % (Self.Starting_Address, Self.Back_Address)
    def Assign_Color(Self) :
        global Color_Index
        Color = Loop_Colors[Color_Index]
        Color_Index = (Color_Index + 1) % len(Loop_Colors)
        return Color
    def Am_I_Inside(Self, Loop) :
        """Return True if Self is nested within Loop.  Otherwise return False."""
        Self_Start = Self.Starting_Address
        Loop_Start = Loop.Starting_Address
        Self_End = Self.Back_Address
        Loop_End = Loop.Back_Address
        if Loop_Start < Self_Start and Self_End < Loop_End :
            return True
        else : return False
    def Am_I_Outside(Self, Loop) :
        """Return True if Loop is nested within Self.  Otherwise return False."""
        return Loop.Am_I_Inside(Self)
 
def Max_Back_Edge(Back_Edge_Sources) :
    max = 0
    for Source in Back_Edge_Sources :
        if Source.Node_Type == 'BB' :
            Address = Source.Ending_Addr
        else : Address = Source.Addr
        if Address > max :
            max = Address
    return max

def Lookup_Target_Address(I, Symbols) :
    Label = I.Target
    if (Symbols.has_key(Label)) :
        Target_Address = Symbols[Label]
    else :
        print 'Error in %s instruction at address %i: Target not found %s' % \
              (I.Opcode, I.Address, I.Target)
        Target_Address = 0
    return Target_Address

class CFG :
    def __init__(Self, Analysis) :
        Self.BBs = []       # basic blocks
        Self.Joins = {}     # Join nodes (merging of cflow) -- a dictionary indexed by target address
        Self.Splits = []    # Split nodes (branching of cflow)
        Self.Calls = []     # subroutine call nodes
        Self.Loops = []     # loops
        Self.Nesting = []   # list of (inner-loop, outer-loop) pairs
        Self.Current_BB = None
        Self.Starting_Addr = 0  # entry IP of first node
        Self.Ending_Addr = 0    # exit IP of last node
        Self.Starting_Node = None # first node in CFG
        Self.Analysis = Analysis
    def __repr__(Self) :
        return '[CFG %i: %i]' % (Self.Starting_Addr, Self.Ending_Addr)
    def Add_BB(Self, BB) :
        Self.BBs.append(BB)
    def Add_Join(Self, Join) :
        Self.Joins[Join.Addr] = Join
    def Lookup_Join(Self, Target_Addr) :
        if (Self.Joins.has_key(Target_Addr)) :
            return Self.Joins[Target_Addr]
    def Add_Split(Self, Split) :
        Self.Splits.append(Split)
    def Add_Call(Self, Call) :
        Self.Calls.append(Call)
    def End_Block(Self, BB) :
        """ Call this only when BB has been fully connected into the CFG.  If the
        Ending_Addr = 0, then the BB is empty (no instructions have been added) and
        the BB should be removed from the CFG.  This means reconnecting the source
        of its input to the target of its output."""
        if BB.Ending_Addr == 0 :  
            Self.Splice_Out_BB(BB)
        Self.Current_BB = None

    def Find_BB_Containing(Self, Address) :
        """ Find the Basic Block containing instruction Address and return it.
        If there is no such BB, return ''."""
        for BB in Self.BBs :
            if BB.Member_Instruction(Address) :
                return BB
        return ''
        
    def Splice_Out_BB(Self, BB) :
        """ Reroute the source of BB's input to the target of its output.  Remove BB from
        the CFG's BBs. Target will be a Join, since it's the only way to get an empty BB --
        with a labeled instruction following a split or call; all other types of fall thru
        instructions are added to the BB.  Source might be a split."""
        Source = BB.In
        Target = BB.Out
        if not (Target.Node_Type == 'Join') :
            print 'Warning: Empty basic block %s is not connected to a Join, but %s.' % (BB, Target)
        # update the source to target links
        if Target :
            Source.Reconnect_Out(BB, Target)
        # update the target to source links
        if Source :
            Target.Reconnect_In(BB, Source)

        # remove BB from CFG
        New_BBs = []
        for Block in Self.BBs :
            if not (BB == Block) :
                New_BBs.append(Block)
        Self.BBs = New_BBs

        BB.In = None
        BB.Out = None
        print 'Empty basic block %s has been spliced out of %s.' % (BB, Self)  # debugging -- remove later

    def Splice_Out_J(Self, Join) :
        """ This is used when Join has only 1 input.  Reroute the source of
        its single input to the target of its ouput.  Remove Join from
        the CFG's BBs."""
        if len(Join.Ins) > 1 :
            print 'Error: Trying to remove Join %s with > 1 input: %s' % \
                  (Join, Join.Ins)
        else :
            if Join.Ins : 
                Source = Join.Ins[0]
            else : Source = None
            Target = Join.Out
            if Target :
                # if Join is the Starting_Node of the CFG then replace Starting_Node with Target
                if (Join == Self.Starting_Node) :
                    Self.Starting_Node = Target
                # update the source to target links
                Source.Reconnect_Out(Join, Target)
            if Source :
                # update the target to source links
                Target.Reconnect_In(Join, Source)
        # remove Join from CFG
        del Self.Joins[Join.Addr]
        Join.Ins = []
        Join.Out = None
        Self.Analysis.Removed_Joins.append(Join)
        print 'Join %s has been spliced out of %s.' % (Join, Self)  # debugging -- remove later

    def Record_Starting_Node(Self, Node) :
        if not Self.Starting_Node :
            Self.Starting_Node = Node
    def Add_Target_Joins(Self, Instructions, Symbols) :
        """ Create a Join node for each target branched to from a beq/bne/j.  If a bne/beq
        uses a numerical offset, compute branch target address and create a join corresponding
        to it; if there is a label at that BTA, use it, o.w., set Label = None.  If a symbolic
        label is used, lookup the Address of the target in Symbols and use it as the Join's Addr.
        Note: This just creates Join nodes and records them in the CFG.  It doesn't connect
        them to anything."""
        for I in Instructions :
            if I.Opcode in ['beq', 'bne', 'j'] :
                if I.Target == '' :
                    if I.Opcode == 'j' :
                        print 'Error in J instruction at address %i: no symbolic target.' % \
                              (I.Address)
                    Target_Address = I.Address + 4 + (I.Offset * 4)
                    Label = None
                    for Entry in Symbols.items() :      # Entry = (Label, Address)
                        if Entry[1] == Target_Address :
                            Label = Entry[0]
                else :
                    Target_Address = Lookup_Target_Address(I, Symbols)
                    Label = I.Target
                J = Join(Target_Address, Label)
                Self.Add_Join(J)

    def Insert_Join(Self, Join, Instruction) :
        """ Instruction is a labeled instruction which is a target of some branch/jump.
            Splice Join into the CFG: if there is a current BB, connect its output to
            Join as one of its inputs and end the current BB.  If Join's output is not
            already connected to a basic block, then create a new BB and connect it to
            Join's output.  The current BB becomes the BB connected to the output of
            the Join.  Note that the Join can never be connected to a Split or Call
            Node (only a BB) because beq/bne/j/jal are always the last instruction in a
            BB that is then connected to a Split or Call node."""
        Current_BB = Self.Current_BB
        if Current_BB :
            Current_BB.Connect_Out(Join)
            Join.Connect_In(Current_BB)
            Self.End_Block(Current_BB)
        if not Join.Out :
            BB = Basic_Block(Instruction.Address)
            Self.Add_BB(BB)
            Join.Connect_Out(BB)
            BB.Connect_In(Join)
        # The current BB becomes the BB connected to Join's output.
        Self.Current_BB = Join.Out

    def Insert_Split(Self, Instruction, Symbols) :
        """ Instruction is a branch.  Create a Split node and connect its input to the output
        of the current BB.  End the current BB.
        True Output: Compute the branch target address from Instruction's Target or Offset and
        look up the corresponding Join.  Connect the Split's T output to the Join as one of its
        inputs.
        False Output (fall through case): Create a new Fall_Thru BB starting at IP+4. Connect
        Split's F output to the new BB's input."""
        Current_BB = Self.Current_BB
        S = Split(Instruction.Address, Instruction.Opcode, Instruction.Target)
        Self.Add_Split(S)
        S.Connect_In(Current_BB)
        Current_BB.Connect_Out(S)
        Self.End_Block(Current_BB)

        # True Output

        if Instruction.Target == '' :
            Target_Address = Instruction.Address + 4 + (Instruction.Offset * 4)
        else :
            Target_Address = Lookup_Target_Address(Instruction, Symbols)
        J = Self.Lookup_Join(Target_Address)
        S.Connect_from_T(J)
        J.Connect_In(S)
        
        # False Output (fall through)

        New_BB = Self.Insert_Fall_Thru_BB(Instruction.Address + 4)
        S.Connect_from_F(New_BB)
        New_BB.Connect_In(S)

    def Insert_Call(Self, Instruction) :
        """ Instruction is a jal. Create a Call node and connect its input to the output of the current
        BB.  End the current BB.  Create a new Fall_Thru BB starting at IP+4. Connect the Call node's
        output to the new BB's input."""
        Current_BB = Self.Current_BB
        C = Call(Instruction.Address, Instruction.Target)
        Self.Add_Call(C)
        C.Connect_In(Current_BB)
        Current_BB.Connect_Out(C)
        
        Self.End_Block(Current_BB)
        New_BB = Self.Insert_Fall_Thru_BB(Instruction.Address+4)
        C.Connect_Out(New_BB)
        New_BB.Connect_In(C)

    def Insert_Fall_Thru_BB(Self, Fall_Thru_IP) :
        """ Create a new basic block and make it the current BB.  Starting
        Address should be Fall_Thru_IP.  This BB starts right after a branch (false case) or
        right after a jal.  This basic block might end up being empty (e.g., if
        the fall through instruction is a labeled instruction (join)).  This empty BB will be
        spliced out by End_Block since its ending address will be 0 (no instructions have been
        inserted). 
        """
        New_BB = Basic_Block(Fall_Thru_IP)
        Self.Add_BB(New_BB)
        Self.Current_BB = New_BB
        return New_BB
                
    def Create_CFG(Self, Instructions, Symbols) :
        """ This walks through the Instructions and creates a control flow graph.
        It assumes (for now) that the Instructions are for a single subroutine; they
        do not include instructions for any of the subroutines called from Instructions.
        Finally, clean up the graph."""
        Self.Starting_Addr = Instructions[0].Address
        Self.Ending_Addr = Instructions[-1].Address
        Self.Add_Target_Joins(Instructions, Symbols)

        for I in Instructions :
            # if I is a branch/jump target, lookup corresponding Join J (if there is no join, do nothing)
            J = Self.Lookup_Join(I.Address)
            if J :
                Self.Insert_Join(J, I)
                Self.Record_Starting_Node(J)    # record if this is the first
                
            # do the following whether or not the instruction has a label:

            # if there is no current BB, make a new one and add I to it.
            if not Self.Current_BB :
                BB = Basic_Block(I.Address)
                Self.Add_BB(BB)
                Self.Current_BB = BB
            Self.Current_BB.Add_Instruction(I)          # add I to Current BB
            Self.Record_Starting_Node(Self.Current_BB)  # record if this is the first
            
            # depending on what type of instruction I is, insert the appropriate nodes

            if (I.Opcode in '[beq, bne]') :
                Self.Insert_Split(I, Symbols)
            elif (I.Opcode == 'j') :
                Target_Address = Lookup_Target_Address(I, Symbols)
                J = Self.Lookup_Join(Target_Address)
                Self.Current_BB.Connect_Out(J)
                J.Connect_In(Self.Current_BB)
                Self.End_Block(Self.Current_BB)
            elif (I.Opcode == 'jal') :
                Self.Insert_Call(I)
            elif (I.Opcode == 'jr') :
                Self.End_Block(Self.Current_BB)
            # otherwise, do nothing.
        Self.Cleanup()
        Self.Find_Loops()

    def Cleanup(Self) :
        """ Remove any joins that have <= 1 input."""
        for Join in Self.Joins.values() :
            if len(Join.Ins) < 2 :
                Self.Splice_Out_J(Join)

    def Find_Loops(Self) :
        """ For each join, look for all inputs that are coming from an address that is greater
        than the join's address (these are back edges).  Starting at each source of a back
        edge, traverse the nodes upward (in the reverse direction of control flow) until you
        hit the join.  All nodes traversed are recorded as part of the loop associated with
        this join (starting address = join's address; ending address = max address of back
        edge sources.  Also record nesting relationships and for each CFG node that
        is in a loop, record the innermost loop that contains it to the node's Loop attribute."""
        for Join in Self.Joins.values() :
            Back_Edge_Sources = []
            for Source in Join.Ins :
                if Source.Addr > Join.Addr :
                    Back_Edge_Sources.append(Source)
            if Back_Edge_Sources :
                L = Loop(Join, Back_Edge_Sources)
                Self.Loops.append(L)
                Nodes_Visited = []
                Traverse_Up_from_Nodes(Back_Edge_Sources, Nodes_Visited, Join)
                L.Body_Nodes = Nodes_Visited
        Self.Determine_Loop_Nesting()
        Self.Record_Loops_in_Body_Nodes()

    def Determine_Loop_Nesting(Self) :
        """ Compute nesting relationships between Loops in CFG and record
        them as (Inner, Outer) pairs in the CFG.Nesting attribute."""
        for Loop in Self.Loops :
            for Other_Loop in Self.Loops :
                if not Loop == Other_Loop :
                    if Loop.Am_I_Inside(Other_Loop) :
                        Self.Nesting.append((Loop, Other_Loop))
                        
    def Nested_P(Self, Loop1, Loop2) :
        """Return True if Loop1 is nested in Loop2 in CFG.Nesting; Else False."""
        if (Loop1, Loop2) in Self.Nesting :
            return True
        else : return False

    def Record_Loops_in_Body_Nodes(Self) :
        """ For each loop L, take each of its body nodes.  If the node's
        Loop attribute is None or if the node already has a Loop recorded and L is
        inside the recorded loop attribute, replace node's Loop attribute with L."""
        for L in Self.Loops :
            for Node in L.Body_Nodes :
                Recorded_Loop = Node.Loop
                if (not Recorded_Loop) or Self.Nested_P(L, Recorded_Loop) :
                    Node.Loop = L
                
    def All_Nodes(Self) :
        Nodes = []
        for BB in Self.BBs :
            Nodes.append(BB)
        for C in Self.Calls :
            Nodes.append(C)
        for S in Self.Splits :
            Nodes.append(S)
        for J in Self.Joins.items() :
            Nodes.append(J[1])
        return Nodes

    def Collate_Edges(Self) :
        """ Traverse the CFG from Starting_Node, print out edges.  Keep track of nodes traversed.
        Warn about any nodes that are not included in the edges reached.  These may represent
        dead code."""
        Pending_Nodes = []
        Nodes_Visited = []
        Edges = []
        Pending_Nodes.append(Self.Starting_Node)
        Nodes_Visited, Edges = Traverse_Down_from_Nodes(Pending_Nodes, Nodes_Visited, Edges)
        Warn_Nodes_Not_Visited(Nodes_Visited, Self.All_Nodes())
        return (Edges, Nodes_Visited)

    def Create_Dot_File(Self, Name) :
        """ Collate edges and send them (along with nodes visited) to
        Write_Dot_File."""
        Edges, Nodes_Visited = Self.Collate_Edges()
        Write_Dot_File(Edges, Nodes_Visited, Self.Loops, Name)

def Write_Dot_File(Edges, Nodes_Visited, Loops, FileName='output') :
    OutputFile = open('//Maple/users/Scotty/PROGRAMS/Python/MiSaSiM/asm/dot/%s.dot' % FileName, 'w')
    OutputFile.write('digraph %s {\n    size="6,6";\n' % FileName)
    for N in Nodes_Visited :
        if N.Loop :
            OutputFile.write('%s [shape = %s,style=filled,color="%s"];\n' % \
                             (N.Dot_Node_Label(), N.Dot_Node_Shape(), \
                              N.Loop.Dot_Color))
        else :
            OutputFile.write('%s [shape = %s];\n' % \
                             (N.Dot_Node_Label(), N.Dot_Node_Shape()))
    for Edge in Edges :
        Source = Edge[0]
        Sink = Edge[1]
        if len(Edge) > 2 :  # Are there attributes on the edge?  Use the first as a label.
            OutputFile.write('%s -> %s [label="%s"];\n' % \
                             (Source.Dot_Node_Label(), Sink.Dot_Node_Label(),Edge[2]))
        else : 
            OutputFile.write('%s -> %s;\n' % (Source.Dot_Node_Label(), Sink.Dot_Node_Label()))
    OutputFile.write('}')
    OutputFile.close()

def Create_Dot_Files(Analysis) :
    """ Create a dot file for each CFG, name the file by the cfg's label
    (the label of the first instruction in the cfg) and store the dot file
    in the //Maple/users/Scotty/PROGRAMS/Python/asm/dot/ directory.
    Note that this will overwrite previous files of the same name."""
    for CFG_Entry in Analysis.CFGs.items() :
        CFG_Entry[1].Create_Dot_File(CFG_Entry[0])

def Traverse_Down_from_Nodes(Pending_Nodes, Nodes_Visited, Edges) :
    """ Pending_Nodes is a list of the nodes in a CFG that still need
    to be traversed.  When it is empty, return the Nodes_Visited and Edges.
    Otherwise, take the first pending node and if it hasn't already been
    visited, add entries to Edges showing the output edge(s) from the
    current node to its output sinks.  Add the output sinks to Pending_Nodes.
    Add the current node to Nodes_Visited."""
    while Pending_Nodes :
        Current_Node = Pending_Nodes.pop()
        if not (Current_Node in Nodes_Visited) :
            if Current_Node.Node_Type == 'Split' :
                SinkT = Current_Node.T_Out
                SinkF = Current_Node.F_Out
                if SinkT :
                    Edges.append((Current_Node, SinkT, 'T'))
                    Pending_Nodes.append(SinkT)
                if SinkF :
                    Edges.append((Current_Node, SinkF, 'F'))
                    Pending_Nodes.append(SinkF)
            elif Current_Node.Out :
                Edges.append((Current_Node, Current_Node.Out))
                Pending_Nodes.append(Current_Node.Out)
            Nodes_Visited.append(Current_Node)
    return (Nodes_Visited, Edges)

def Warn_Nodes_Not_Visited(Nodes_Visited, All_Nodes) :
    """ All_Nodes is a list of all nodes in a CFG.  Check that they have
    all been visited (are members of Nodes_Visited).  Print a warning
    for any nodes in CFG that have not been visited. """
    for n in All_Nodes :
        if not (n in Nodes_Visited) :
            print 'Warning: CFG node %s is not reached.' % (n)

def Traverse_Up_from_Nodes(Pending_Nodes, Nodes_Visited, Stop_Node) :
    """ Pending_Nodes is a list of the nodes in a CFG that still need
    to be traversed.  When it is empty, return.
    Otherwise, take the first pending node and if it hasn't already been
    visited and it's not Stop_Node, add the input sources to Pending_Nodes.
    Add the current node to Nodes_Visited."""
    while Pending_Nodes :
        Current_Node = Pending_Nodes.pop()
        if not (Current_Node in Nodes_Visited) :
            if (not (Current_Node == Stop_Node)) :
                if Current_Node.Node_Type == 'Join' :
                    Pending_Nodes.extend(Current_Node.Ins)
                elif Current_Node.In :
                    Pending_Nodes.append(Current_Node.In)
            Nodes_Visited.append(Current_Node)

def Analyze(Sim) :
    Ana = Analysis(Sim)
    # Create Control Flow Graphs
    Ana.Create_CFGs(Sim.Instructions, Sim.Symbols)
    return Ana

