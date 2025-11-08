import os
from importlib import *
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
from maya import cmds
from ysrig import addmenu

MENU = "ysrig_Menu"
VENDOR = "Yukito Suzuki"
VERSION = "2.1.1"

def initializePlugin(plugin):
    reload(addmenu)
    pluginFn = ompx.MFnPlugin(plugin, VENDOR, VERSION)
    addmenu.main(VERSION)

def uninitializePlugin(plugin):
    reload(addmenu)
    if cmds.menu(MENU, exists=True):
        cmds.deleteUI(MENU, menu=True)
