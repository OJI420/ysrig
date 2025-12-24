from importlib import *
from ysrig import gui_base
reload(gui_base)

CTRL_SHAPE_TYPE = ["Locator", "Octahedron", "Cube", "Sphere"]

class Gui(gui_base.GuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["Side"] = gui_base.YSSidePrefix()
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Chain")

        self.widget["Frame2"] = gui_base.YSFrame(label="Skeleton")
        self.widget["JointCount"] = gui_base.YSDoubleSpinBox(label="★ Chain Joint Count", range=[4, 99], decimals=0, step=1)
        self.widget["Mirror"] = gui_base.YSCheckBox(label="Mirror")

        self.widget["Frame3"] = gui_base.YSFrame(label="Controller")
        self.widget["CtrlCount"] = gui_base.YSDoubleSpinBox(label="Ctrl Count", range=[3, 25], decimals=0, step=1)
        self.widget["CtrlShapeType"] = gui_base.YSComboBox(label="Ctrl Shape Type", items=CTRL_SHAPE_TYPE)

        self.widget["Frame4"] = gui_base.YSFrame(label="Rig")
        self.widget["ConnectType"] = gui_base.YSRadioButton(label="Connect Type", radio_label=["World", "Local"])

    def call(self):
        guide = self.klass(
            f'{self.widget["Side"].get_prefix()}{self.widget["GroupName"].get()}', # prefixとgroup_nameを結合して渡す
            self.widget["JointCount"].get(),
            self.pre_widget["Parent"].get(),
            self.widget["Side"].get_prefix(),
            self.widget["CtrlShapeType"].get_items()
        )

        guide.apply_settings(
            mirror = self.widget["Mirror"].get(),
            connect_type = self.widget["ConnectType"].get(),
            ctrl_shape_type = self.widget["CtrlShapeType"].get(),
            ctrl_count = self.widget["CtrlCount"].get()
        )


def main():
    G = Gui()
    G.show()