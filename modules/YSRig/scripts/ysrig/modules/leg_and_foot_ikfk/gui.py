from importlib import *
from ysrig import gui_base
reload(gui_base)

PV_CTRL_SHAPE_TYPE = ["Locator", "Octahedron", "Cube", "Sphere"]

class Gui(gui_base.GuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["Side"] = gui_base.YSSidePrefix()
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Leg")
        self.widget["UpperLegName"] = gui_base.YSLineEdit(label="★ UpperLeg Name")
        self.widget["ForeLegName"] = gui_base.YSLineEdit(label="★ ForeLeg Name")
        self.widget["FootName"] = gui_base.YSLineEdit(label="★ Foot Name")
        self.widget["ToeName"] = gui_base.YSLineEdit(label="★ Toe Name")

        self.widget["UseToeSub"] = gui_base.YSCheckBox(label="★ Use ToeSub")
        self.widget["ToeSubName"] = gui_base.YSLineEdit(label="★ ToeSub Name")
        self.widget["UseToeSub"].connect(self.tiptoe_enable)

        self.widget["Frame2"] = gui_base.YSFrame(label="Skeleton")
        self.widget["GoalBone"] = gui_base.YSCheckBox(label="Goal Bone")
        self.widget["Mirror"] = gui_base.YSCheckBox(label="Mirror")
        self.widget["TwistJointCount"] = gui_base.YSDoubleSpinBox(label="Twist Joint Count", range=[0, 99], decimals=0, step=1)

        self.widget["Frame3"] = gui_base.YSFrame(label="Controller")
        self.widget["PVCtrlShapeType"] = gui_base.YSComboBox(label="PV Ctrl Shape Type", items=PV_CTRL_SHAPE_TYPE)

        self.widget["Frame4"] = gui_base.YSFrame(label="Rig")
        self.widget["ConnectType"] = gui_base.YSRadioButton(label="Connect Type", radio_label=["World", "Local"])

    def call(self):
        guide = self.klass(
            f'{self.widget["Side"].get_prefix()}{self.widget["GroupName"].get()}', # prefixとgroup_nameを結合して渡す
            -1,
            self.pre_widget["Parent"].get(),
            self.widget["Side"].get_prefix(),
            [
                f'{self.widget["Side"].get_prefix()}{self.widget["UpperLegName"].get()}',
                f'{self.widget["Side"].get_prefix()}{self.widget["ForeLegName"].get()}',
                f'{self.widget["Side"].get_prefix()}{self.widget["FootName"].get()}',
                f'{self.widget["Side"].get_prefix()}{self.widget["ToeName"].get()}',
                f'{self.widget["Side"].get_prefix()}{self.widget["UseToeSub"].get()}'
            ],
            self.widget["UseToeSub"].get(),
            self.widget["PVCtrlShapeType"].get_items()
        )

        guide.apply_settings(
            goal_bone = self.widget["GoalBone"].get(),
            mirror = self.widget["Mirror"].get(),
            connect_type = self.widget["ConnectType"].get(),
            pv_ctrl_shape_type = self.widget["PVCtrlShapeType"].get(),
            twist_joint_count = self.widget["TwistJointCount"].get()
        )

    def tiptoe_enable(self):
        self.widget["ToeSubName"].enable(self.widget["UseToeSub"].get())


def main():
    G = Gui()
    G.show()