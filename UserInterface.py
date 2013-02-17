# MiSaSiM MIPS ISA Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
#
# 27 January 2005:  (Dan Ordille) added hotkeys, enhanced main memu bar,
#                   proper text widget
# 22 August 2009:   added hexidecimal display support, fixed a few bugs
# 12 January 2010:  added init file
# 20 February 2011: added HiLo to register list
# 18 March 2011:    fixed some memory leaks; repaired in update_mods

import os
import copy

from Tkinter        import *
from tkFileDialog   import *
from tkMessageBox   import *
from Simulator      import *
from Code import *
from Navigator import *

appPath = os.getcwd()

######################### MiSaSim Window #########################

class MiSaSiM(Tk) :
    def __init__(Self, Version) :
        Tk.__init__(Self)
        Self.Version = Version
        Self.title('MiSaSiM %.2f(mt)' % Version)

        # MiSaSim environment variables
        Self.ExeLimit = 500000
        Self.RepRate = 1
        Self.FontSize = 10
        Self.FontFace = 'normal'
        Self.ButtonMode = 'icon+name'
        Self.DisplayBase = 10
        Self.NumCores = 1

        # load options parameters if options init file exists
        Self.Load_Init_File()

        # init simulation and navigator
        Self.Sim = Simulation(Self)
        Self.Nav = 

        # current core info display
        Self.CurrCore = 0
        Self.CoreIDSetters = []
        for CoreID in range(Self.NumCores):
            def Setter():
                Self.CurrCore = CoreID
                Self.MenuView.Refresh()
                Self.RegView.Refresh()
                Self.CodeView.Refresh()
            Self.CoreIDSetters.append(Setter)

        # make panes
        Self.MessageView = MessagePane(Self)
        Self.CodeView = CodePane(Self)
        Self.TraceView = TracePane(Self)
        Self.RegView = RegPane(Self)
        Self.DataView = MemoryPane(Self)
        Self.StackView = MemoryPane(Self)
        Self.MenuView = MenuPane(Self)

        # set grid geometry
        Self.MenuView.grid(row=0, column=0, sticky=NSEW, columnspan=3, ipady=2)
        Self.CodeView.grid(row=1, column=0, sticky=NSEW)
        Self.DataView.grid(row=1, column=1, sticky=NSEW)
        Self.StackView.grid(row=1, column=2, stick=NSEW)
        Self.TraceView.grid(row=2, column=0, sticky=NSEW)
        Self.RegView.grid(row=2, column=1, sticky=NSEW, rowspan=2, columnspan=2)
        Self.MessageView.grid(row=3, column=0, sticky=NSEW)

        # set grid resizing attributes
        Self.rowconfigure(0, weight=0)
        Self.rowconfigure(1, weight=1)
        Self.rowconfigure(2, weight=1)
        Self.rowconfigure(3, weight=1)
        Self.columnconfigure(0, weight=1)
        Self.columnconfigure(1, weight=0)
        Self.columnconfigure(2, weight=0)

        # set shortcut keys
        Self.bind_class(Self, '<Control-l>', Self.CodeView.Load)
        Self.bind_class(Self, '<Control-r>', Self.CodeView.Reload)
        Self.bind_class(Self, '<Control-x>', Self.Execute)
        Self.bind_class(Self, '<Control-d>', Self.Dump)
        Self.bind_class(Self, '<Control-t>', Self.Restart)
        Self.bind_class(Self, '<Control-m>', Self.MultiExec)
        Self.bind_class(Self, '<Control-e>', Self.Goto_End)
        Self.bind_class(Self, '<Control-n>', Self.Next)
        Self.bind_class(Self, '<Control-b>', Self.Backward)
        Self.bind_class(Self, '<Control-f>', Self.Forward)
        Self.bind_class(Self, '<Control-p>', Self.Prev)
        Self.bind_class(Self, '<Control-s>', Self.Goto_Start)
        Self.bind_class(Self, '<Control-g>', Self.Goto_Addr)
        Self.bind_class(Self, '<Control-c>', Self.Copy)
        Self.bind_class(Self, '<Control-o>', Self.Options)
        Self.bind_class(Self, '<Control-q>', Self.Exit)
        Self.bind_class(Self, '<Control-y>', Self.Seed)

        # create top menubar
        Self.menubar = Menu(Self, relief=RAISED)
        Self.TopFileMenu() 
        Self.TopEditMenu()
        Self.TopTraceMenu()
        Self.TopHelpMenu()
        Self.config(menu=Self.menubar)

        Self.MenuView.Refresh()

    def TopFileMenu(Self) :
        filemenu = Menu(Self.menubar, tearoff=0, relief=RAISED)
        Self.menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Load", underline=0, accelerator = 'Ctrl-L', command=Self.CodeView.Load)
        filemenu.add_command(label="Reload", underline=0, accelerator = 'Ctrl-R', command=Self.CodeView.Reload)
        filemenu.add_command(label="Execute", underline=1, accelerator = 'Ctrl-X', command=Self.Execute)
        filemenu.add_command(label="Restart", underline=3, accelerator = 'Ctrl-T', command=Self.Restart)
        filemenu.add_command(label="MultiExec", underline=0, accelerator = 'Ctrl-M', command=Self.MultiExec)
        filemenu.add_separator()
        filemenu.add_command(label="Dump", underline=0, accelerator = 'Ctrl-D', command=Self.Dump)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", accelerator = 'Ctrl-Q', command=Self.quit)
        
    def TopEditMenu(Self) :
        editmenu = Menu(Self.menubar, tearoff=0, relief=RAISED)
        editmenu.add_command(label="Options", underline=0, accelerator = 'Ctrl-O', command=Self.Options)
        Self.menubar.add_cascade(label="Edit", menu=editmenu)
        
    def TopTraceMenu(Self) :
        TraceMenu = Menu(Self.menubar, tearoff=0)
        TraceMenu.add_command(label="Trace Start", underline=6, accelerator = 'Ctrl-S', command=Self.Goto_Start)
        TraceMenu.add_command(label="Trace End", underline=6, accelerator = 'Ctrl-E', command=Self.Goto_End)
        TraceMenu.add_separator()
        TraceMenu.add_command(label="Previous", underline=0, accelerator = 'Ctrl-P', command=Self.Prev)
        TraceMenu.add_command(label="Next", underline=0, accelerator = 'Ctrl-N', command=Self.Next)
        TraceMenu.add_separator()
        TraceMenu.add_command(label="Backward", underline=0, accelerator = 'Ctrl-B', command=Self.Backward)
        TraceMenu.add_command(label="Forward", underline=0, accelerator = 'Ctrl-F', command=Self.Forward)
        Self.menubar.add_cascade(label="Trace", menu=TraceMenu)

    def TopHelpMenu(Self) :
        helpmenu = Menu(Self.menubar, tearoff=0, relief=RAISED)
        helpmenu.add_command(label="About", command=Self.MenuView.About)
        helpmenu.add_command(label="Help", command=Self.MenuView.notdone)
        Self.menubar.add_cascade(label="Help", menu=helpmenu)

    def MultiExec(Self, Event=None) :
        """ This routine queries for a repeat value. It then execute the program
        multiple times (as specified) and returns the summary statistics. """
        MultiExecWin = Toplevel()
        MultiExecWin.title('MultiExecution')
        RepRateScale = Scale(MultiExecWin, label='Enter number of executions', from_=1, to=100, orient='horizontal', length=400)
        RepRateScale.pack(expand=YES, fill=X)
        ButtonFrame = Frame(MultiExecWin)
        ButtonFrame.pack(side=TOP, fill=X)
        OKButton= Button(ButtonFrame, text='OK', command=lambda: Self.Set_Rep_Rate(RepRateScale, MultiExecWin))
        OKButton.pack(side=RIGHT, expand=YES, fill=X)
        CancelButton = Button(ButtonFrame, text='Cancel', command=MultiExecWin.destroy)
        CancelButton.pack(side=RIGHT, expand=YES, fill=X)

    def Set_Rep_Rate(Self, Scale, Win) :
        """ This callback routine sets the rep rate for executions. The executions
        are then performed and the reprate is reset to one."""
        Self.RepRate = Scale.get()
        Win.destroy()
        Self.Execute()
        Self.RepRate = 1

    def Execute(Self, Event=None) :
        """ This routine executes the program and initilaizes all views."""
        if not Self.Sim.Instructions == [] :
            if not Self.Sim.Trace == [] :
                Self.Restart()
            SumDynamicI = 0.0
            SumStackData = 0.0
            SumDynamicMix = None
            for N in range(Self.RepRate) :
                if N <> 0 :
                    Self.Sim.Restart()
                Self.Sim.Simulate(Self.ExeLimit)
                StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData = Self.Sim.Compute_Exe_Stats()
                SumDynamicI += DynamicI
                SumStackData += StackData
                if SumDynamicMix :
                    for  Class, Count in DynamicMix.items() :
                        #SumDynamicMix[Class] += Count  # BugFix Fall 2011
                        if Class in SumDynamicMix :
                            SumDynamicMix[Class] += Count
                        else :
                            SumDynamicMix[Class] = Count
                else :
                    SumDynamicMix = DynamicMix
            DynamicI = SumDynamicI / Self.RepRate
            StackData = SumStackData / Self.RepRate
            Self.Sim.Print_Exe_Stats((StaticI, DynamicI, DynamicMix, RegData, StaticData, StackData))
            Self.Sim.Goto_Start_of_Trace()
            Self.TraceView.Refresh()
            Self.RegView.Refresh()
            DataAddresses, StackAddresses = Self.DataView.Collect_Sorted_Addresses()
            Self.DataView.Refresh(DataAddresses)
            Self.StackView.Refresh(StackAddresses)

    def Restart(Self, Event=None) :
        """ This routine restarts the simulation and refreshes all affected
        views. """
        Self.Sim.Restart()
        Self.TraceView.Refresh()
        Self.RegView.Refresh()
        DataAddresses, StackAddresses = Self.DataView.Collect_Sorted_Addresses()
        Self.DataView.Refresh(DataAddresses)
        Self.StackView.Refresh(StackAddresses)
        Self.CodeView.Refresh()
        Self.MenuView.Refresh()

    def Clear(Self, Event=None) :
        """ This routine clears the simulator, clearing and initializing all
        views. """
        Self.Sim = Simulation(Self)
        Self.MenuView.Refresh()
        Self.CodeView.Refresh()
        Self.TraceView.Refresh()
        Self.MessageView.Refresh()
        Self.RegView.Refresh()
        DataAddresses, StackAddresses = Self.DataView.Collect_Sorted_Addresses()
        Self.DataView.Refresh(DataAddresses)
        Self.StackView.Refresh(StackAddresses)

    def Options(Self, Event=None) :
        """ This routine displays and updates simulator parameters. """
        OptionsForm = Toplevel()
        OptionsForm.title('Options')

        ExeLimit = StringVar()
        ExeLimit.set(str(Self.ExeLimit))
        ExeLimitFrame = Frame(OptionsForm)
        ExeLimitLabel = Label(ExeLimitFrame, text='max execution', width=15)
        ExeLimitEntry = Entry(ExeLimitFrame)
        ExeLimitEntry.config(textvariable=ExeLimit)
        ExeLimitFrame.pack(side=TOP, fill=X)
        ExeLimitLabel.pack(side=LEFT)
        ExeLimitEntry.pack(side=RIGHT, expand=YES, fill=X)

        FontSize = IntVar()
        FontSize.set(Self.FontSize)
        FontSizeFrame = Frame(OptionsForm)
        FontSizeFrame.pack(side=TOP, fill=X)
        FontSizeLabel = Label(FontSizeFrame, text='font size', width=15)
        FontSizeLabel.pack(side=LEFT)
        for Size in (8, 10, 11, 12, 14, 16, 18) :
            FontSizeEntry = Radiobutton(FontSizeFrame, text=str(Size), variable=FontSize, value=Size)
            FontSizeEntry.pack(side=LEFT)

        FontFace = StringVar()
        FontFace.set(Self.FontFace)
        FontFaceFrame = Frame(OptionsForm)
        FontFaceFrame.pack(side=TOP, fill=X)
        FontFaceLabel = Label(FontFaceFrame, text='font face', width=15)
        FontFaceLabel.pack(side=LEFT)
        for Face in ('normal', 'bold', 'italic') :
            FontFaceEntry = Radiobutton(FontFaceFrame, text=Face, variable=FontFace, value=Face)
            FontFaceEntry.pack(side=LEFT)

        ButtonMode = StringVar()
        ButtonMode.set(Self.ButtonMode)
        ButtonModeFrame = Frame(OptionsForm)
        ButtonModeFrame.pack(side=TOP, fill=X)
        ButtonModeLabel = Label(ButtonModeFrame, text='button mode', width=15)
        ButtonModeLabel.pack(side=LEFT)
        for Mode in ('icon', 'name', 'icon+name') :
            ButtonModeEntry = Radiobutton(ButtonModeFrame, text=Mode, variable=ButtonMode, value=Mode)
            ButtonModeEntry.pack(side=LEFT)

        DisplayBase = IntVar()
        DisplayBase.set(Self.DisplayBase)
        DisplayBaseFrame = Frame(OptionsForm)
        DisplayBaseFrame.pack(side=TOP, fill=X)
        DisplayBaseLabel = Label(DisplayBaseFrame, text='display base', width=15)
        DisplayBaseLabel.pack(side=LEFT)
        for Text, Base in (("decimal", 10), ("hexidecimal", 16)) :
            DisplayBaseEntry = Radiobutton(DisplayBaseFrame, text=Text, variable=DisplayBase, value=Base)
            DisplayBaseEntry.pack(side=LEFT)

        OptionsVars = (ExeLimit, FontSize, FontFace, ButtonMode, DisplayBase)
        ButtonFrame = Frame(OptionsForm)
        ButtonFrame.pack(side=TOP, fill=X)
        OKButton = Button(ButtonFrame, text='OK', command=(lambda Vars=OptionsVars,
                                                           Win=OptionsForm:
                                                           Self.Update_Options(Vars, Win)))
        OKButton.pack(side=LEFT, expand=YES, fill=X)
        CancelButton = Button(ButtonFrame, text='Cancel', command=OptionsForm.destroy)
        CancelButton.pack(side=RIGHT, expand=YES, fill=X)

    def Update_Options(Self, Vars, Window) :
        """ This routine collects the results of the options command and updates
        all the the information. """
        NewExeLimit = int(Vars[0].get())
        if 0 < NewExeLimit :
            Self.ExeLimit = NewExeLimit
        NewFontSize = int(Vars[1].get())
        if Self.FontSize <> NewFontSize :
            Self.FontSize = NewFontSize
            Self.Update_Display_Fonts()
        NewFontFace = Vars[2].get()
        if Self.FontFace <> NewFontFace :
            Self.FontFace = NewFontFace
            Self.Update_Display_Fonts()
        NewButtonMode = Vars[3].get()
        if Self.ButtonMode <> NewButtonMode :
            Self.ButtonMode = NewButtonMode
            Self.MenuView.DestroyMenuIP()
            Self.MenuView.BuildMenu(Self)
            Self.MenuView.BuildIP(Self)
        NewDisplayBase = Vars[4].get()
        if Self.DisplayBase <> NewDisplayBase :
            Self.DisplayBase = NewDisplayBase
            Self.RegView.Refresh()
            DataAddresses, StackAddresses = Self.DataView.Collect_Sorted_Addresses()
            Self.DataView.Refresh(DataAddresses)
            Self.StackView.Refresh(StackAddresses)
        Window.destroy()
        Self.Store_Init_File()

    def Update_Display_Fonts(Self) :
        """ This routine updates display fonts in all text views. """
        Self.MenuView.IP.config(font=('courier', Self.FontSize, Self.FontFace))
        Self.CodeView.Code.config(font=('courier', Self.FontSize, Self.FontFace))
        Self.TraceView.Trace.config(font=('courier', Self.FontSize, Self.FontFace))
        for Name in range(32) :
            Self.RegView.Labels[Name].config(font=('courier', Self.FontSize, Self.FontFace))
        Self.DataView.Mem.config(font=('courier', Self.FontSize, Self.FontFace))
        Self.StackView.Mem.config(font=('courier', Self.FontSize, Self.FontFace))
        Self.MessageView.Msgs.config(font=('courier', Self.FontSize, Self.FontFace))

    def Load_Init_File(Self) :
        """ This routine loads the current options settings to the options.ini file
        (if it exists). """
        Path = os.getcwd()
        if "options.ini" in os.listdir(Path) :
            File = open(Path + "/options.ini", 'r')
            for Line in File.readlines() :
                Line = Line.strip()
                if len(Line) > 0 and ':' in Line :
                    I = Line.find(':')
                    Keyword = Line[:I]
                    Value = Line[I+2:]
                    exec("Self.%s = %s" % (Keyword, Value))
            File.close()

    def Store_Init_File(Self) :
        """ This routine saves the current options settings to the options.ini file
        in the bin directory. """
        FileName = os.getcwd() + "/options.ini"
        try :
            File = open(FileName, 'w')
        except :
            showerror('MiSaSiM', 'Could not store options init file ' + FileName)
        else :
            File.write("<MaSaSiM version %1.2f>\n\n" % (Self.Version))
            File.write("ExeLimit: %d\n" % (Self.ExeLimit))
            File.write("FontSize: %d\n" % (Self.FontSize))
            File.write("FontFace: \"%s\"\n" % (Self.FontFace))
            File.write("ButtonMode: \"%s\"\n" % (Self.ButtonMode))
            File.write("DisplayBase: %d\n" % (Self.DisplayBase))
            File.close()

    def Dump(Self, Event=None) :
        """ This routine dumps the contents of memory to a user specified file. """
        FileName = asksaveasfilename(initialdir='../asm', filetypes=[('text files', '.txt')])
        if FileName:
            try :
                File = open(FileName, 'w')
            except :
                showerror('MiSaSiM', 'Could not open file ' + FileName)
            else :
                DataAddresses, StackAddresses = Self.DataView.Collect_Sorted_Addresses()
                for Address in DataAddresses :
                    Value = Self.Sim.Mem[Address]
                    File.write('%04d: %10d\n' % (Address, Value))
                for Address in StackAddresses :
                    Value = Self.Sim.Mem[Address]
                    File.write('%04d: %10d\n' % (Address, Value))
                File.close()

    def Copy(Self, Event=None) :
        """ This routine copy the selected region onto the clipboard. """
        if Event and Event.widget.tag_ranges(SEL) :
            String = Event.widget.get(SEL_FIRST, SEL_LAST)  
            Self.clipboard_clear()              
            Self.clipboard_append(String)
            print String

    def Exit(Self, Event=None) :
        Self.quit()

    def Seed(Self, Event=None) :
        """ This routine inputs a new seed. """
        SeedForm = Toplevel()
        Seed = StringVar()
        SeedEntry = Entry(SeedForm)
        SeedEntry.config(textvariable=Seed)
        SeedEntry.pack(side=TOP, expand=YES, fill=X)
        OKButton = Button(SeedForm, text='OK', command=(lambda Var=Seed,
                                                        Win=SeedForm:
                                                        Self.Update_Seed(Var, Win)))
        OKButton.pack(side=TOP, expand=YES, fill=X)
        SeedEntry.focus_set()

    def Update_Seed(Self, Seed, Window) :
        """ This routine updates the seed. """
        SeedStr = Seed.get()
        if SeedStr <> "" and SeedStr.isdigit() and int(SeedStr) > 0 :
            seed(int(SeedStr))
        Window.destroy()

    def Print_Message(Self, String) :
        """ This routines redirects message prints to the message view. """
        Self.MessageView.Print_Message(String)

    def Print_Warning(Self, String) :
        """ This routines redirects warning prints to the message view. """
        Self.MessageView.Print_Warning(String)

    def Print_Error(Self, String) :
        """ This routines redirects error prints to the message view. """
        Self.MessageView.Print_Error(String)

    def Forward(Self, Event=None) :
        """ This routine moves forward to the next instruction in the trace. """
        if not Self.Sim.Instructions == [] :
            if Self.Sim.Trace == [] :
                Self.Execute()
            Mods = Self.Sim.Nav.Next_Inst(Self.Sim.Trace)
            Self.Process_Mods(Mods, True)
            del Mods

    def Backward(Self, Event=None) :
        """ This routine moves backward to the previous instruction in the trace. """
        if not Self.Sim.Instructions == [] :
            if Self.Sim.Trace == [] :
                Self.Execute()
            Mods = Self.Sim.Nav.Prev_Inst(Self.Sim.Trace)
            Self.Process_Mods(Mods, False)
            del Mods

    def Next(Self, Event=None) :
        """ This routine moves to the next occurrence of the current
        instructions in the trace. """
        if not Self.Sim.Instructions == [] :
            if Self.Sim.Trace == [] :
                Self.Execute()
            Mods = Self.Sim.Nav.Move_to_Next_Occurrence(Self.Sim.Trace)
            Self.Process_Mods(Mods, True)
            del Mods

    def Prev(Self, Event=None) :
        """ This routine moves to the previous occurrence of the current
        instructions in the trace. """
        if not Self.Sim.Instructions == [] :
            if Self.Sim.Trace == [] :
                Self.Execute()
            Mods = Self.Sim.Nav.Move_to_Prev_Occurrence(Self.Sim.Trace)
            Self.Process_Mods(Mods, False)
            del Mods

    def Goto_Start(Self, Event=None) :
        """ This routine moves to the next instruction block in the trace. """
        if not Self.Sim.Instructions == [] :
            if Self.Sim.Trace == [] :
                Self.Execute()
            Mods = Self.Sim.Nav.Move_to_Top(Self.Sim.Trace)
            Self.Process_Mods(Mods, False)
            del Mods

    def Goto_End(Self, Event=None) :
        """ This routine moves to the previous instruction block in the trace. """
        if not Self.Sim.Instructions == [] :
            if Self.Sim.Trace == [] :
                Self.Execute()
            Mods = Self.Sim.Nav.Move_to_Bottom(Self.Sim.Trace)
            Self.Process_Mods(Mods, True)
            del Mods

    def Goto_Addr(Self, Event=None) :
        """ This routine displays and updates simulator parameters. """
        GotoForm = Toplevel()
        GotoForm.title('Goto Address')

        Address = StringVar()
        Address.set(str(Self.Sim.IP))
        AddressFrame = Frame(GotoForm)
        AddressLabel = Label(AddressFrame, text='address', width=15)
        AddressEntry = Entry(AddressFrame)
        AddressEntry.config(textvariable=Address)
        AddressFrame.pack(side=TOP, fill=X)
        AddressLabel.pack(side=LEFT)
        AddressEntry.pack(side=RIGHT, expand=YES, fill=X)

        GotoVars = (Address)
        ButtonFrame = Frame(GotoForm)
        ButtonFrame.pack(side=TOP, fill=X)
        OKButton = Button(ButtonFrame, text='OK', command=(lambda Vars=GotoVars,
                                                           Win=GotoForm:
                                                           Self.Goto_Addr_Cmd(Vars, Win)))
        OKButton.pack(side=LEFT, expand=YES, fill=X)
        CancelButton = Button(ButtonFrame, text='Cancel', command=GotoForm.destroy)
        CancelButton.pack(side=RIGHT, expand=YES, fill=X)

    def Goto_Addr_Cmd(Self, Vars, Window) :
        """ This routine moves to the next occurrence of the specified
        instructions address in the trace. """
        Inst_Addr = int(Vars.get())
        if Inst_Addr > 0 and Inst_Addr % 4 == 0 :
            if not Self.Sim.Instructions == [] :
                if Self.Sim.Trace == [] :
                    Self.Execute()
                Mods = Self.Sim.Nav.Move_to_Address(Self.Sim.Trace, Inst_Addr)
                Self.Process_Mods(Mods, True)
                del Mods
        Window.destroy()

    def Process_Mods(Self, Mods, Forward) :
        """ This routine processes a Mod oject returned from the Navigator.
        The direction flag Forward indicates the direction of the trace motion. """
        NewTraceRow, CurrCore, IPMods, RegMods, DataMods, StackMods = Mods
        Self.CurrCore = CurrCore
        Self.MenuView.Update(IPMods)
        Self.MenuView.Refresh()
        Self.TraceView.Select(NewTraceRow)
        DataAddresses, StackAddresses = Self.DataView.Collect_Sorted_Addresses()
        Self.DataView.Process_Mods(DataMods, Forward, DataAddresses)
        Self.StackView.Process_Mods(StackMods, Forward, StackAddresses)
        del DataAddresses, StackAddresses
        Self.RegView.Update(RegMods)
        Self.RegView.Refresh()
        SelectedRow = Self.Sim.Lookup_Instruction_Position(Self.Sim.IP) + 1
        Self.CodeView.Select(SelectedRow)
        Self.CodeView.Refresh()

