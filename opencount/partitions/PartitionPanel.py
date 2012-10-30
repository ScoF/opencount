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

    def start(self, proj):
        self.proj = proj
        self.partitionpanel.start(self.proj.voteddir)
    def stop(self):
        pass
        
class PartitionPanel(ScrolledPanel):
    PARTITION_JOBID = util.GaugeID("PartitionJobId")

    def __init__(self, parent, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        
        self.voteddir = None
        self.init_ui()

    def init_ui(self):
        txt0 = wx.StaticText(self, label="What is the ballot vendor?")
        self.vendor_dropdown = wx.ComboBox(self, style=wx.CB_READONLY, choices=BALLOT_VENDORS)
        sizer0 = wx.BoxSizer(wx.HORIZONTAL)
        sizer0.AddMany([(txt0,), (self.vendor_dropdown,)])

        btn_run = wx.Button(self, label="Run Partitioning...")
        btn_run.Bind(wx.EVT_BUTTON, self.onButton_run)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddMany([(btn_run,)])
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddMany([(sizer0,), (btn_sizer,)])
        self.SetSizer(self.sizer)
        self.Layout()
        self.SetupScrolling()

    def start(self, voteddir):
        """ 
        Input:
            str VOTEDDIR: Root directory of voted ballots.
        """
        self.voteddir = voteddir
        
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
        imgpaths = []
        for dirpath, dirnames, filenames in os.walk(self.voteddir):
            for imgname in [f for f in filenames if util.is_image_ext(f)]:
                imgpaths.append(pathjoin(dirpath, imgname))
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


        
        
