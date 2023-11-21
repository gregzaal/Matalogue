# Matalogue

A Blender add-on that displays a list of materials and other node trees right in the toolbar of the Node Editor.

This makes it easier to **switch between different materials** while shading, and different compositing setups while working with multiple scenes.

### [Download Latest Version](https://raw.githubusercontent.com/gregzaal/Matalogue/master/matalogue.py) for Blender 4.0 (right click > Save As)

https://github.com/gregzaal/Matalogue/assets/5604661/e025af6d-6379-470e-b32b-f3ad175b8858

Older versions:
* [Blender 2.8 - 3.6](https://raw.githubusercontent.com/gregzaal/Matalogue/4045065/matalogue.py)
* [Blender 2.7](https://raw.githubusercontent.com/gregzaal/Matalogue/e9aaa80e/matalogue.py)

Still to do:

* Center and zoom view to the nodes (requires new API access). As a hack, maybe recenter nodes instead of view?
* Split into multi-file add-on
* Add preferences:
  - Hide panels for other node tree types (e.g. only show shader trees when in shader editor, not geo nodes & comp)

----

## Documentation

### Trees

There are multiple sources of node trees in Blender, namely:

* Shader nodes for both materials and lights
* Geometry nodes
* Node groups of various types
* Compositing
* Freestyle nodes (*not yet supported*)

By clicking on one of the listed items, the Node Editor will switch to that tree and select the related objects.

##### Materials

Lists all the materials according to the options below. Click on a name to switch to the nodes for that material.

* **Selected Objects Only** - Only show materials that are assigned to selected objects, otherwise all materials in the current scene are shown.
* **Visible Layers Only** - Only show materials that are assigned to objects that are on one of the visible layers. Take note that if *All Scenes* is off, materials on visible layers of other scenes will be shown too.
* **All Scenes** - Show materials from all scenes, not just the current one. Requires *Selected Objects Only* to be disabled.
* **0-User Materials** - Show materials that have no users (those that will be deleted when Blender is closed). Requires *All Scenes* to be enabled.

##### Geometry Nodes

Lists all geometry nodes modifiers and tools in the scene.

##### Lighting

Lists all the **lamp data** in the current scene, as well as the **World** nodes. Click on a name to switch to the nodes for that lamp.

##### Compositing

Lists each scene - clicking on one will take you to the compositing nodes for that scene.

### Special Cases

When switching to a material that is not actually used by any objects, a dummy object (which has no vertices) is created. This is because the only way to control what material is displayed in the Node Editor via Python is by selecting the object that material is assigned to.

The dummy object is automatically deleted once it is no longer needed (though only when you switch to another material).