######################### Menu Pane #########################

Load = """R0lGODlhEAAQAOYAAP///v/9+v/9+P7+/f789/788v789v368v777/767/368fv26Pv36fv36vz2
2Pz01/zz0PzyyPvyyvvyzPrw3Pvvufrts/rsrPjqwvbpyfnpofnppPnonPjmlfjmlPjkjvjlkfbh
rPfjhffji/fihfXgn/fhgfTdp/XekfXelPbgfPbfdvbecvTbnvbedvPalvbcbPXbaPPYjvXbZfXa
Y/PXhvXZXe/UlPTYXPLVgfLUf/TXVPTXV+/ThfTWT/HScvPUSe/Qeu7OiPPTR/PTRPHQbO7PcvLR
O/LQOebNee3KavHOMPHNLuXKdOPHa/DLJuTHa+nBc+LDYOHCXtu2PNqzNtm0NNmxMtiyLNqvNtqv
NdquNNqrNtqrNdqqNtqmN9qkNdqhNtqfNdqaNtqYNdqUNdmOM9iILdiGLP///wAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5
BAUUAGkALAAAAAAQABAAAAeigGmCg4SFhoeIiYRWU1KOUlRYkpNYglUDmJgNUE6dSU1XgloEHygl
IQipqgFZgl4KKSk5Sko9PUFBRgxbgl0LN0JRGQXExQBcgl8AAswCDh4iKzE4D2CCYQYRFRccIyow
Nj5EEGKCYwcWGx0kLjM8QEdLE2SCZQkaICYsNDtDSExPJJQRZIbCiRYvZNTQoeNHkSIYzAhCQ/GM
xYsYzyjayDEQADs="""

