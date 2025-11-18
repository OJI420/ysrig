from importlib import *
from ysrig import gui_base
reload(gui_base)

class Gui(gui_base.GuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Spine")
        self.widget["HipJointName"] = gui_base.YSLineEdit(label="★ Hip Joint Name", placeholder_text="Hip")

        self.widget["Frame2"] = gui_base.YSFrame(label="Skeleton")
        self.widget["JointCount"] = gui_base.YSDoubleSpinBox(label="★ Spine Joint Count", range=[1, 9], decimals=0, step=1)

        self.widget["Frame4"] = gui_base.YSFrame(label="Rig")
        self.widget["Translate"] = gui_base.YSCheckBox(label="Translate Enabled")
        self.widget["ConnectType"] = gui_base.YSRadioButton(label="Connect Type", radio_label=["World", "Local"])

    def call(self):
        guide = self.klass(
            self.widget["GroupName"].get(),
            self.widget["JointCount"].get(),
            self.pre_widget["Parent"].get(),
            "",
            [self.widget["HipJointName"].get()]
        )

        guide.apply_settings(
            connect_type = self.widget["ConnectType"].get(),
            translate_enabled = self.widget["Translate"].get()
        )


def main():
    G = Gui()
    G.show()