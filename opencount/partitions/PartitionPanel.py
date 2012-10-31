import sys, os, pdb, traceback, threading, Queue
try:
    import cPickle as pickle
except:
    import pickle

from os.path import join as pathjoin
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib.pubsub import Publisher

sys.path.append('..')

import util
import barcode.partition_imgs as partition_imgs

BALLOT_VENDORS = ("Diebold", "Hart", "Sequoia")

class PartitionMainPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.proj = None

        self.init_ui()

    def init_ui(self):
        self.partitionpanel = PartitionPanel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.partitionpanel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Layout()

    def start(self, proj, stateP):
        self.proj = proj
        self.partitionpanel.start(self.proj, self.proj.voteddir, stateP)
        self.proj.addCloseEvent(self.partitionpanel.save_session)
    def stop(self):
        self.partitionpanel.save_session()
        self.proj.removeCloseEvent(self.partitionpanel.save_session)
        self.export_results()
    def export_results(self):
        partition_outP = pathjoin(self.proj.projdir_path, self.proj.partitions)
        pickle.dump(self.partitionpanel.partitioning, open(partition_outP, 'wb'),
                    pickle.HIGHEST_PROTOCOL)
        
class PartitionPanel(ScrolledPanel):
    PARTITION_JOBID = util.GaugeID("PartitionJobId")

    def __init__(self, parent, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        
        self.voteddir = None
        # PARTITIONING: maps {partitionID: [imgpath_i, ...]}
        self.partitioning = None

        self.init_ui()

    def init_ui(self):
        txt0 = wx.StaticText(self, label="What is the ballot vendor?")
        self.vendor_dropdown = wx.ComboBox(self, style=wx.CB_READONLY, choices=BALLOT_VENDORS)
        sizer0 = wx.BoxSizer(wx.HORIZONTAL)
        sizer0.AddMany([(txt0,), (self.vendor_dropdown,)])

        self.sizer_stats = wx.BoxSizer(wx.HORIZONTAL)
        txt1 = wx.StaticText(self, label="Number of Partitions: ")
        self.num_partitions_txt = wx.StaticText(self)
        self.sizer_stats.AddMany([(txt1,), (self.num_partitions_txt,)])
        self.sizer_stats.ShowItems(False)

        btn_run = wx.Button(self, label="Run Partitioning...")
        btn_run.Bind(wx.EVT_BUTTON, self.onButton_run)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddMany([(btn_run,)])
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddMany([(sizer0,), (self.sizer_stats,), (btn_sizer,)])
        self.SetSizer(self.sizer)
        self.Layout()
        self.SetupScrolling()

    def start(self, proj, voteddir, stateP='_state_partition.p'):
        """ 
        Input:
            str VOTEDDIR: Root directory of voted ballots.
        """
        self.proj = proj
        self.voteddir = voteddir
        self.stateP = stateP
        self.restore_session()
        
    def stop(self):
        self.save_session()

    def restore_session(self):
        try:
            state = pickle.load(open(self.stateP, 'rb'))
            self.voteddir = state['voteddir']
            self.vendor = state['vendor']
            self.partitioning = state['partitioning']
            self.vendor_dropdown.SetStringSelection(self.vendor)
            if self.partitioning != None:
                self.num_partitions_txt.SetLabel(str(len(self.partitioning)))
                self.sizer_stats.ShowItems(True)
                self.Layout()
        except:
            return False
        return True
    def save_session(self):
        print "...PartitionPanel: Saving state..."
        state = {'voteddir': self.voteddir,
                 'vendor': self.vendor_dropdown.GetStringSelection(),
                 'partitioning': self.partitioning}
        pickle.dump(state, open(self.stateP, 'wb'))

    def onButton_run(self, evt):
        class PartitionThread(threading.Thread):
            def __init__(self, voteddir, vendor, callback, jobid, queue, tlisten, *args, **kwargs):
                threading.Thread.__init__(self, *args, **kwargs)
                self.voteddir = voteddir
                self.vendor = vendor
                self.callback = callback
                self.jobid = jobid
                self.queue = queue
                self.tlisten = tlisten
            def run(self):
                partitioning = partition_imgs.partition_imgs(self.voteddir, vendor=vendor, queue=queue)
                wx.CallAfter(Publisher().sendMessage, "signals.MyGauge.done", (self.jobid,))
                wx.CallAfter(self.callback, partitioning)
                self.tlisten.stop()
        class ListenThread(threading.Thread):
            def __init__(self, queue, jobid, *args, **kwargs):
                threading.Thread.__init__(self, *args, **kwargs)
                self.queue = queue
                self.jobid = jobid
                self._stop = threading.Event()
            def stop(self):
                print "...ListenThread: Someone called my stop()..."
                self._stop.set()
            def is_stopped(self):
                return self._stop.isSet()
            def run(self):
                while True:
                    if self.is_stopped():
                        print "...ListenThread: Stopping."
                        return
                    try:
                        val = self.queue.get(block=True, timeout=1)
                        if val == True:
                            wx.CallAfter(Publisher().sendMessage, "signals.MyGauge.tick", (self.jobid,))
                    except Queue.Empty:
                        pass

        vendor = self.vendor_dropdown.GetValue()
        b2imgs = pickle.load(open(self.proj.ballot_to_images, 'rb'))
        # TODO: Assume that relevant information is on the first page
        for ballotid, imgpaths in b2imgs.iteritems():
            imgpaths.append(imgpaths[0])
        queue = Queue.Queue()
        tlisten = ListenThread(queue, self.PARTITION_JOBID)

        t = PartitionThread(imgpaths, vendor, self.on_partitiondone,
                            self.PARTITION_JOBID, queue, tlisten)
        numtasks = len(imgpaths)
        gauge = util.MyGauge(self, 1, thread=t, msg="Running Partitioning...",
                             job_id=self.PARTITION_JOBID)
        tlisten.start()
        t.start()
        gauge.Show()
        wx.CallAfter(Publisher().sendMessage, "signals.MyGauge.nextjob", (numtasks, self.PARTITION_JOBID))
        
    def on_partitiondone(self, partitioning):
        print "...Partitioning Done..."
        print partitioning
        self.partitioning = partitioning
        self.num_partitions_txt.SetLabel(str(len(partitioning)))
        self.sizer_stats.ShowItems(True)
        self.Layout()


        
        