Reload = """R0lGODlhEAAQAOYAAKfXnqTUm6HSmJ/Sl5/Rlp7RlZzQlJzPlJrPkpnPkJjOj5bNj5XMjZTLjJLK
iZHKipDKiI/JiI/Jh47JhY7GhovHhY3HhovGg4nGgoXHe4vDg4rEg4fEgIXEfonDgIPEeYPDeYLC
eoHCd3/BeXPGZ4G+en6/dXDCZHy9c27AY22+Ymy8YGq7X2i5Xnazb2e2XG6wZmW0W2ytZWusY2iq
YV+tVmioYF6rVGWnXmOkXWKiW1qmUFejTlWhTVOeS1GbSVaXUE+ZR1SVTk2WRVGSS0+QSUuTQ0mR
QUyNR0aOP0qLRUSLPUKIO0CGOT6DNzyANTp+NDd7MjN2LjJ0LCxtJyprJiloJCdmIyVlIiRjICNh
HyFfHh5bG////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5
BAUUAF0ALAAAAAAQABAAAAejgF2Cg4M8P4SIiEFHiV0pLDE1Oz5DNjpQiCotIA4GBgkNEhxCVIMr
LxMBCqsQFx0jSFiDMSYCBxY4TVBSRUpZhDceDBtLToNXWog9i0xPhFtcN4ZGS0NJulIkJ4TLR82I
j4OUFBQuUoQqGSLSPzMaEhhApYIrHwABAwgMECEdOVWyBMVAQYDAggcVSsggYuUXIR4waBSLMoUK
skbeGjXSpbFLIAA7"""

