# MiSaSiM Simulator
# Written by Linda and Scott Wills
# (c) 2004-2012 Scott & Linda Wills
# All rights reserved.

from Tkinter        import *
from tkMessageBox   import *
from urllib         import urlopen, urlretrieve
from os             import listdir, mkdir, remove, rename
from sys            import version

MiSaSiMURL = 'http://www.ece.gatech.edu/~scotty/misasim/'
Version = 2.31
ReqPython = ["2.6", "2.7"]

class Manager () :
    """ This class supports installation, upgrading and maintanance, and running
    of MiSaSiM. """
    def __init__(Self, Version, URL) :
        Self.Run = False
        PyVersion = Self.Get_Python_Version()
        WebVersion = Self.Get_Version(URL)
        BinDir, AsmDir = Self.Get_Dirs()
        if PyVersion not in ReqPython :
            print "WARNING: MiSaSiM needs Python %s or %s; Python %s installed" % (ReqPython[0], ReqPython[1], PyVersion)
        elif WebVersion :
            if BinDir == "../bin/" and Version == WebVersion and PyVersion in ReqPython :
                Self.Run = True
            elif not BinDir :
                print "installing MiSaSiM ..."
                BinDir, AsmDir = Self.Create_Dirs()
                Self.Install(URL, PyVersion, BinDir, AsmDir)
                remove("./Misasim.py")
            elif Version <> WebVersion :
                print "upgrading MiSaSiM to version %.2f ..." % (WebVersion)
                if not AsmDir :
                    print "creating ../asm ..."
                    mkdir("../asm")
                    AsmDir = "../asm/"
                Self.Install(URL, PyVersion, BinDir, AsmDir)
        else :
            print "cannot access MiSaSiM website"
            if BinDir == "../bin" :
                "running current version"
                Self.Run = True
            else :
                "check internet access; if okay, the website must be down ... sorry"

    def Get_Version (Self, URL) :
        """ This routine attempts to download the web version number from
        the web. If it fails, the web version number is set to None. """
        try :
            return float(urlopen(URL + 'version.txt').read())
        except IOError :
            return None

    def Get_Python_Version(Self) :
        """ This routine returns the pcurrent executing python version and first
        subversion as a text string (e.g., "2.6"). """
        return version[:3]

    def Get_Dirs(Self) :
        """ This routine returns the bin and asm directories. If they don't exist,
        None is returned. """
        Items = listdir("..")
        BinDir = AsmDir = None
        if 'bin' in Items :
            BinDir = '../bin/'
        if 'asm' in Items :
            AsmDir = '../asm/'
        return (BinDir, AsmDir)

    def Create_Dirs(Self) :
        """ This routine creates the bin and asm directories relative to the
        location of this function. """
        Items = listdir('.')
        if "Misasim" not in Items :
            print "creating ./Misasim ..."
            mkdir("./Misasim")
        Items = listdir('./Misasim')
        if "bin" not in Items :
            print "creating ./Misasim/bin ..."
            mkdir("./Misasim/bin")
        if "asm" not in Items :
            print "creating ./Misasim/asm ..."
            mkdir("./Misasim/asm")
        return ("Misasim/bin/", "Misasim/asm/")

    def Install(Self, URL, PyVersion, BinDir, AsmDir) :
        """ This routine populates the bin and asm sites with files from the MiSaSiM
        website. If files already exist, they are renamed. """
        BinItems = listdir(BinDir)
        AsmItems = listdir(AsmDir)
        for FileName in urlopen(URL + 'manifest.txt') :
            FileName = FileName[:-1]
            if FileName[-4:] == ".asm" :
                Self.Upgrade(URL, FileName, AsmDir, AsmItems)
            elif FileName[-4:] == ".pyc" :
                Self.Upgrade(URL + PyVersion + '/', FileName, BinDir, BinItems)
            elif FileName <> "" :
                Self.Upgrade(URL, FileName, BinDir, BinItems)
        print "installation complete"

    def Upgrade(Self, URL, FileName, Dir, ExistingItems) :
        """ This routine upgrades a filename from the web. If it already exists locally,
        it is renamed. """
        print "downloading %s into %s" % (FileName, Dir)
        if FileName in ExistingItems :
            OldFileName = FileName + '~'
            if OldFileName in ExistingItems :
                remove(Dir + OldFileName)
            rename(Dir + FileName, Dir + OldFileName)
        urlretrieve(URL + FileName, Dir + FileName)

if __name__ == '__main__':
    Mgr = Manager(Version, MiSaSiMURL)
    if Mgr.Run :
        from UserInterface import *
        Main = MiSaSiM(Version)
        Main.mainloop()
    else :
        raw_input('press ENTER to continue ...')

