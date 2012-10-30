import os, sys, pdb, traceback
from os.path import join as pathjoin
try:
    import cPickle as pickle
except:
    import pickle
import wx
from wx.lib.pubsub import Publisher

class ConfigPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, style=wx.SIMPLE_BORDER, *args, **kwargs)
        
        # Instance vars
        self.parent = parent
        self.project = None
        self.samplesdir = ""
        
        # Set up widgets
        self.box_samples = wx.StaticBox(self, label="Samples")
        self.box_samples.sizer = wx.StaticBoxSizer(self.box_samples, orient=wx.VERTICAL)
        self.box_samples.txt = wx.StaticText(self, label="Please choose the directory where the sample images reside.")
        self.box_samples.btn = wx.Button(self, label="Choose voted ballot directory...")
        self.box_samples.btn.Bind(wx.EVT_BUTTON, self.onButton_choosesamplesdir)
        self.box_samples.txt2 = wx.StaticText(self, label="Voted ballot directory:")
        self.box_samples.txt_samplespath = wx.StaticText(self)
        self.box_samples.sizer.Add(self.box_samples.txt)
        self.box_samples.sizer.Add(self.box_samples.btn)
        self.box_samples.sizer.Add(self.box_samples.txt2)
        self.box_samples.sizer.Add(self.box_samples.txt_samplespath)
        self.box_samples.Fit()
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.lower_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lower_left_sizer.Add(self.box_samples.sizer, flag=wx.EXPAND)
        self.left_sizer = wx.GridSizer(2, 1, 10, 10)
        self.left_sizer.Add(self.lower_left_sizer, flag=wx.EXPAND)
        self.left_sizer.Add((0,100))
        self.is_double_sided = wx.CheckBox(self, -1, label="Double sided ballots.")
        self.is_double_sided.Bind(wx.EVT_CHECKBOX, self.changeDoubleSided, self.is_double_sided)
        self.left_sizer.Add(self.is_double_sided)
        
        self.is_straightened = wx.CheckBox(self, -1, label="Ballots already straightened.")
        self.is_straightened.Bind(wx.EVT_CHECKBOX, self.onCheck_straightened, self.is_straightened)
        self.left_sizer.Add(self.is_straightened)
        
        self.lower_scroll = wx.ListBox(self)
        self.lower_scroll.box = wx.StaticBox(self, label="For the voted ballots, the following files were skipped:")
        self.lower_scroll.sizer = wx.StaticBoxSizer(self.lower_scroll.box, orient=wx.VERTICAL)
        self.lower_scroll.sizer.Add(self.lower_scroll, 1, flag=wx.EXPAND)
        self.right_sizer = wx.GridSizer(2, 1, 10, 10)
        self.right_sizer.Add(self.lower_scroll.sizer, flag=wx.EXPAND)
        
        self.top_sizer.Add(self.left_sizer, flag=wx.EXPAND)
        self.top_sizer.Add((10, 10))
        self.top_sizer.Add(self.right_sizer, 1, flag=wx.EXPAND)
        
        self.btn_run = wx.Button(self, label="Run sanity check")
        self.btn_run.Bind(wx.EVT_BUTTON, self.onButton_runsanitycheck)
        self.btn_run.box = wx.StaticBox(self)
        self.btn_run.sizer = wx.StaticBoxSizer(self.btn_run.box, orient=wx.VERTICAL)
        self.btn_run.sizer.Add(self.btn_run)
        
        self.sizer.Add(self.top_sizer, 1, flag=wx.EXPAND)
        self.sizer.Add(self.btn_run.sizer, flag=wx.EXPAND)
        
        self.SetSizer(self.sizer)
        self.Fit()

    def start(self, project):
        self.project = project

    def initDoubleSided(self):
        ds = DoubleSided(self, -1)
        ds.regex.SetValue("(.*)")
        ds.finished()
        ds.Destroy()

    def onCheck_straightened(self, evt):
        if not self.project.raw_samplesdir:
            dlg = wx.MessageDialog(self, message="Please select the \
voted ballots directories first.")
            self.Disable()
            dlg.ShowModal()
            self.Enable()
            self.is_straightened.SetValue(False)
            return

        val = self.is_straightened.GetValue()

    def changeDoubleSided(self, x):
        val = self.is_double_sided.GetValue()
        self.project.is_multipage = val
        if val:
            ds = DoubleSided(self, -1)
            ds.Show()

    def wrap(self, text):
        res = ""
        for i in range(0,len(text),50):
            res += text[i:i+50]+"\n"
        return res

    def set_samplepath(self, path):
        self.samplesdir = os.path.abspath(path)
        self.box_samples.txt_samplespath.SetLabel(self.wrap(self.samplesdir))
        self.project.raw_samplesdir = self.samplesdir
        Publisher().sendMessage("processing.register", data=self.project)
    def get_samplepath(self):
        return self.box_samples.txt_samplespath.GetLabelText().replace("\n", "")
        
    def onSanityCheck(self, evt):
        """
        Triggered when either the templates or samples sanity check
        completes. Update the relevant ListBox widget with the results
        of a sanity check.
        """
        type, results_dict = evt.data
        listbox = self.upper_scroll if type == 'templates' else self.lower_scroll
        if len(results_dict) == 0:
            listbox.Append("All files valid")
        else:
            for imgpath, msg in results_dict.items():
                listbox.Append(imgpath + ": " + msg)
        if type == 'samples':
            # Assume that we first process the templates, then the samples last
            TIMER.stop_task(('cpu', MainFrame.map_pages[MainFrame.CONFIG]['cpu']))
            TIMER.start_task(('user', MainFrame.map_pages[MainFrame.CONFIG]['user']))
            self.parent.Enable()

    #### Event Handlers
    def onButton_choosesamplesdir(self, evt):
        dlg = wx.DirDialog(self, "Select Directory", defaultPath=os.getcwd(), style=wx.DD_DEFAULT_STYLE)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            dirpath = dlg.GetPath()
            self.set_samplepath(dirpath)
                
    def onButton_runsanitycheck(self, evt):
        TIMER.stop_task(('user', MainFrame.map_pages[MainFrame.CONFIG]['user']))
        TIMER.start_task(('cpu', MainFrame.map_pages[MainFrame.CONFIG]['cpu']))
        self.upper_scroll.Clear()
        self.lower_scroll.Clear()
        num_files = 0
        for dirpath, dirnames, filenames in os.walk(self.samplesdir):
            num_files += len(filenames)
        self.parent.Disable()
        pgauge = util_widgets.ProgressGauge(self, num_files, msg="Checking files...")
        pgauge.Show()
        thread = threading.Thread(target=sanity_check.sanity_check,
                                  args=(self.samplesdir, self))
        thread.start()

