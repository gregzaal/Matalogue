# Matalogue

A Blender add-on that displays a list of materials and other node trees right in the toolbar of the Node Editor.

This makes it easier to **switch between different materials** while shading, and different compositing setups while working with multiple scenes.

### [Download Latest Version](http://bit.ly/matalogue_download) for Blender 4.0

![demo](https://raw.githubusercontent.com/gregzaal/Matalogue/master/demo.gif)

Older versions:
* [Blender 2.8 - 3.6](https://raw.githubusercontent.com/gregzaal/Matalogue/4045065/matalogue.py)
* [Blender 2.7](https://raw.githubusercontent.com/gregzaal/Matalogue/e9aaa80e/matalogue.py)

Still to do:

* Center and zoom view to the nodes (requires new API access)

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

##### Groups

Lists all the node groups, including both shader node groups and compositing node groups (separated by a short gap).

Clicking on one of the groups will open it up and allow you to edit the nodes inside without actually adding the group node anywhere.

If you're currently editing shader nodes and you click on a compositing node group, you will be switched to the compositing node tree first and will need to click on the group again in order to open it. This is a known limitation, and I can't figure out a way around it.

##### Lighting

Lists all the **lamp data** in the current scene, as well as the **World** nodes. Click on a name to switch to the nodes for that lamp.

##### Compositing

Lists each scene - clicking on one will take you to the compositing nodes for that scene.

### Special Cases

When switching to a material that is not actually used by any objects, a dummy object (which has no vertices) is created. This is because the only way to control what material is displayed in the Node Editor via Python is by selecting the object that material is assigned to.

The dummy object is automatically deleted once it is no longer needed (though only when you switch to another material).