Exec = """R0lGODlhEAAQAOcAAP///ykpKUyJxkqHxBxLk2RkZEiEwkWAvygxPZ6/5qC/5T4+PikqLCksMCky
Pio7UipYnC03QjBlqTFEWTRqrTVObjhvsDt0tDw8PCkqKz5ETD94uEBAQEJKVUJ8vENITigsMSU0
TElPVkligCRTmSNUmk1kgVBnglCLxlqP01xcXFyQ0yBQl2CU1GJyhx5NlWR1h2SMwmWBo2aY1muG
pmxsbGyd2G2Ipm6e2XB9i3CJp3Kh2nSi2nek23mm23qRr3uMoXun3H2Yu32o3H+q3YGr14Ks3oWv
34av34eu2Yiw34ix2oyu2Iyz4Y604Y+gtZCfr5C24pa34pq85Zy85Z295RxAc19yhqTC56jE6K7J
57PN6rTN6rfP6rjR67rR7LvS7bzT7cHW7ho4YAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAA
AAiiAAEIHEiwoMGDCBMqXChAwAADBzxsuGCBgkEBS7x86bKFixYmEgoKQAHlSgIdNE4ggTGGoMMi
OW5EkWFiRA8XFayUYAFgQBIxCZwoMRKEB44hCqjEeAHAQJgpTY4Q8bHDxowWK1JIIUHgAJgnH0QA
yYJFQZUfGjoIgUBgQgQGCzg0eOAAAYIMCzCACEFAYIACNQIQ/KtC8MAAiA37Tbyw8cKAACH+EEFk
b2JlIEltYWdlUmVhZHkAOw=="""

MultiExec = """R0lGODlhEAAQAOcAAP///zdrGSkpKUyJxkqHxKC/5Z6/5rLSlY26ZI+8Z0iEwkWAv1OMKDBlqTFE
WTRqrTVObjVoJDZlZS03QjhvsDlsGzt0tD4+Pj94uEBAQEJ8vENITio7UikyPklPVkligCksMEx7
MSkqLE1kgVBnglCLxigxPVePLVuERFyHSF9yhmJyh2RkZGR1h2SMwmWBo2aOTyNUmmeUmGuGpmxs
bGyd2G2Ipm2UXm6e2XB9i3CJp3Kh2nSi2nek23mm23uMoXun3H2o3H+q3YGrYYGr14Kmm4Ks3oWv
34av34eu2Ye5YIe6YIiw34ix2ou6Yoyu2Iyz4Yy8ZSBQl4604Y+gtY+7ah5NlZCfr5C24pq85Zy8
5RxLkxxAc6TC56jE6K7J57HTkLHWkmaY1rPN6rTN6rTUlbbUnLfP6rjR67rR7LvS7bzT7cHW7tDm
uho4YAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAA
AAi2AAEIHEiwoMGDCBMqXDhgAAEFCzRgsEDhgcEBTdCkOTOGzJcnDQoOKHFFhQEdM0ggaeGGoEMi
OWxgeTHiQ48VELjEkAKAQBI2BqYwMQKEB44gBbS4sAJAwZosUI4I8bGjhhgZN2CkkLBlgRoqGzz8
8NKlQJEhZdpUORHBwQQRFzKA4NDBBAowYQBESRBAoAAWNAQMDGFm4IG+AAQoFiywgpMlAJTwTRiA
AYIDCBggRhigc2cAAQEAIf4QQWRvYmUgSW1hZ2VSZWFkeQA7"""

Dump = """R0lGODlhEAAQAPebADZrvDZruzZquzlsvDtuvTptuzhruz5wuzVptv///9Hg9tHg9/j7/vf7/vb5
/fD1/Orw+u3y+/f6/evx+9/p+L3Q7F6JyTVptdHf9oCq6fb6/vb6/WSMyO7z++rx+/L2/PH2/OLs
+dvn+LrQ7tDf9n6o6Onx+u70++jw+t3o+Nvm93qj4cPV7zVpt8zd9X6o52aNyenw+vP4/fj6/u/0
/N/p+dvn99nl93ii4KnC5zVotsnc9H2n5+Hs+ePt+e70/PP3/eXt+tjl9neg3qS+5DRntMfZ9H2m
5mWNyWeOyWySy22Sy2mQymWMyHSc2p+64TRms8XY8nuk43qj43qk43uk4nuj4nuj4Xmi4Xeg33af
3nSe3XKc23Sd3Jq13TRlscLV8nih4HWe3nOb2nOb2ZWw2jNkr77S8Hqj4nef3naf3XKb2XGZ2HCZ
1o6r1TNjrTZqurvQ73qi4m2W04qn0jJiq7jO7/f6/ojAYmqTz4SjzjJhqjhsu7bM7nqi4cLcv2iQ
zYGezDJhqDdrurPK7Xqi4GWNynybyTFgpzVquq3G663F6nyayHmYxzVpuTVpuDVotzVotTRmsjNl
sDNkrjJjrDJiqjJhqTFgqDFgpjFhqBWygAAAAAAAAAAAAAAAAAAAAAAAAAAAABUFAAAAAAIAAAAA
AAAAAAAAAAAAAAAVBQAAAAIoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJwAAAAS3ACiqNjAAAAA
EgAVABLcOO4YAMB8kHyRQAAAAAAAAI4AAAAB1gAAcdq0AIAAEsAQABLcOO4YAHB8kHyRBf///wAA
/z0AAHyRBBLb6At1AAB8gQAAAJvADP//AwwAAAObwAAAGAAAANAAAAAS2wAAQAAAALQAAAAS2wAA
AAAAAAAAAAAAAAAADAACAAEAAHyQAf3cAADAfwAAAAAAAAAAAgDIAIACGgAVsgAAALKAAAUAFQAA
AIDi39wMfE8AEnyAGpDl5Q5IfDx8gQAAAxLcMNw4AAgAEgAAAAAADiH5BAgAAAkALAAAAAAQABAA
AAj+AAEIFBgggAABAwgUMHAAQQIAChYwaODgAYQIDiRMoFDBwgUAGDJo2MChg4cPDECEEDGiwgEA
JEqAAMHBxAkJDlCkULGCRQsALl6gQAEjhowZNGrYuIEjh44AO3j06OHjhwQgQZYKGUKkSAAjRzgg
SaJkCZMmHNI6eQJFQBQpU6hUsXIFSxYtW7h08fJFAJgpU6xYqYIlzBAxXcaQKWNGwBk0aFbQDZNG
TZc1bNq4eQMnjhwGoEOLnkOnjgE7WO7gWc16tYM8evbw6ePnzp/buG87ABRI0CBChVS3Zu3A0CFE
iRQtEs2cAaNGiOA4egQpUhFJkyhVsnQJE6JMmgIBAgAh/gA7"""

