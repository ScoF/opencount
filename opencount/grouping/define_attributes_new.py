import os, sys, pdb, traceback, re
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
        self.boxdraw = DrawAttrBoxPanel(self)
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
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.init_ui()

    def init_ui(self):
        btn_addattr = wx.Button(self, label="Add Attribute")
        btn_addattr.Bind(wx.EVT_BUTTON, self.onButton_addattr)
        btn_modify = wx.Button(self, label="Modify")
        btn_modify.Bind(wx.EVT_BUTTON, self.onButton_modify)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddMany([(btn_addattr,), (btn_modify,)])

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(btn_sizer)

        self.SetSizer(self.sizer)
        self.Layout()
    def onButton_addattr(self, evt):
        boxdrawpanel = self.GetParent().boxdraw
        boxdrawpanel.set_mode_m(boxdrawpanel.M_CREATE)
    def onButton_modify(self, evt):
        boxdrawpanel = self.GetParent().boxdraw
        boxdrawpanel.set_mode_m(boxdrawpanel.M_IDLE)

class DrawAttrBoxPanel(select_targets.BoxDrawPanel):
    def __init__(self, parent, *args, **kwargs):
        select_targets.BoxDrawPanel.__init__(self, parent, *args, **kwargs)

    def onLeftDown(self, evt):
        self.SetFocus()
        x, y = self.CalcUnscrolledPosition(evt.GetPositionTuple())
        if self.mode_m == self.M_CREATE:
            print "...Creating Attr Box..."
            self.startBox(x, y, AttrBox)
        elif self.mode_m == self.M_IDLE and not self.sel_boxes:
            boxes = self.get_boxes_within(x, y, mode='any')
            if boxes:
                self.select_boxes(boxes[0][0])
            else:
                self.startBox(x, y, select_targets.SelectionBox)
    def onLeftUp(self, evt):
        x, y = self.CalcUnscrolledPosition(evt.GetPositionTuple())
        self.clear_selected()
        if self.mode_m == self.M_CREATE and self.isCreate:
            box = self.finishBox(x, y)
            dlg = DefineAttributeDialog(self)
            status = dlg.ShowModal()
            if status == wx.ID_CANCEL:
                self.Refresh()
                return
            box.attrtypes = dlg.results
            box.is_digitbased = dlg.is_digitbased
            box.num_digits = dlg.num_digits
            box.is_tabulationonly = dlg.is_tabulationonly
            label = ', '.join(box.attrtypes)
            if box.is_digitbased:
                label += ' (DigitBased)'
            if box.is_tabulationonly:
                label += ' (TabulationOnly)'
            box.label = label
            self.boxes.append(box)
        elif self.mode_m == self.M_IDLE and self.isCreate:
            box = self.finishBox(x, y)
            boxes = select_targets.get_boxes_within(self.boxes, box)
            print "...Selecting {0} boxes.".format(len(boxes))
            self.select_boxes(*boxes)
        self.Refresh()

    def drawBox(self, box, dc):
        select_targets.BoxDrawPanel.drawBox(self, box, dc)
        if isinstance(box, AttrBox):
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetTextForeground("Blue")
            w = int(round(abs(box.x2 - box.x1) * self.scale))
            h = int(round(abs(box.y2 - box.y1) * self.scale))
            client_x, client_y = self.img2c(box.x1, box.y1)            
            w_txt, h_txt = dc.GetTextExtent(box.label)
            x_txt, y_txt = client_x, client_y - h_txt
            if y_txt < 0:
                y_txt = client_y + h
            dc.DrawText(box.label, x_txt, y_txt)
        
