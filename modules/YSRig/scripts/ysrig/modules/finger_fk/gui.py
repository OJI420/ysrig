from importlib import *
from ysrig import gui_base
reload(gui_base)

CTRL_SHAPE_TYPE = ["Circle", "Square", "BoundingBox", "Cube", "Sphere"]

class Gui(gui_base.GuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["Side"] = gui_base.YSSidePrefix()
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Finger")
        self.widget["FingerNames"] = gui_base.YSCheckList(label="★ Finger Names")

        self.widget["Frame2"] = gui_base.YSFrame(label="Skeleton")
        self.widget["GoalBone"] = gui_base.YSCheckBox(label="Goal Bone")
        self.widget["Mirror"] = gui_base.YSCheckBox(label="Mirror")

        self.widget["Frame3"] = gui_base.YSFrame(label="Controller")
        self.widget["CtrlShapeType"] = gui_base.YSComboBox(label="Ctrl Shape Type", items=CTRL_SHAPE_TYPE)

        self.widget["Frame4"] = gui_base.YSFrame(label="Rig")
        self.widget["Translate"] = gui_base.YSCheckBox(label="Translate Enabled")
        self.widget["ConnectType"] = gui_base.YSRadioButton(label="Connect Type", radio_label=["World", "Local"])

    def call(self):
        guide = self.klass(
            f'{self.widget["Side"].get_prefix()}{self.widget["GroupName"].get()}', # prefixとgroup_nameを結合して渡す
            -1,
            self.pre_widget["Parent"].get(),
            self.widget["Side"].get_prefix(),
            [f'{self.widget["Side"].get_prefix()}{d[0]}' for d in self.widget["FingerNames"].get()],
            [d[1] for d in self.widget["FingerNames"].get()],
            self.widget["CtrlShapeType"].get_items()
        )

        guide.apply_settings(
            goal_bone = self.widget["GoalBone"].get(),
            mirror = self.widget["Mirror"].get(),
            connect_type = self.widget["ConnectType"].get(),
            translate_enabled = self.widget["Translate"].get(),
            fk_ctrl_shape_type = self.widget["CtrlShapeType"].get()
        )


def main():
    G = Gui()
    G.show()