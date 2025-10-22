from maya import cmds
import os
import json

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def save_shape():
    savefile = os.path.join(path, "prefs", "ysrig", "controller_sahpe.json")
    data = {}
    selection = cmds.ls(sl=True)

    for sel in selection:
        cv = cmds.listRelatives(sel, s=True)[0]
        cv_pos = []

        for i in range(cmds.getAttr(f"{cv}.controlPoints", size=True)):
            cv_pos.append(cmds.getAttr(f"{cv}.controlPoints[{i}]")[0])

        data[sel] = cv_pos
        data[f"{sel}_Uniform_Scale"] = cmds.getAttr("%s.displayRotatePivot"%(sel))
        
    with open(savefile, "w") as f:
        json.dump(data, f, indent=4)

"""
from ysrig import save_json
save_json.save_shape()
"""

def save_button_shape():
    savefile = os.path.join(path, "prefs", "ysrig", "button_shape.json")
    mod = {}

    sels = cmds.ls(sl=True)
    for sel in sels:
        mod[sel] = {}
        shapes = cmds.listRelatives(sel, c=True)
        for shape in shapes:
            mod[sel][shape] = {}
            mod[sel][shape]["pos"] = [cmds.getAttr(f"{shape}.translateX"), cmds.getAttr(f"{shape}.translateZ")]
            mod[sel][shape]["cvs"] = []

            cv = cmds.listRelatives(shape, s=True)[0]
            for i in range(cmds.getAttr(f"{cv}.controlPoints", size=True)):
                mod[sel][shape]["cvs"] += [cmds.getAttr(f"{cv}.controlPoints[{i}]")[0]]

    with open(savefile, "w") as f:
        json.dump(mod, f, indent=4)
"""
from ysrig import save_json
save_json.save_button_shape()
"""