class AttrBox(select_targets.Box):
    def __init__(self, x1, y1, x2, y2, is_sel=False, label=''):
        select_targets.Box.__init__(self, x1, y1, x2, y2)
        self.is_sel = is_sel
        self.label = label
        self.attrtypes = None
        self.is_digitbased = None
        self.num_digits = None
        self.is_tabulationonly = None
    def __str__(self):
        return "AttrBox({0},{1},{2},{3},{4})".format(self.x1, self.y1, self.x2, self.y2, self.label)
    def __repr__(self):
        return "AttrBox({0},{1},{2},{3},{4})".format(self.x1, self.y1, self.x2, self.y2, self.label)
    def __eq__(self, o):
        return (isinstance(o, AttrBox) and self.x1 == o.x1 and self.x2 == o.x2
                and self.y1 == o.y1 and self.y2 == o.y2 and self.label == o.label)
    def copy(self):
        return AttrBox(self.x1, self.y1, self.x2, self.y2, label=self.label)
    def get_draw_opts(self):
        if self.is_sel:
            return ("Yellow", 3)
        else:
            return ("Green", 3)

class DefineAttributeDialog(wx.Dialog):
    """
    A dialog to allow the user to add attribute types to a 
    bounding box.
    """
    def __init__(self, parent, message="Please enter your input(s).", 
                 vals=('',),
                 can_add_more=False,
                 *args, **kwargs):
        """
        vals: An optional list of values to pre-populate the inputs.
        can_add_more: If True, allow the user to add more text entry
                      fields.
        """
        wx.Dialog.__init__(self, parent, title='Input required', *args, **kwargs)
        self.parent = parent
        self.results = []
        self._panel_btn = None
        self.btn_ok = None
        self.is_digitbased = False
        self.num_digits = None
        self.is_tabulationonly = False

        self.input_pairs = []
        for idx, val in enumerate(vals):
            txt = wx.StaticText(self, label="Attribute {0}:".format(idx))
            input_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
            if idx == len(vals) - 1:
                input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.onButton_ok)
            input_ctrl.SetValue(vals[idx])
            self.input_pairs.append((txt, input_ctrl))
        if not self.input_pairs:
            txt = wx.StaticText(self, label="Attribute 0")
            input_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
            input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.onButton_ok)
            self.input_pairs.append((txt, input_ctrl))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        caption_txt = wx.StaticText(self, label=message)
        self.sizer.Add(caption_txt, border=10, flag=wx.ALL)
        gridsizer = wx.GridSizer(rows=0, cols=2, hgap=5, vgap=3)
        btn_add = wx.Button(self, label="+")
        self.btn_add = btn_add
        btn_add.Bind(wx.EVT_BUTTON, self.onButton_add)
        btn_add.Bind(wx.EVT_SET_FOCUS, self.onAddButtonFocus)
        
        horizsizer = wx.BoxSizer(wx.HORIZONTAL)
        horizsizer.Add(btn_add, proportion=0, flag=wx.ALIGN_LEFT | wx.ALIGN_TOP)

        gridsizer.Add(self.input_pairs[0][0])
        gridsizer.Add(self.input_pairs[0][1])
        horizsizer.Add(gridsizer)
        for txt, input_ctrl in self.input_pairs[1:]:
            gridsizer.Add((1,1))
            gridsizer.Add(txt, border=10, flag=wx.ALL)
            gridsizer.Add(input_ctrl, border=10, flag=wx.ALL)
        self.gridsizer = gridsizer
        self.sizer.Add(horizsizer)
        
        self.chkbox_is_digitbased = wx.CheckBox(self, label="Is this a digit-based precinct patch?")
        self.chkbox_is_tabulationonly = wx.CheckBox(self, label="Should \
this patch be only used for tabulation (and not for grouping)?")
        numdigits_label = wx.StaticText(self, label="Number of Digits:")
        self.numdigits_label = numdigits_label
        self.num_digits_ctrl = wx.TextCtrl(self, value='')
        digit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        digit_sizer.Add(self.chkbox_is_digitbased, proportion=0)
        digit_sizer.Add(numdigits_label, proportion=0)
        digit_sizer.Add(self.num_digits_ctrl, proportion=0)
        self.digit_sizer = digit_sizer
        self.sizer.Add(digit_sizer, proportion=0)
        self.sizer.Add(self.chkbox_is_tabulationonly, proportion=0)

        self._add_btn_panel(self.sizer)
        self.SetSizer(self.sizer)
        if not can_add_more:
            btn_add.Hide()
        self.Fit()

        self.input_pairs[0][1].SetFocus()

    def onAddButtonFocus(self, evt):
        """
        Due to tab-traversal issues, do this annoying thing where we
        shift focus away from the '+' button. Sigh.
        """
        if len(self.input_pairs) > 1:
            self.input_pairs[1][1].SetFocus()
        else:
            self.btn_ok.SetFocus()

    def _add_btn_panel(self, sizer):
        """
        Due to tab-traversal issues, do this annoying hack where we
        re-create the button panel every time we dynamically add new
        rows to the dialog.
        """
        if self._panel_btn:
            sizer.Remove(self._panel_btn)
            self._panel_btn.Destroy()
            self._panel_btn = None
        panel_btn = wx.Panel(self)
        self._panel_btn = panel_btn
        btn_ok = wx.Button(panel_btn, id=wx.ID_OK)
        btn_ok.Bind(wx.EVT_BUTTON, self.onButton_ok)
        self.btn_ok = btn_ok
        btn_cancel = wx.Button(panel_btn, id=wx.ID_CANCEL)
        btn_cancel.Bind(wx.EVT_BUTTON, self.onButton_cancel)
        panel_btn.sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel_btn.sizer.Add(btn_ok, border=10, flag=wx.RIGHT)
        panel_btn.sizer.Add(btn_cancel, border=10, flag=wx.LEFT)
        panel_btn.SetSizer(panel_btn.sizer)
        sizer.Add(panel_btn, border=10, flag=wx.ALL | wx.ALIGN_CENTER)

    def onButton_ok(self, evt):
        history = set()
        if self.chkbox_is_digitbased.GetValue() == True:
            self.is_digitbased = True
            self.num_digits = int(self.num_digits_ctrl.GetValue())
        if self.chkbox_is_tabulationonly.GetValue() == True:
            self.is_tabulationonly = True
        for txt, input_ctrl in self.input_pairs:
            val = input_ctrl.GetValue()
            if val in history:
                dlg = wx.MessageDialog(self, message="{0} was entered \
more than once. Please correct.".format(val),
                                       style=wx.OK)
                dlg.ShowModal()
                return
            self.results.append(input_ctrl.GetValue())
            history.add(val)
        self.EndModal(wx.ID_OK)

    def onButton_cancel(self, evt):
        self.EndModal(wx.ID_CANCEL)

    def onButton_add(self, evt):
        txt = wx.StaticText(self, label="Attribute {0}:".format(len(self.input_pairs)))
        input_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.onButton_ok)
        self.input_pairs[-1][1].Unbind(wx.EVT_TEXT_ENTER)
        self.input_pairs.append((txt, input_ctrl))
        self.gridsizer.Add(txt)
        self.gridsizer.Add(input_ctrl)
        self._add_btn_panel(self.sizer)
        self.Fit()
        input_ctrl.SetFocus()