Start = """R0lGODlhEAAQAOYAALTO8rDL8KvI76XE7aLB7p7A652+7Ji76Za56pG26JC054+155C15o+06I6z
5o2y5oqx5Yau5IWt5IOs44Cr6ICr6n6p6H6p4n6o4Xuo4Xmn4Xqn4Hem5nek4Xaj33Oi4XGh33Cg
4nCf3m6f3W2e3m2d3mmd32uc3Wqb3GWb4Waa32WX22SX3WKX22OX2lyS316R2FON2VKL2VCJ2UqJ
2UyJ2EqF1kWE2EOE1keE1kSB00GA1Dl70j130Cx0zzhryh5rzR5pyzNkxhpiyBlcxhlaxBhZxhhV
xBdSwBZKvRRBuxQ+thM8txI5thIzsv///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5
BAUUAE8ALAAAAAAQABAAAAeEgE+Cg4SFhoeHFYochDExhhQABCGDNTU3hhwBBimCNiYKPIYhAggv
TzkqCws+hikDDTI7LAwXEkCGLwUHOB8OGicYQ4YyBw48JBEgLR5GhjcJHT5BOhsuIkiGPBAluEU9
IyhJhj4TK8NPST8uSoZAGTDOgktCTIZDREfZg05NiP8AEQUCADs="""

Prev = """R0lGODlhEAAQANUAAJq96pm76ZW46JW56Iuz5Y2y5oav5YOt44Gr43yp4Xqm5Xqm4Xek4HWk43Gh
3nKh33Gg4G6f3Wud4Gub4Wmb3GWZ4Wea3GWZ32aY22KX4WKV2l+V3GCV3VmQ3VqQ21ON2VCJ2UqH
2UiF1kGA1jp81D130CpyzypwyzdrySduzRtlyTFfxBlcxBlcxhdSwBZKvRVHvRRAuRM5txM5tBIz
tBEwsP///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAUUADYALAAAAAAQABAAAAZxQJtw
SCwaj0jhpFJcGi+XDhEqJXIUgNDwmiV6GoEASfgNj4UfSMBQMNnS67YQJBEgHgcV3Y5XCUcbBAwW
Cy2AgoQtQicnIgkYDi6MjpAuRCwlERQwQpianEQvKBoxQ6KkRjMrMkSqrEY1NEWxSbW2Q0EAOw=="""

Backward = """R0lGODlhEAAQANUAAJq96pm76ZW46JW56Iuz5Y2y5oav5YOt44Gr43yp4Xqm5Xqm4Xek4HWk43Gh
3nKh33Gg4G6f3Wud4Gub4Wmb3GWZ4Wea3GWZ32aY22KX4WKV2l+V3GCV3VmQ3VqQ21ON2VCJ2UqH
2UiF1kGA1jp81D130CpyzypwyzdrySduzRtlyTFfxBlcxBlcxhdSwBZKvRVHvRRAuRM5txM5tBIz
tBEwsP///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAUUADYALAAAAAAQABAAAAZNQJtw
SCwaj8jipJIkXi6dppCjAISknkYgQGp+IAFDwZQESQSIx0GVHG0IDMuilTydRAmMwyVllSIUMFI2
LygaMYM2MysyiTY1NI6SSEEAOw=="""

Forward = """R0lGODlhEAAQANUAAK3I76jH7qPC7aHB7Jm76pm76ZK36JC154qx5Iew6Iev5IGr44Gr4oCr6oCr
6ICq436p6Hyp6Hyp4X6o4Xmn5nmm4HWk43ek4HSj4HWj33Si4nKh326g4mKX4WGX3WCV3VOO20uI
1kOE1keE1kN/0z960D130DV30jx0zztxzCxyzSNuzRpiyRpixhlZxhhZxBhTwBdQvRZOwBZKvRVF
txVFuRRBt////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAUUADcALAAAAAAQABAAAAZMwJtw
SCwaj0iHA2lsRDRMIgWQ+ESFnIDAMrp2BoaCRxUFER4PRKjFFB0wGAbJxTwpNpISjMZcTSomMVcs
GSgzVzcvKTWINzI2jZGSQQA7"""

Next = """R0lGODlhEAAQANUAAK3I76jH7qPC7aHB7Jm76pm76ZK36JC154qx5Iew6Iev5IGr44Gr4oCr6oCr
6ICq436p6Hyp6Hyp4X6o4Xmn5nmm4HWk43ek4HSj4HWj33Si4nKh326g4mKX4WGX3WCV3VOO20uI
1kOE1keE1kN/0z960D130DV30jx0zztxzCxyzSNuzRpiyRpixhlZxhhZxBhTwBdQvRZOwBZKvRVF
txVFuRRBt////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAUUADcALAAAAAAQABAAAAZvwJtw
SCwaj0WHI7k0NiIa4jNapAASn6EVW+QEBJaR0AsWDzsDQ8GjuqHV7CGI8HggQq15/d4Sig4YGAwk
Ln+Bgy5CJwobEiUwNIuNjzRCKxMVJjGWmJpELBkoM0OgokUvKTVEqKpFMjausEiztLRBADs="""

End = """R0lGODlhEAAQAOYAAK3I76vI76XE7abD7p7A656+6pq86pi76Ze66pS36JK36JG26Iuz54uy5Y2y
5omx5omx5Iqx5Yiw6Iew5oau5ISu5IWt5IOs44Kr44Gr4oCr6H+p436p6H+q436o4Xun6Huo43qm
5Xem5naj33Sj33Ki4nOi4HCg4nCf3m6d32md32qb3GWb4WaZ3WKX32OX2mCV316U2F6S2VyS31mQ
3VeL1lKL2U6J2FOF1EuH1kaF1kWE2E6A0kSB00KB0zl70Tl70ix0zypyzx5rzRpiyBpjyBpgxhlc
xhlZxBhZxhhVwBdSwBZKvRRBuxQ+uRM8txM6txI5tv///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5
BAUUAFIALAAAAAAQABAAAAeGgFKCg4SFhoeHGhqELDA0NoYaHyWDMwwGO4YiABIugjYVCUCGJwED
ITdSOyAOQYYsAggFKj8/JhZDhjMEExMKKUIZGUSGNgcdHQ0tQyQkSYY7CxsQOUVFMihLhkARFDpG
Ukk1K0yGQRc9R4JLOC9NhkM+SINMPDFPhkRKhE1NUFCIAgpEFAgAOw=="""

Goto = """R0lGODlhEAAQAOcAAP///3un3JK56Pz+/vv9/VFxqff5+/X5+/T3+/n7/KrLkfr9/fz9/f3//
3mi2Hag1XWe1K3NlGaLwFd7qVeYKFp8slubKVx+tVygPF6Bt16fOl+DuV+hQ2CFumGFu2KeMWKjR
mOHvWOfMWSIvmWfMVGXImalSGiOw2iiNWilRmmiOWujN2ySyGyUyW6Uym6kOW+QwW+Wy2+XzG+lP
XCZznCmP3Kaz3Oc0XOd0nSrT0mRHEaQGURzgnmj2XqaxEOPFnqk23qm3DuLEHyvVYCzYYGzWoK1Z
4Ws3YW2ZoW2aom4a42x3Y66b5C8dDWHCJbBgJfCgpjCg57FiKHGiqHHiqXIjajLkKnKkC2DASuDA
bDOlt7n8uTq8+fr9efv8ejs9urv9urw9+vy9+3z9+70+PD1+fH2+/L3+vP3+yV/APT4+/X4+yV8D
vb6+yR8EPf7/Pj7/Pj8/Pn79yF9APn8/Pn9/fr8/B97AB57Axt5ABl5APz///3+/nqk2v7//xV5A
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACwAAAAAEAAQAAAI1gABC
BxIsCCAAksCBOnj4AEEHDZoxGjhowCAIwIyatyoEQaAACBDihQpAQAQgyhDAOgBIAEcAwjOlBkDp
guXLQA6AHAAYIGdBG3WIDBDRkyYLwAyAHgAgAGBBXTeHFCDpgYJLwAuAIAAYAABp3XiGDigoggFO
RUA3Og6wOuMFyg+DFGQY8cEADIA7GnQdoWWCAqsNKGSwgkWFwL9NOAjIgITJUiIGImCIQ2LghauV
JkiJQkUE2zyFDghYYSHDSV0/BCi4QkINzxQEszC4Y4e2QTn4PkzMCAAIf4QQWRvYmUgSW1hZ2VSZ
WFkeQA7"""


