import os, sys, pdb, traceback
try:
    import cPickle as pickle
except:
    import pickle

import wx
from wx.lib.scrolled import ScrolledPanel

class DefineAttributesMainPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.init_ui()

    def init_ui(self):
        self.defineattrs = DefineAttributesPanel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.defineattrs, proportion=1, flag=wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Layout()

    def start(self, proj, stateP):
        self.proj = proj
        self.proj.addCloseEvent(self.defineattrs.save_session)
        self.defineattrs.start(stateP)

    def stop(self):
        self.proj.removeCloseEvent(self.defineattrs.save_session)
        self.export_results()

    def export_results(self):
        pass
        
class DefineAttributesPanel(ScrolledPanel):
    def __init__(self, parent, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        
        self.stateP = None

        self.init_ui()
    
    def init_ui(self):
        pass

    def start(self, stateP):
        self.stateP = stateP

    def stop(self):
        pass

    def restore_session(self):
        pass
    def save_session(self):
        pass


def main():
    pass

if __name__ == '__main__':
    main()


