import os, sys, pdb, traceback
try:
    import cPickle as pickle
except:
    import pickle

import wx
from wx.lib.scrolledpanel import ScrolledPanel

sys.path.append('..')
import util
import specify_voting_targets.select_targets as select_targets

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
        b2imgs = pickle.load(open(self.proj.ballot_to_images, 'rb'))
        # 0.) Create the BALLOT_SIDES list of lists:
        #     [[imgP_i_side0, ...], [imgP_i_side1, ...]]
        ballot_sides = []
        for idx, (ballotid, imgpaths) in enumerate(b2imgs.iteritems()):
            if idx > 5:
                break
            for i, imgpath in enumerate(imgpaths):
                if i == len(ballot_sides):
                    ballot_sides.append([imgpath])
                else:
                    ballot_sides[i].append(imgpath)

        self.defineattrs.start(ballot_sides, stateP)

    def stop(self):
        self.defineattrs.save_session()
        self.proj.removeCloseEvent(self.defineattrs.save_session)
        self.export_results()

    def export_results(self):
        pass
        
class DefineAttributesPanel(ScrolledPanel):
    def __init__(self, parent, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        
        # BOXES_MAP: {int side: [Box_i, ...]}
        self.boxes_map = None
        # BALLOTS: [[imgpath_i_front, ...], ...]
        self.ballots = None

        # CUR_SIDE: Which side we're displaying
        self.cur_side = 0
        # CUR_I: Index into self.BALLOTS[self.CUR_SIDE] that we're displaying
        self.cur_i = 0

        self.stateP = None

        self.init_ui()
    
    def init_ui(self):
        self.toolbar = ToolBar(self)
        self.boxdraw = select_targets.BoxDrawPanel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.toolbar)
        self.sizer.Add(self.boxdraw, proportion=1, flag=wx.EXPAND)

        self.SetSizer(self.sizer)
        self.Layout()
        self.SetupScrolling()

    def start(self, ballot_sides, stateP):
        """
        Input:
            list BALLOT_SIDES: [[imgP_i_side0, ...], [imgP_i_side1, ...] ...], i.e. a list of 
                candidate ballots (includes all sides) to display.
            str STATEP:
        """
        self.stateP = stateP
        self.ballot_sides = ballot_sides
        if not self.restore_session():
            self.boxes_map = {}
        self.cur_i = 0
        self.cur_side = 0
        self.display_image(self.cur_side, self.cur_i)

    def stop(self):
        pass

    def restore_session(self):
        try:
            state = pickle.load(open(self.stateP, 'rb'))
            self.boxes_map = state['boxes_map']
            self.ballot_sides = state['ballot_sides']
        except:
            return False
        return True
    def save_session(self):
        # 0.) Add new boxes from self.BOXDRAW to self.BOXES_MAP, if any
        for box in self.boxdraw.boxes:
            if box not in self.boxes_map.get(self.cur_side, []):
                self.boxes_map.setdefault(self.cur_side, []).append(box)
        state = {'boxes_map': self.boxes_map,
                 'ballot_sides': self.ballot_sides}
        pickle.dump(state, open(self.stateP, 'wb'), pickle.HIGHEST_PROTOCOL)

    def display_image(self, cur_side, cur_i):
        """ Displays the CUR_SIDE-side of the CUR_I-th image.
        Input:
            int CUR_SIDE: 
            int CUR_I:
        """
        if cur_side < 0 or cur_side > len(self.ballot_sides):
            return None
        ballots = self.ballot_sides[cur_side]
        if cur_i < 0 or cur_i > len(ballots):
            return None
        # 0.) Add new boxes from self.BOXDRAW to self.BOXES_MAP, if any
        for box in self.boxdraw.boxes:
            if box not in self.boxes_map.get(self.cur_side, []):
                self.boxes_map.setdefault(self.cur_side, []).append(box)
        self.cur_side = cur_side
        self.cur_i = cur_i
        imgpath = ballots[cur_i]
        boxes = self.boxes_map.get(cur_side, [])
        wximg = wx.Image(imgpath, wx.BITMAP_TYPE_ANY)
        self.boxdraw.set_image(wximg)
        self.boxdraw.set_boxes(boxes)
        
    def next_side(self):
        pass
    def prev_side(self):
        pass
    def next_img(self):
        pass
    def prev_img(self):
        pass
    

class ToolBar(wx.Panel):
    pass

def main():
    pass

if __name__ == '__main__':
    main()


