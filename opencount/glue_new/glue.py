import os, sys, time, pdb, traceback
try:
    import cPickle as pickle
except ImportError as e:
    import pickle

import wx
from wx.lib.scrolledpanel import ScrolledPanel
print 'hi'
sys.path.append('..')
print 'hi'

from ProjectPanel import ProjectPanel
from ConfigPanel import ConfigPanel
from PartitionPanel import PartitionPanel
from specify_voting_targets.select_targets import SelectTargetsMainPanel
#from labelcontest.labelcontest import LabelContest
from grouping.define_attributes import DefineAttributesPanel
#from grouping.select_attributes import SelectAttributesMasterPanel
#from digits_ui.digits_ui import LabelDigitsPanel
#from grouping.verify_grouping import GroupingMasterPanel
#from runtargets.runtargets import RunTargets
#from quarantine.quarantinepanel import QuarantinePanel
#from post_processing.postprocess import ResultsPanel

print 'hi' 
class MainFrame(wx.Frame):
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        
        self.init_ui()

    def init_ui(self):
        self.notebook = wx.Notebook(self)
        self.setup_pages()

    def setup_pages(self):
        self.panel_projects = ProjectPanel(self.notebook)
        self.panel_config = ConfigPanel(self.notebook)
        self.panel_partition = PartitionPanel(self.notebook)
        self.panel_seltargets = SelectTargetsMainPanel(self.notebook)
        self.panel_define_attrs = DefineAttributesPanel(notebook)
        self.panel_define_attrs.unsubscribe_pubsubs()
        self.panel_label_attrs = SelectAttributesMasterPanel(notebook)
        self.panel_label_digitattrs = tab_wrap(LabelDigitsPanel)(notebook)
        self.panel_correct_grouping = GroupingMasterPanel(notebook)
        self.panel_label_contests = tab_wrap(LabelContest)(notebook)
        self.panel_run = RunTargets(notebook)
        self.panel_set_threshold = tab_wrap(ThresholdPanel)(notebook)
        self.panel_quarantine = QuarantinePanel(notebook)
        self.panel_process = ResultsPanel(notebook)
        self.pages = [(self.panel_projects, "Projects"),
                      (self.panel_config, "Import Files"), 
                      (self.panel_partition, "Partition ballots"),
                      (self.panel_seltargets, "Select Voting Targets"),
                      (self.panel_define_attrs, "Define Ballot Attributes"),
                      (self.panel_label_attrs, "Label Ballot Attributes"),
                      (self.panel_label_digitattrs, "Label Digit-Based Attributes"),
                      (self.panel_label_contests, "Label Contests"),
                      (self.panel_correct_grouping, "Correct Grouping"),
                      (self.panel_run, "Extract Targets"),
                      (self.panel_set_threshold, "Set Threshold"),
                      (self.panel_quarantine, "Process Quarantine"),
                      (self.panel_process, "Results")]
        for panel, text in self.pages[1:]:
            notebook.AddPage(panel, text)
        
print 'hi'

def main():
    app = wx.App(False)
    f = MainFrame(None)
    f.Show()
    f.Maximize()
    app.MainLoop()

if __name__ == '__main__':
    print 'meow'
    main()

print 'hi'
