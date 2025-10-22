from importlib import *
from ysrig import gui_base
reload(gui_base)

class Gui(gui_base.GuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["Side"] = gui_base.YSSidePrefix()
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Neck")
        self.widget["HeadJointName"] = gui_base.YSLineEdit(label="★ Head Joint Name", placeholder_text="Head")

        self.widget["Frame2"] = gui_base.YSFrame(label="Skeleton")
        self.widget["JointCount"] = gui_base.YSDoubleSpinBox(label="★ Neck Joint Count", range=[2, 99], decimals=0, step=1)
        self.widget["GoalBone"] = gui_base.YSCheckBox(label="Goal Bone")
        self.widget["Mirror"] = gui_base.YSCheckBox(label="Mirror")

        self.widget["Frame4"] = gui_base.YSFrame(label="Rig")
        self.widget["Translate"] = gui_base.YSCheckBox(label="Translate Enabled")
        self.widget["ConnectType"] = gui_base.YSRadioButton(label="Connect Type", radio_label=["World", "Local"])

    def call(self):
        guide = self.klass(
            f'{self.widget["Side"].get_prefix()}{self.widget["GroupName"].get()}', # prefixとgroup_nameを結合して渡す
            self.widget["JointCount"].get(),
            self.pre_widget["Parent"].get(),
            self.widget["Side"].get_prefix(),
            [f'{self.widget["Side"].get_prefix()}{self.widget["HeadJointName"].get()}']
        )

        guide.apply_settings(
            goal_bone = self.widget["GoalBone"].get(),
            mirror = self.widget["Mirror"].get(),
            connect_type = self.widget["ConnectType"].get(),
            translate_enabled = self.widget["Translate"].get()
        )


def main():
    G = Gui()
    G.show()