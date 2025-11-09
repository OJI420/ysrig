from importlib import *
from ysrig import gui_base, core
reload(gui_base)

class Gui(gui_base.facialGuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Jaw")

        self.widget["Frame2"] = gui_base.YSFrame(label="Skeleton")
        self.widget["GoalBone"] = gui_base.YSCheckBox(label="Goal Bone")

    def call(self):
        guide = self.klass(
            self.widget["GroupName"].get(),
            2,
            core.get_facials_root(),
            ""
        )

        guide.apply_settings(
            goal_bone = self.widget["GoalBone"].get()
        )



def main():
    G = Gui()
    G.show()