class SpreadSheetAttrDialog(DefineAttributeDialog):
    def __init__(self, parent, attrtypes, *args, **kwargs):
        DefineAttributeDialog.__init__(self, parent, *args, **kwargs)

        # The path that the user selected
        self.path = ''

        self.parent = parent
        self.chkbox_is_digitbased.Hide()
        self.num_digits.Hide()
        self.numdigits_label.Hide()
        self.chkbox_is_tabulationonly.Disable()
        self.btn_add.Hide()

        txt = wx.StaticText(self, label="Spreadsheet File:")
        file_inputctrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.file_inputctrl = file_inputctrl
        btn_select = wx.Button(self, label="Select...")
        btn_select.Bind(wx.EVT_BUTTON, self.onButton_selectfile)

        sizer_horiz = wx.BoxSizer(wx.HORIZONTAL)
        txt2 = wx.StaticText(self, label="Custom attr is a 'function' of:")
        self.combobox = wx.ComboBox(self, choices=attrtypes, style=wx.CB_READONLY)
        sizer_horiz.Add(txt2)
        sizer_horiz.Add(self.combobox, proportion=1, flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_file = wx.BoxSizer(wx.HORIZONTAL)
        sizer_file.Add(txt)
        sizer_file.Add((10, 10))
        sizer_file.Add(file_inputctrl, proportion=1, flag=wx.EXPAND)
        sizer_file.Add(btn_select)
        sizer.Add(sizer_file)
        sizer.Add(sizer_horiz)

        self.input_pairs.append((txt, file_inputctrl))

        self.sizer.Insert(len(self.sizer.GetChildren())-1, sizer,
                          proportion=1,
                          border=10,
                          flag=wx.EXPAND | wx.ALL)

        self.Fit()

    def onButton_selectfile(self, evt):
        dlg = wx.FileDialog(self, message="Choose spreadsheet...",
                            defaultDir='.', style=wx.FD_OPEN)
        status = dlg.ShowModal()
        if status == wx.ID_CANCEL:
            return
        path = dlg.GetPath()
        self.file_inputctrl.SetValue(path)
        self.path = path

class FilenameAttrDialog(wx.Dialog):
    """
    Dialog that handles the creation of a Filename-based Custom
    Attribute. The user-input will be a regex-like expression in order
    to extract the 'attribute' from the filename. For instance, to 
    extract the last digit '0' from a filename like:
        329_141_250_145_0.png
    The user-input regex would be:
        r'\d*_\d*_\d*_\d*_(\d*).png'
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        
        # self.attrname is the name of the CustomAttribute
        self.attrname = None
        # self.regex is the user-inputted regex to use
        self.regex = None
        self.is_tabulationonly = False
        self.is_votedonly = False

        sizer = wx.BoxSizer(wx.VERTICAL)

        txt1 = wx.StaticText(self, label="Please enter a Python-style \
regex that will match the attribute value.")
        sizer.Add(txt1)
        sizer.Add((20, 20))

        sizer_input0 = wx.BoxSizer(wx.HORIZONTAL)
        txt0 = wx.StaticText(self, label="Custom Attribute Name:")
        attrname_input = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        attrname_input.Bind(wx.EVT_TEXT_ENTER, lambda evt: re_input.SetFocus())
        self.attrname_input = attrname_input
        sizer_input0.Add(txt0)
        sizer_input0.Add(attrname_input, proportion=1, flag=wx.EXPAND)
        sizer.Add(sizer_input0, flag=wx.EXPAND)
        
        sizer.Add((20, 20))

        sizer_input = wx.BoxSizer(wx.HORIZONTAL)
        txt2 = wx.StaticText(self, label="Regex Pattern:")
        sizer_input.Add(txt2)
        re_input = wx.TextCtrl(self, value=r'\d*_\d*_\d*_\d*_(\d*).png',
                               style=wx.TE_PROCESS_ENTER)
        self.re_input = re_input
        re_input.Bind(wx.EVT_TEXT_ENTER, self.onButton_ok)
        sizer_input.Add(re_input, proportion=1, flag=wx.EXPAND)

        sizer.Add(sizer_input, proportion=1, flag=wx.EXPAND)

        self.is_tabulationonly_chkbox = wx.CheckBox(self, label="Is this \
for Tabulation Only?")
        self.is_votedonly_chkbox = wx.CheckBox(self, label="Does this \
only occur on voted ballots?")
        sizer.Add(self.is_tabulationonly_chkbox)
        sizer.Add(self.is_votedonly_chkbox)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(self, label="Ok")
        btn_ok.Bind(wx.EVT_BUTTON, self.onButton_ok)
        btn_sizer.Add(btn_ok)
        btn_cancel = wx.Button(self, label="Cancel")
        btn_cancel.Bind(wx.EVT_BUTTON, self.onButton_cancel)
        btn_sizer.Add(btn_cancel)

        sizer.Add(btn_sizer, flag=wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        self.Fit()

        self.attrname_input.SetFocus()
        
    def onButton_ok(self, evt):
        self.attrname = self.attrname_input.GetValue()
        self.regex = self.re_input.GetValue()
        self.is_tabulationonly = self.is_tabulationonly_chkbox.GetValue()
        self.is_votedonly = self.is_votedonly_chkbox.GetValue()
        self.EndModal(wx.ID_OK)

    def onButton_cancel(self, evt):
        self.EndModal(wx.ID_CANCEL)
        
def main():
    pass

if __name__ == '__main__':
    main()


