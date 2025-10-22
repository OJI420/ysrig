from importlib import *
from ysrig import gui_base, core
reload(gui_base)

class Gui(gui_base.facialGuiBase):
    def gui(self):
        self.widget["Frame1"] = gui_base.YSFrame(label="Name")
        self.widget["GroupName"] = gui_base.YSLineEdit(label="★ Group Name", placeholder_text="Eyes")
        self.widget["EyeName"] = gui_base.YSLineEdit(label="★ Eye Name")

    def call(self):
        guide = self.klass(
            self.widget["GroupName"].get(),
            2,
            core.get_facials_root(),
            "",
            [
                f'L_{self.widget["EyeName"].get()}',
                f'L_{self.widget["EyeName"].get()}_GB'
            ]
        )

        guide.apply_settings()



def main():
    G = Gui()
    G.show()