import os, sys, time, pdb, traceback
try:
    import cPickle as pickle
except ImportError as e:
    import pickle

import wx
from wx.lib.scrolledpanel import ScrolledPanel

sys.path.append('..')
from tab_wrap import tab_wrap
from projconfig_new.ProjectPanel import ProjectPanel, Project
from projconfig_new.ConfigPanel import ConfigPanel
from partitions.PartitionPanel import PartitionMainPanel
from specify_voting_targets.select_targets import SelectTargetsMainPanel
from labelcontest.labelcontest import LabelContest
from grouping.define_attributes import DefineAttributesPanel
from grouping.select_attributes import SelectAttributesMasterPanel
from digits_ui.digits_ui import LabelDigitsPanel
from grouping.verify_grouping import GroupingMasterPanel
from runtargets.runtargets import RunTargets
from threshold.threshold import ThresholdPanel
from quarantine.quarantinepanel import QuarantinePanel
from post_processing.postprocess import ResultsPanel

PROJROOTDIR = 'projects_new'

class MainFrame(wx.Frame):
    PROJECT = 0
    CONFIG = 1
    PARTITION = 2
    SELTARGETS = 3
    DEFINE_ATTRS = 4
    LABEL_ATTRS = 5
    LABEL_DIGATTRS = 6
    CORRECT_GROUPING = 7
    LABEL_CONTESTS = 8
    RUN = 9
    QUARANTINE = 10
    PROCESS = 11

    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        
        # PROJECT: Current Project being worked on.
        self.project = None

        self.init_ui()
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChange)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.notebook.ChangeSelection(0)
        self.notebook.SendPageChangedEvent(-1, 0)

    def init_ui(self):
        self.notebook = wx.Notebook(self)
        self.setup_pages()

    def setup_pages(self):
        self.panel_projects = ProjectPanel(self.notebook)
        self.panel_config = ConfigPanel(self.notebook)
        self.panel_partition = PartitionMainPanel(self.notebook)
        self.panel_seltargets = SelectTargetsMainPanel(self.notebook)
        self.panel_define_attrs = DefineAttributesPanel(self.notebook)
        self.panel_define_attrs.unsubscribe_pubsubs()
        self.panel_label_attrs = SelectAttributesMasterPanel(self.notebook)
        self.panel_label_digitattrs = tab_wrap(LabelDigitsPanel)(self.notebook)
        self.panel_correct_grouping = GroupingMasterPanel(self.notebook)
        self.panel_label_contests = tab_wrap(LabelContest)(self.notebook)
        self.panel_run = RunTargets(self.notebook)
        self.panel_set_threshold = tab_wrap(ThresholdPanel)(self.notebook)
        self.panel_quarantine = QuarantinePanel(self.notebook)
        self.panel_process = ResultsPanel(self.notebook)
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
        for panel, text in self.pages:
            self.notebook.AddPage(panel, text)
        
    def onPageChange(self, evt):
        old = evt.GetOldSelection()
        new = evt.GetSelection()

        if old == MainFrame.PROJECT:
            self.project = self.panel_projects.get_project()
        
        if new == MainFrame.PROJECT:
            self.panel_projects.start(PROJROOTDIR)
        elif new == MainFrame.CONFIG:
            self.panel_config.start(self.project)
        elif new == MainFrame.PARTITION:
            self.panel_partition.start(self.project)
        elif new == MainFrame.SELTARGETS:
            pass
        elif new == MainFrame.DEFINE_ATTRS:
            pass
        elif new == MainFrame.LABEL_ATTRS:
            pass
        elif new == MainFrame.LABEL_DIGATTRS:
            pass
        elif new == MainFrame.CORRECT_GROUPING:
            pass
        elif new == MainFrame.LABEL_CONTESTS:
            pass
        elif new == MainFrame.RUN:
            pass
        elif new == MainFrame.QUARANTINE:
            pass
        elif new == MainFrame.PROCESS:
            pass

    def onClose(self, evt):
        """
        Triggered when the user/program exits/closes the MainFrame.
        """
        if self.project:
            self.project.save()
        if self.notebook.GetCurrentPage() == self.panel_define_attrs:
            self.panel_define_attrs.stop()
        for fn in Project.closehook:
            fn()
        evt.Skip()

def main():
    app = wx.App(False)
    f = MainFrame(None)
    f.Show()
    f.Maximize()
    app.MainLoop()

if __name__ == '__main__':
    main()
