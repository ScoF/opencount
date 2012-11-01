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
    # NUM_EXMPLS: Number of exemplars to grab from each partition
    NUM_EXMPLS = 5

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
        """ Export the partitions_map and partitions_invmap, where
        PARTITIONS_MAP maps {partitionID: [int BallotID_i, ...]}, and
        PARTITIONS_INVMAP maps {int BallotID: partitionID}.
        Also, choose a set of exemplars for each partition and save
        them as PARTITION_EXMPLS: {partitionID: [int BallotID_i, ...]}
        """
        # partitioning: {(str bc_i, ...): [[imgpath_i, isflip_i, bbs_i, info], ...]}
        # sort by first barcode
        partitioning_sorted = sorted(self.partitionpanel.partitioning.items(), key=lambda t: t[0][0])
        partitions_map = {}
        partitions_invmap = {}
        partition_exmpls = {}
        image_to_page = {} # maps {str imgpath: int side}
        img2b = pickle.load(open(self.proj.image_to_ballot, 'rb'))
        for partitionID, (bcs, items) in enumerate(partitioning_sorted):
            partition = set()
            exmpls = set()
            for (imgpath, isflip, bbs, info) in items:
                ballotid = img2b[imgpath]
                partition.add(ballotid)
                if len(exmpls) <= self.NUM_EXMPLS:
                    exmpls.add(ballotid)
                partitions_invmap[ballotid] = partitionID
                image_to_page[imgpath] = info['page']
            partitions_map[partitionID] = list(partition)
            partition_exmpls[partitionID] = sorted(list(exmpls))
        partitions_map_outP = pathjoin(self.proj.projdir_path, self.proj.partitions_map)
        partitions_invmap_outP = pathjoin(self.proj.projdir_path, self.proj.partitions_invmap)
        partition_exmpls_outP = pathjoin(self.proj.projdir_path, self.proj.partition_exmpls)
        pickle.dump(partitions_map, open(partitions_map_outP, 'wb'),
                    pickle.HIGHEST_PROTOCOL)
        pickle.dump(partitions_invmap, open(partitions_invmap_outP, 'wb'),
                    pickle.HIGHEST_PROTOCOL)
        pickle.dump(image_to_page, open(pathjoin(self.proj.projdir_path,
                                                 self.proj.image_to_page), 'wb'),
                    pickle.HIGHEST_PROTOCOL)
        pickle.dump(partition_exmpls, open(partition_exmpls_outP, 'wb'),
                    pickle.HIGHEST_PROTOCOL)
        
class PartitionPanel(ScrolledPanel):
    PARTITION_JOBID = util.GaugeID("PartitionJobId")

    def __init__(self, parent, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        
        self.voteddir = None
        # PARTITIONING: maps {(str bc_i, ...): [[imgpath_i, isflip_i, bbs_i, info], ...]}
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
            def __init__(self, imgpaths, vendor, callback, jobid, queue, tlisten, *args, **kwargs):
                threading.Thread.__init__(self, *args, **kwargs)
                self.imgpaths = imgpaths
                self.vendor = vendor
                self.callback = callback
                self.jobid = jobid
                self.queue = queue
                self.tlisten = tlisten
            def run(self):
                partitioning = partition_imgs.partition_imgs(self.imgpaths, vendor=vendor, queue=queue)
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
        votedpaths = []
        for ballotid, imgpaths in b2imgs.iteritems():
            votedpaths.append(imgpaths[0])
        queue = Queue.Queue()
        tlisten = ListenThread(queue, self.PARTITION_JOBID)

        t = PartitionThread(votedpaths, vendor, self.on_partitiondone,
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


        
        
