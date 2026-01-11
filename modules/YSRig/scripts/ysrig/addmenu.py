import importlib
import maya.cmds as cmds
import maya.mel as mel
from ysrig import reload, skeleton_base, ctrl_base, rig_base, build_manager, export_meta_node, import_meta_node, export_user_settings, import_user_settings, reset_user_settings, help, snap_guide_to_vertex, picker_editor, picker, remove_registry
from ysrig.modules import chain_basic, chain_spline_ik, ribbon, root, spine_basic, neck_and_head_basic, shoulder_and_arm_ikfk, leg_and_foot_ikfk, finger_fk, eye_basic, eye_and_simple_eyelid, jaw_basic, biped
reload.main(chain_basic)
reload.main(chain_spline_ik)
reload.main(ribbon)
reload.main(root)
reload.main(spine_basic)
reload.main(neck_and_head_basic)
reload.main(shoulder_and_arm_ikfk)
reload.main(leg_and_foot_ikfk)
reload.main(finger_fk)
reload.main(eye_basic)
reload.main(eye_and_simple_eyelid)
reload.main(jaw_basic)
reload.main(build_manager)
reload.main(biped)
reload.main(help)
reload.main(snap_guide_to_vertex)
reload.main(picker_editor)
reload.main(picker)
importlib.reload(skeleton_base)
importlib.reload(ctrl_base)
importlib.reload(rig_base)
importlib.reload(export_meta_node)
importlib.reload(import_meta_node)
importlib.reload(export_user_settings)
importlib.reload(import_user_settings)
importlib.reload(reset_user_settings)
importlib.reload(remove_registry)

MAINWINDOW = mel.eval('$tmpVar=$gMainWindow')
MENU = "ysrig_Menu"

def main(ver):
    if cmds.menu(MENU, exists=True):
        cmds.deleteUI(MENU)

    cmds.menu(MENU, parent=MAINWINDOW, tearOff=True, label=f"- YSRig v{ver} -")

    cmds.menuItem(label="Build Guide", subMenu=True, tearOff=True)
    cmds.menuItem(label="Template", subMenu=True, tearOff=True)
    cmds.menuItem(label="Biped", command=lambda *args: biped.gui.main())

    cmds.setParent("..", m=True)

    cmds.menuItem(divider=True, label="Root")
    cmds.menuItem(label="Root", command=lambda *args: root.guide.main())

    cmds.menuItem(divider=True, label="Chain")
    cmds.menuItem(label="Chain Basic", command=lambda *args: chain_basic.gui.main())
    cmds.menuItem(label="Chain Spline IK", command=lambda *args: chain_spline_ik.gui.main())

    cmds.menuItem(divider=True, label="Spine")
    cmds.menuItem(label="Spine Basic", command=lambda *args: spine_basic.gui.main())

    cmds.menuItem(divider=True, label="Neck")
    cmds.menuItem(label="Neck and Head Basic", command=lambda *args: neck_and_head_basic.gui.main())

    cmds.menuItem(divider=True, label="Arm")
    cmds.menuItem(label="Shoulder and Arm IKFK", command=lambda *args: shoulder_and_arm_ikfk.gui.main())

    cmds.menuItem(divider=True, label="Leg")
    cmds.menuItem(label="Leg and Foot IKFK", command=lambda *args: leg_and_foot_ikfk.gui.main())

    cmds.menuItem(divider=True, label="Finger")
    cmds.menuItem(label="Finger FK", command=lambda *args: finger_fk.gui.main())

    cmds.menuItem(divider=True, label="Eye")
    cmds.menuItem(label="Eye Basic", command=lambda *args: eye_basic.gui.main())
    cmds.menuItem(label="Eye and Simple Eyelid", command=lambda *args: eye_and_simple_eyelid.gui.main())

    cmds.menuItem(divider=True, label="Jaw")
    cmds.menuItem(label="Jaw Basic", command=lambda *args: jaw_basic.gui.main())

    """
    cmds.menuItem(divider=True, label="Other")
    cmds.menuItem(label="Ribbon", command=lambda *args: ribbon.gui.main())
    """

    cmds.setParent("..", m=True)

    cmds.menuItem(label="Guide Tools", subMenu=True, tearOff=True)
    cmds.menuItem(label="Snap Guide To Vertex", command=lambda *args: snap_guide_to_vertex.gui.main())

    cmds.setParent("..", m=True)

    cmds.menuItem(label="Build Manager", command=lambda *args: build_manager.gui.main())

    cmds.menuItem(label="Picker", subMenu=True, tearOff=True)
    cmds.menuItem(label="Picker Editor", command=lambda *args: picker_editor.gui.main())
    cmds.menuItem(label="Show Picker", command=lambda *args: picker.gui.main())

    cmds.setParent("..", m=True)

    cmds.menuItem(label="Import / Export", subMenu=True, tearOff=True)
    cmds.menuItem(label="Export Rig", command=lambda *args: export_meta_node.main())
    cmds.menuItem(label="Import Rig", command=lambda *args: import_meta_node.main())

    cmds.setParent("..", m=True)

    cmds.menuItem(divider=True)

    cmds.menuItem(label="Settings", subMenu=True, tearOff=True)
    cmds.menuItem(label="Export User Settings", command=lambda *args: export_user_settings.main())
    cmds.menuItem(label="Import User Settings", command=lambda *args: import_user_settings.main())
    cmds.menuItem(label="Reset User Settings", command=lambda *args: reset_user_settings.main())
    cmds.menuItem(label="Reset Window Layout", command=lambda *args: remove_registry.main())

    cmds.setParent("..", m=True)

    cmds.menuItem(divider=True)
    cmds.menuItem(label="Help", command=lambda *args: help.help.main())

    #cmds.menuItem(label="Picker Editor", command=lambda *args: picker_editor.gui.main())