class DoubleSided(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self, parent, id, "Set Double Sided Properties")
        sizer = wx.BoxSizer(wx.VERTICAL)
        t = wx.StaticText(self, -1, "Enter a regex to match on the file name")
        self.regex = wx.TextCtrl(self, -1)
        self.regex.SetValue(r"(.*)-(.*)")
        sizer.Add(t)
        sizer.Add(self.regex)
        t = wx.StaticText(self, -1, "How to construct the similar portion")
        self.part = wx.TextCtrl(self, -1)
        self.part.SetValue(r"\1")
        sizer.Add(t)
        sizer.Add(self.part)
        self.check = wx.CheckBox(self, -1, "Ballots alternate front and back.")
        self.check.Bind(wx.EVT_CHECKBOX, self.togglefrontback)
        sizer.Add(self.check)
        d = wx.Button(self, -1, label="Done")
        d.Bind(wx.EVT_BUTTON, self.finished)
        sizer.Add(d)
        self.SetSizer(sizer)
        self.isalternating = False
    
    def togglefrontback(self, evt):
        self.isalternating = self.check.GetValue()
        if self.isalternating:
            self.regex.Disable()
            self.part.Disable()
        else:
            self.regex.Enable()
            self.part.Enable()

    def finished(self, x=None):
        voteddir_raw = os.path.abspath(self.parent.project.raw_samplesdir)
        blankdir_raw = os.path.abspath(self.parent.project.raw_templatesdir)
        voteddir = os.path.abspath(self.parent.project.votedballots_straightdir)
        blankdir = os.path.abspath(self.parent.project.blankballots_straightdir)

        def get(from_dir, to_dir, load_dir):
            res = []
            for root,_,files in os.walk(load_dir):
                files = [x for x in files if util.is_image_ext(x)]
                # Straightener converts all images to .png
                files = util.replace_exts(files, '.png')
                if len(files)%2 != 0 and self.isalternating:
                    raise Exception("OH NO! Odd number of files in directory %s"%root)
                root = os.path.abspath(root)
                res += [util.to_straightened_path(pathjoin(root, x), from_dir, to_dir) for x in files]
            return res

        images = get(voteddir_raw, voteddir, self.parent.samplesdir)
        templates = get(blankdir_raw, blankdir, self.parent.templatesdir)

        if self.isalternating:
            _imgpath = images[0]
            # Check if paths end in an integer, like:
            #    Pol267-001.png
            #    Pol267-002.png
            #    ...
            pat = re.compile(r'.*[\-_](\d*)\.[a-zA-Z]+$')
            m = pat.match(_imgpath)
            if m == None:
                # Sort by OS-defined way.
                images = sorted(images)
                templates = sorted(templates)
            else:
                # Imgpaths end in an integer, presumably unique+increasing.
                # Sort by the integer's value, not by the OS-specific
                # way (which might 'get it wrong', as what happened in Marin).
                util.sort_nicely(images)
                util.sort_nicely(templates)
            images = dict(zip(images[::2], map(list,zip(images,images[1:]))[::2]))
            templates = dict(zip(templates[::2], map(list,zip(templates,templates[1:]))[::2]))
        else:
            split = self.regex.GetValue()
            join = self.part.GetValue()
            def group(it):
                it = [(re.sub(split, join, x), x) for x in it]
                ht = {}
                for a,b in it:
                    if a not in ht:
                        ht[a] = []
                    ht[a].append(b)
                return ht
            images = group(images)
            templates = group(templates)

        pickle.dump(images, open(self.parent.project.ballot_to_images, "w"))
        pickle.dump(templates, open(self.parent.project.template_to_images, "w"))

        rev_images = {}
        for k,v in images.items():
            for vv in v:
                rev_images[vv] = k
        rev_temp = {}
        for k,v in templates.items():
            for vv in v:
                rev_temp[vv] = k

        pickle.dump(rev_images, open(self.parent.project.image_to_ballot, "w"))
        pickle.dump(rev_temp, open(self.parent.project.image_to_template, "w"))

        self.Destroy()