Options = """R0lGODlhEAAQAOcAAP///5ubm6O96MfHx+Tk5Ji05lGD1ZaWlpOTk5KSkoeHh4WFhYGk33Sc3nie
3nmf3Xmf3nub0n+l34GBgXOc3oKCgoODg4Ol34SEhHGZ3IWn4YaGhm+X24ep4YiIiIin2omJiYmp
4YqKiout44yMjIyp2Iyu4o2NjY6Ojo+Pj2WR2ZKx5F2J0pSz5ZSz5pWVlVeH1Za05ZiYmE+B001/
05mZmZm35pq25kt90Zu35pu455ycnJy35py5552dnZ25556enkl90aW+6aW/6afA6ajA6qvC6qvD
6qysrKzD6q3E6q7G67PI7LPI7bW1tbfM7bjM7rm5ubq6urrN7rrO7rvO7ry8vLzP78DAwMLCwsPD
w8TExMXFxcbGxkd70cjIyMzMzM/Pz9LS0tTU1NfX193d3eLi4pi25ufn5+7u7kV50QAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAA
AAioAAEIHDgQyI4ANQgqFOgjAIE0BxYqDGAGTRQEEgnKIBAmAQAUJERkPFCGS4oTSMgokPgCwZgv
VqRk2bJA4YgPCQaAGdBFCxYMFQiG6HGmhBgnIBQssDCBYAceV6iYiOBhg0QNNqoQEcCEAQuJFwpM
GRLjxxIIBhZKcAFFSIscShzMkPjgiYAVN5I0oJGRQxMdBY5QCJIRgAoGRopk8FJYIAwDONQ0BhAQ
ACH+EEFkb2JlIEltYWdlUmVhZHkAOw=="""

Exit = """R0lGODlhEAAQAOcAAP////90d/heYfhfYvddYPtpbOIdH/dbXf93evZYW/VWWfNRVOovMfBHSu5B
Q+5AQus5PO0/Qew7Puw8Pu09P+0+QOw6Pe49P+s4O+s3Oe5BRO5CRe9DRu9ER+9FSPBGSPBGSes0
NvE/QfJFR/JMT/JNT+kyNfRISvRNUPVOUPVWWOktL/VXWvZKTPZVWPZWWfZYWugwMvZZW/ZZXPZa
XPZaXectMOYqLPdcXvdcX+UnKvdfYeUlJ+QiJPhgY/hhZPhiZPlhY/ljZvloavphY/piZfpjZvpk
Z/pqbfpsbvtnaeMgIvttb/ttcPxrbvxzdv1ucf1vcv1xdP10d/15fP5xdP52ef56ff5+gf9UV/9W
Wf9YW/9bXv9iY/9naP9sbv9ucP9wcf9wcv9wc/9xdP9ydP9zdv90duMfIf92ef93efdVV/95e/95
fP95ff96ff97fv98fv9+gP9+gf+Chv+HiuIcHgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAQABAA
AAjBAAEIHEhQoI+CAAIEQDjggAKCARBYiUJQwI8hC0oIjDgHi5QCAgkMYBJnQIMNAMxUuVKHSoEg
OQQkebMDhIaBUJxMofMECAEkbAh4cFBQiZAmcuC0UYOjwwOEAATUcMNlyxkOEaACmHEgjZYsYj5A
gJqAxpEyY8B8WXMhRkEWMoyQgeFgAgovKULoGKggQZEwLx5IyGBiRJcTK5YIXKCCiIsIFgTauCGi
BQMDAxuQqDB2II8elwtSwIAQjR2tqAUGBAAh/hBBZG9iZSBJbWFnZVJlYWR5ADs="""

class MenuPane(Frame) :
    def __init__(Self, Parent, relief = FLAT) :
        Frame.__init__(Self, Parent, relief = FLAT, bd=0)
        Self.BuildMenu(Parent)
        Self.BuildCoreInfo(Parent)
        Self.CoreIPs = {}

    def BuildMenu(Self, Parent) :
        Self.IconImages = []
        for Image, Text, Command in ((Load, ' Load ', lambda: Parent.CodeView.Load()),
                                     (Reload, ' Reload ', lambda: Parent.CodeView.Reload()),
                                     (Exec, ' Execute ', lambda: Parent.Execute()),
                                     (MultiExec, ' MultiExec ', lambda: Parent.MultiExec()),
                                     (Dump, ' Dump ', lambda: Parent.Dump()),
                                     (Start, ' Start ', lambda: Parent.Goto_Start()),
                                     (Prev, ' Prev ', lambda: Parent.Prev()),
                                     (Backward, ' Backward ', lambda: Parent.Backward()),
                                     (Forward, ' Forward ', lambda: Parent.Forward()),
                                     (Next, ' Next ', lambda: Parent.Next()),
                                     (End, ' End ', lambda: Parent.Goto_End()),
                                     (Goto, ' Goto ', lambda: Parent.Goto_Addr()),
                                     (Options, ' Options ', lambda: Parent.Options()),
                                     (Exit, ' Exit ', lambda: Parent.Exit())) :
            if Self.master.ButtonMode == 'name' :
                Button(Self, bd = 2, text = Text, compound = LEFT, relief = GROOVE, overrelief= RAISED, command = Command).pack(side = LEFT)
            elif Self.master.ButtonMode == 'icon+name' or Self.master.ButtonMode == 'icon':
                IconImage = PhotoImage(data = Image)
                Self.IconImages.append(IconImage) # keep images to avoid garbage collection
                if Self.master.ButtonMode == 'icon+name' :
                     Button(Self, bd = 2, text = Text, image = IconImage, compound = LEFT, relief = GROOVE, overrelief= RAISED, command = Command).pack(side = LEFT)
                else :
                     Button(Self, bd = 2, image = IconImage, width=50, compound = LEFT, relief = GROOVE, overrelief= RAISED, command = Command).pack(side = LEFT)

        for CoreID in range(Parent.NumCores):
            Button(Self, bd = 2, text = 'Core %s' %(CoreID), 
                   relief = GROOVE, overrelief = RAISED, 
                   command = Parent.CoreIDSetters[CoreID]).pack(side = LEFT)

    def BuildCoreInfo(Self, Parent) :
        Self.IPText = StringVar()
        Self.IP = Label(Self, textvariable = Self.IPText, height=1, width=10)
        Self.IP.pack(side=RIGHT)
        Self.IP.config(font=('courier', Parent.FontSize, Parent.FontFace))
        Self.CoreText = StringVar()
        Self.CurrCore = Label(Self, textvariable = Self.CoreText, height=1, width=10)
        Self.CurrCore.pack(side=RIGHT)
        Self.CurrCore.config(font=('courier', Parent.FontSize, Parent.FontFace))

    def DestroyMenuIP(Self) :
        for Child in Self.children.values() :
            Child.destroy()

    def Update(Self, IPMods):
        for CoreID, IP in IPMods.items():
            Self.CoreIPs[CoreID] = IP

    def Refresh(Self) :       
        CurrCore = Self.master.CurrCore
        Self.CoreText.set('Core = %i' % CurrCore)
        Self.IPText.set('IP = %i' % Self.CoreIPs[CurrCore])

    def notdone(Self) :
        showerror('Not implemented', 'Not yet available')

    def About(Self):
        showinfo('About MiSaSiM', 
                 'MiSaSiM version %s\Aug 2012\n\n'
                 'A MIPS simulation environment\n'
                 'Copyright (c) 2004 - 2012 Scott & Linda Wills\n'
                 'Additional development by Matt Bishop & Dan Ordille\n\n'
                 'GUI icons thanks to Mark James at www.famfamfam.com'  % Self.master.Version)

######################### Code Pane #########################

class CodePane(Frame) :
    def __init__(Self, Parent) :
        Frame.__init__(Self, Parent)
        Sbar = Scrollbar(Self, orient='vertical')
        Self.Code = Text(Self, wrap='none', undo=True, width=70, height=15)
        Sbar.pack(side=RIGHT, fill=Y)
        Self.Code.pack(side=TOP, fill=BOTH, expand=YES)
        Self.Code.config(yscrollcommand=Sbar.set)
        Sbar.config(command=Self.Code.yview)
        Self.Code.config(font=('courier', Parent.FontSize, Parent.FontFace))
        for Tag, Color in (('Address', 'black'), ('Label', 'blue'), ('Opcode', 'purple'),
                           ('Reg', 'red'), ('Immd', 'forest green')) :
            Self.Code.tag_config(Tag, foreground=Color)
        Self.Code.tag_config('Select', background='yellow')
        Self.CurrentDialog = None
        Self.LastFileName = None
        Self.Code.config(state='disabled')

    def Refresh(Self) :
        """ This routine refreshes the code widget based on current simulation data. """
        Self.Code.config(state='normal')
        Self.Code.delete('1.0', END)
        if Self.master.Sim.Instructions <> [] :
            for I in Self.master.Sim.Instructions :
                for (Tag, String) in I.Tagged_Print() :
                    Start = Self.Code.index(INSERT)
                    Self.Code.insert(INSERT, String)
                    if Tag :
                        Self.Code.tag_add(Tag, Start, INSERT)
                Self.Code.insert(INSERT, '\n')
            SelectedRow = Self.master.Sim.Lookup_Instruction_Position(Self.master.Sim.IP) + 1
            Self.Select(SelectedRow)
        Self.Code.config(state='disabled')

    def Select(Self, Row) :
        """ This routine removes the current 'Select' tagged region. It then selects
        and highlight the indicated row. """
        Self.Code.config(state='normal')
        Self.Code.tag_remove('Select', '1.0', END)
        RowIndex = '%i.0' % (Row)
        Self.Code.tag_add('Select', RowIndex, RowIndex + ' lineend')
        Self.Code.see(RowIndex)
        Self.Code.config(state='disabled')

    def Load(Self, Event=None) :
        """ This routine allows a files to be selected and opened. """
        Self.master.Clear()
        if not Self.CurrentDialog :
            Self.CurrentDialog = Open(initialdir='../asm', filetypes=[('assembly files', '.asm')])
        FileName = Self.CurrentDialog.show()
        if FileName:
            try :
                File = open(FileName, 'r')
            except :
                showerror('MiSaSiM', 'Could not open file ' + FileName)
            else :
                Self.LastFileName = FileName
                Self.master.Sim.Parse_Program(File)
                Self.master.Sim.Restart()
                Self.Refresh()

    def Reload(Self, Event=None) :
        """ This routine reloads the current file. """
        Self.master.Clear()
        if Self.LastFileName:
            try :
                File = open(Self.LastFileName, 'r')
            except :
                showerror('MiSaSiM', 'Could not open file ' + Self.LastFileName)
            else :
                Self.master.Sim.Parse_Program(File)
                Self.master.Sim.Restart()
                Self.Refresh()

