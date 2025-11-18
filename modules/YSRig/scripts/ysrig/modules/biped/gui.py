from importlib import *
from ysrig import gui_base
reload(gui_base)

class Gui(gui_base.GuiBase):
    def add_parent_list(self):
        pass

    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Skeleton")
        self.widget["SpineJointCount"] = gui_base.YSDoubleSpinBox(label="★ Spine Joint Count", range=[1, 9], decimals=0, step=1)
        self.widget["NeckJointCount"] = gui_base.YSDoubleSpinBox(label="★ Neck Joint Count", range=[2, 9], decimals=0, step=1)
        self.widget["ArmTwistJointCount"] = gui_base.YSDoubleSpinBox(label="Arm Twist Joint Count", range=[0, 9], decimals=0, step=1)
        self.widget["LegTwistJointCount"] = gui_base.YSDoubleSpinBox(label="Leg Twist Joint Count", range=[0, 9], decimals=0, step=1)
        self.widget["UseFinger"] = gui_base.YSCheckBox(label="★ Use Finger")
        self.widget["FingerNames"] = gui_base.YSCheckList(label="★ Finger Names")
        self.widget["UseToeSub"] = gui_base.YSCheckBox(label="★ Use ToeSub")
        self.widget["UseJaw"] = gui_base.YSCheckBox(label="★ Use Jaw")
        self.widget["UseEyes"] = gui_base.YSCheckBox(label="★ Use Eyes")
        self.widget["UseEyelid"] = gui_base.YSCheckBox(label="★ Use Eyelid")
        self.widget["UseEyes"].connect(self.eyelid_enable)

        self.widget["Frame2"] = gui_base.YSFrame(label="Rig")
        self.widget["ConnectType"] = gui_base.YSRadioButton(label="Connect Type", radio_label=["World", "Local"])

    def call(self):
        guide = self.klass(
            self.widget["SpineJointCount"].get(),
            self.widget["NeckJointCount"].get(),
            self.widget["ArmTwistJointCount"].get(),
            self.widget["LegTwistJointCount"].get(),
            self.widget["UseFinger"].get(),
            [f'L_{d[0]}' for d in self.widget["FingerNames"].get()],
            [d[1] for d in self.widget["FingerNames"].get()],
            self.widget["UseToeSub"].get(),
            self.widget["UseJaw"].get(),
            self.widget["UseEyes"].get(),
            self.widget["UseEyelid"].get(),
            self.widget["ConnectType"].get()
        )

    def eyelid_enable(self):
        self.widget["UseEyelid"].enable(self.widget["UseEyes"].get())

def main():
    G = Gui()
    G.show()