######################### Trace Pane #########################

class TracePane(Frame) :
    def __init__(Self, Parent) :
        Frame.__init__(Self, Parent)
        Sbar = Scrollbar(Self, orient='vertical')
        Self.Trace = Text(Self, wrap='none', undo=True, height=11)
        Sbar.pack(side=RIGHT, fill=Y)
        Self.Trace.pack(side=TOP, fill=BOTH, expand=YES)
        Self.Trace.config(yscrollcommand=Sbar.set)
        Sbar.config(command=Self.Trace.yview)
        Self.Trace.config(font=('courier', Parent.FontSize, Parent.FontFace))
        for Tag, Color in (('Address', 'black'), ('Label', 'blue'), ('Opcode', 'purple'),
                           ('Reg', 'red'), ('Immd', 'forest green')) :
            Self.Trace.tag_config(Tag, foreground=Color)
        Self.Trace.tag_config('Select', background='yellow')
        Self.Trace.tag_config('Even', background='lightcoral')
        Self.Trace.tag_config('Odd', background='lightskyblue')
        Self.Length = 50
        Self.Base = 0
        Self.Trace.config(state='disabled')

    def Refresh(Self) :
        """ This routine refreshes the trace widget based on simulation data. """
        Self.Trace.config(state='normal')
        Self.Base = 0
        Self.Print_Trace_Block()                            # print starting trace block
        Self.Select(0)                                      # start at first trace entry
        Self.Trace.config(state='disabled')

    def Select(Self, Row) :
        """ This routine removes the current 'Select' tagged region. Then the needed
        block is printed (unless already available). It the slected row is
        highlighted. """
        Self.Trace.config(state='normal')
        Self.Trace.tag_remove('Select', '1.0', END)         # clear select mark
        if not Self.Base <= Row < Self.Base + Self.Length : # if row not in current block
            Self.Base = (Row / Self.Length) * Self.Length   # then compute new base
            Self.Print_Trace_Block()                        # and print new block
        Offset = Row % Self.Length                          # compute block offset
        RowIndex = '%i.4' % (Offset + 1)
        Self.Trace.tag_add('Select', RowIndex, RowIndex + ' lineend')
        Self.Trace.see(RowIndex)
        Self.Trace.config(state='disabled')

    def Print_Trace_Block(Self) :
        """ This routine prints a trace Length-sized block beginning at Base. """
        Self.Trace.config(state='normal')
        Self.Trace.delete('1.0', END)
        if Self.master.Sim.Trace <> [] :
            LastAddress = 0
            AddressTag = 'Even'     # address backgroung color toggle value
            Block = Self.master.Sim.Trace[Self.Base:Self.Base + Self.Length]
            for I, Result, OldValue in Block :
                for (Tag, String) in I.Tagged_Print() :
                    if not Tag == 'Comment' :               # don't print comments
                        Start = Self.Trace.index(INSERT)    # save insert point
                        Self.Trace.insert(INSERT, String)   # print I substring
                        if Tag :
                            Self.Trace.tag_add(Tag, Start, INSERT)  # tag substring
                            if Tag == 'Address' :
                                Address = int(String)
                                if not (Address - LastAddress) == 4 :   # if non-sequential
                                    if AddressTag == 'Even' :           # toggle tag color
                                        AddressTag = 'Odd'
                                    else :
                                        AddressTag = 'Even'
                                LastAddress = Address                   # update last address
                                Self.Trace.tag_add(AddressTag, Start, INSERT)
                if Result <> None and OldValue <> None and I.Opcode <> 'swi':
                    Self.Trace.insert(INSERT, ' old: %s, new: %s\n' % (OldValue, Result))
                else :
                    Self.Trace.insert(INSERT, '\n')
            del Block
        Self.Trace.config(state='disabled')

######################### Reg Pane #########################

class RegPane(Frame) :
    def __init__(Self, Parent) :
        Frame.__init__(Self, Parent)
        Sbar = Scrollbar(Self, orient='vertical')
        Self.Labels = []
        Self.Values = []
        Self.RegTable = {}
        for Name in xrange(1,32) :
            Self.Values.append(Name)
            Self.Values[Name - 1] = StringVar()
            Self.Values[Name - 1].set('$%02d: ----' % (Name))
            Self.Labels.append(Label(Self, textvariable = Self.Values[Name - 1], height=1, width=15, anchor = W))
            Self.Labels[Name - 1].grid(column = (Name - 1) % 3, row = (Name - 1) / 3)
            Self.Labels[Name - 1].config(font=('courier', Parent.FontSize, Parent.FontFace))
        Self.Values.append('Hi')
        Self.Values[31] = StringVar()
        Self.Values[31].set(' Hi: ----')
        Self.Labels.append(Label(Self, textvariable = Self.Values[31], height=1, width=15, anchor = W))
        Self.Labels[31].grid(column = 1, row = 10)
        Self.Labels[31].config(font=('courier', Parent.FontSize, Parent.FontFace))
        Self.Values.append('Lo')
        Self.Values[32] = StringVar()
        Self.Values[32].set(' Lo: ----')
        Self.Labels.append(Label(Self, textvariable = Self.Values[32], height=1, width=15, anchor = W))
        Self.Labels[32].grid(column = 2, row = 10)
        Self.Labels[32].config(font=('courier', Parent.FontSize, Parent.FontFace))    
        Self.DefColor = Self.Labels[0].cget("background")

    def Update(Self, RegMods):
        """ This routine updates the RegTable with new modifications. """
        for CoreID, RegMods in RegMods.items():
            for Reg, Value in RegMods.items():
                if not Self.RegTable.has_key(CoreID):
                    Self.RegTable[CoreID] = {}
                Self.RegTable[CoreID][Reg] = (Value, True)

    def Refresh(Self):
        """ Update the RegView Window. """
        CurrCore = Self.master.CurrCore
        for Name in xrange(1, 32):
            if Name in Self.RegTable[CurrCore]:
                Value, New = Self.RegTable[CurrCore][Name]
                if Self.master.DisplayBase == 10 :
                    Self.Values[Name - 1].set('$%02d: %i' % (Name, Value))
                elif Self.master.DisplayBase == 16 :
                    Self.Values[Name - 1].set('$%02d: %X' % (Name, Value))
                Self.Labels[Name - 1].config(background= Self.DefColor)
                if New:
                    Self.Labels[Name - 1].config(background= 'Yellow')
                    Self.RegTable[CurrCore][Name] = (Value, False)
            else :
                Self.Values[Name - 1].set('$%02d: ----' % (Name))
                Self.Labels[Name - 1].config(background= Self.DefColor)
        if 'HiLo' in Self.RegTable[CurrCore]:
            Value, New = Self.RegTable[CurrCore]['HiLo']
            Hi, Lo = Value
            if Self.master.DisplayBase == 10 :
                Self.Values[31].set(' Hi: %i' % (Hi))
                Self.Values[32].set(' Lo: %i' % (Lo))
            elif Self.master.DisplayBase == 16 :
                Self.Values[31].set(' Hi: %X' % (Hi))
                Self.Values[32].set(' Lo: %X' % (Lo))
            Self.Labels[31].config(background= Self.DefColor)
            Self.Labels[32].config(background= Self.DefColor)
            if New:
                Self.Labels[31].config(background= 'Yellow')
                Self.Labels[32].config(background= 'Yellow')
                Self.RegTable[CurrCore]['HiLo'] = (Value, False)
        else :
            Self.Values[31].set(' Hi: ----')
            Self.Values[32].set(' Lo: ----')
            Self.Labels[31].config(background= Self.DefColor)
            Self.Labels[32].config(background= Self.DefColor)

######################### Memory Panes #########################

class MemoryPane(Frame) :
    def __init__(Self, Parent) :
        Frame.__init__(Self, Parent)
        Sbar = Scrollbar(Self, orient='vertical')
        Self.Mem = Text(Self, wrap='none', undo=True, height=9, width=18)
        Sbar.pack(side=RIGHT, fill=Y)
        Self.Mem.pack(side=TOP, fill=BOTH, expand=YES)
        Self.Mem.config(yscrollcommand=Sbar.set)
        Sbar.config(command=Self.Mem.yview)
        Self.Mem.config(font=('courier', Parent.FontSize, Parent.FontFace))
        Self.Mem.tag_config('Free', foreground='gray')
        Self.Mem.tag_config('Frame', background='lightgreen')
        Self.Mem.tag_config('Static', background='lightcyan')
        Self.Mem.config(state='disabled')

    def Refresh(Self, SortedAddresses) :
        """ This routine refreshes the memory list based on current
        simulation data. """
        Self.Mem.config(state='normal')
        Sim = Self.master.Sim
        Self.Mem.delete('1.0', END)
        for Address in SortedAddresses :
            Value = Sim.Mem[Address]
            Self.Insert_Mem(Address, Value, SortedAddresses)
        Self.Paint_Static_Data(SortedAddresses)
        Self.Mem.config(state='disabled')

    def Process_Mods(Self, Mods, Forward, SortedAddresses) :
        """ This routine processes a set of memory modifications.
        If the allocation flag is true, the address is inserted or
        removed based on the trace movement direction. """
        Self.Mem.config(state='normal')
        Sorted_Mod_Addresses = Mods.keys()
        Sorted_Mod_Addresses.sort()
        for Address in Sorted_Mod_Addresses :
            Value, Allocated = Mods[Address]
            if Allocated :
                if Forward :
                    Self.Insert_Mem(Address, Value, SortedAddresses)
                else :
                    Self.Remove_Mem(Address, SortedAddresses)
            else :
                Self.Update_Mem(Address, Value, SortedAddresses)
        del Sorted_Mod_Addresses
        Self.Gray_Free_Memory(SortedAddresses)
        Self.Paint_Active_Frame(SortedAddresses)
        Self.Paint_Static_Data(SortedAddresses)
        Self.Mem.config(state='disabled')

    def Gray_Free_Memory(Self, SortedAddresses) :
        """ This routine changes text color to gray for free (unallocated)
        memory above the stack pointer. It also removes address color for
        unabllocated rows. """
        Sim = Self.master.Sim
        Self.Mem.tag_remove('Free', '1.0', END)
        SP = Sim.Regs[29]
        for Address in SortedAddresses :
            if Address < SP and Address >= Sim.StackBase :
                RowIndex = '%i.0' % Self.Find_Row(Address, SortedAddresses)
                Self.Mem.tag_remove('Frame', RowIndex, RowIndex + ' + 5c')
                Self.Mem.tag_add('Free', RowIndex, RowIndex + ' lineend')

    def Paint_Active_Frame(Self, SortedAddresses) :
        """ This routine paints addresses in the active frame if a frame
        pointer ($30) is defined. """
        Sim = Self.master.Sim
        Self.Mem.tag_remove('Frame', '1.0', END)
        if 30 in Sim.Regs :
            FP = Sim.Regs[30]
            SP = Sim.Regs[29]
            for Address in SortedAddresses :
                if FP > Address >= SP :
                    Row = Self.Find_Row(Address, SortedAddresses)
                    RowIndex = '%i.0' % Row
                    Self.Mem.tag_add('Frame', RowIndex, RowIndex + ' + 5c')
                    Self.Mem.see(RowIndex)

    def Paint_Static_Data(Self, SortedAddresses) :
        """ This routine paints addresses of static data. This is specified
        between DataBase and DataEnd"""
        Sim = Self.master.Sim
        Self.Mem.tag_remove('Static', '1.0', END)
        StaticStart = Sim.DataBase
        StaticEnd = Sim.DataEnd
        for Address in SortedAddresses :
            if StaticEnd > Address >= StaticStart :
                Row = Self.Find_Row(Address, SortedAddresses)
                RowIndex = '%i.0' % Row
                Self.Mem.tag_add('Static', RowIndex, RowIndex + ' + 5c')

    def Update_Mem(Self, Address, Value, SortedAddresses) :
        """ This routine updates a memory address in MemView. """
        Row = Self.Find_Row(Address, SortedAddresses)
        Index = '%i.7' % Row
        Self.Mem.delete(Index, Index + ' lineend')
        if Self.master.DisplayBase == 10 :
            Self.Mem.insert(Index , '%10d' % (Value))
        elif Self.master.DisplayBase == 16 :
            Self.Mem.insert(Index , '%8X' % (Value))

    def Insert_Mem(Self, Address, Value, SortedAddresses) :
        """ This routine adds a memory address into MemView. """
        Row = Self.Find_Row(Address, SortedAddresses)
        Index = '%i.0' % Row
        if Self.master.DisplayBase == 10 :
            Self.Mem.insert(Index , '%5d: %10d\n' % (Address, Value))
        elif Self.master.DisplayBase == 16 :
            Self.Mem.insert(Index , '%5d: %8X\n' % (Address, Value))

    def Remove_Mem(Self, Address, SortedAddresses) :
        """ This routine removes a memory address from MemView. """
        Row = Self.Find_Row(Address, SortedAddresses)
        Index = '%i.0' % Row
        Self.Mem.delete(Index, Index + ' + 1l')

    def Find_Row(Self, TargetAddress, SortedAddresses) :
        """ This routine finds the row number for a given memory address. """
        Row = 1
        if SortedAddresses == [] :
            return Row
        for Address in SortedAddresses :
            if Address >= TargetAddress :       # when row is found, return it
                return Row
            Row += 1
        return Row                              # must be the largest address

    def Collect_Sorted_Addresses(Self) :
        """ This routine collects two sorted address lists, one for data addresses
        and one for stack addresses. """
        DataAddresses = []
        StackAddresses = []
        for Address in Self.master.Sim.Mem.keys() :
            if Address < Self.master.Sim.StackBase :
                DataAddresses.append(Address)
            else :
                StackAddresses.append(Address)
        DataAddresses.sort()
        StackAddresses.sort()
        return DataAddresses, StackAddresses

######################### Message Pane #########################

class MessagePane(Frame) :
    def __init__(Self, Parent) :
        Frame.__init__(Self, Parent)
        Sbar = Scrollbar(Self, orient='vertical')
        Self.Msgs = Text(Self, wrap='none', undo=True, height=3)
        Sbar.pack(side=RIGHT, fill=Y)
        Self.Msgs.pack(side=TOP, fill=BOTH, expand=YES)
        Self.Msgs.config(yscrollcommand=Sbar.set)
        Sbar.config(command=Self.Msgs.yview)
        Self.Msgs.config(font=('courier', Parent.FontSize, Parent.FontFace))
        Self.Msgs.tag_config('Warning', background='yellow')
        Self.Msgs.tag_config('Error', background='red')
        Self.Msgs.config(state='disabled')

    def Refresh(Self) :
        """ This routine clears the message window (text widget). """
        Self.Msgs.config(state='normal')
        Self.Msgs.delete('1.0', END)
        Self.Msgs.config(state='disabled')

    def Print_Message(Self, String) :
        """ This routine prints a message in the MessageView. """
        Self.Msgs.config(state='normal')
        if not '1.0' == Self.Msgs.index(INSERT) :
            Self.Msgs.insert(INSERT, '\n')
        Self.Msgs.insert(INSERT, String)
        Self.Msgs.see(INSERT)
        Self.Msgs.config(state='disabled')

    def Print_Warning(Self, String) :
        """ This routine prints a warning in the MessageView. """
        Self.Msgs.config(state='normal')
        if not '1.0' == Self.Msgs.index(INSERT) :
            Self.Msgs.insert(INSERT, '\n')
        Start = Self.Msgs.index(INSERT)
        Self.Msgs.insert(INSERT, String)
        Self.Msgs.tag_add('Warning', Start, INSERT)
        Self.Msgs.see(INSERT)
        Self.Msgs.config(state='disabled')

    def Print_Error(Self, String) :
        """ This routine prints an error in the MessageView. """
        Self.Msgs.config(state='normal')
        if not '1.0' == Self.Msgs.index(INSERT) :
            Self.Msgs.insert(INSERT, '\n')
        Start = Self.Msgs.index(INSERT)
        Self.Msgs.insert(INSERT, String)
        Self.Msgs.tag_add('Error', Start, INSERT)
        Self.Msgs.see(INSERT)
        Self.Msgs.config(state='disabled')
