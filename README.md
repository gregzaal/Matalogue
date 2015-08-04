# Matalogue

A Blender add-on that displays a list of materials and other node trees right in the toolbar of the Node Editor.

This makes it easier to **switch between different materials** while shading, and different compositing setups while working with multiple scenes.

### [Download Latest Version](https://raw.githubusercontent.com/gregzaal/Matalogue/master/matalogue.py)

![demo](https://raw.githubusercontent.com/gregzaal/Matalogue/master/demo.gif)

Still to do:

* Show list of node groups
* Functions to assign materials to objects
* Create new materials right from the node editor and optionally...
* Center and zoom view to the nodes (requires new API access)

----

## Documentation

### Trees

There are multiple sources of node trees in Blender, namely:

* Material nodes
* Lamp nodes
* Compositing
* Texture nodes (*not yet supported*)
* Node groups (*not yet supported*)
* Freestyle nodes (*not yet supported*)

By clicking on one of the listed items, the Node Editor will switch to that tree and select the related objects.

##### Materials

Lists all the materials according to the options below. Click on a name to switch to the nodes for that material.

* **Selected Objects Only** - Only show materials that are assigned to selected objects, otherwise all materials in the current scene are shown.
* **All Scenes** - Show materials from all scenes, not just the current one. Requires *Selected Objects Only* to be disabled.
* **0-User Materials** - Show materials that have no users (those that will be deleted when Blender is closed). Requires *All Scenes* to be enabled.

##### Lighting

Lists all the **lamp data** in the current scene, as well as the **World** nodes. Click on a name to switch to the nodes for that lamp.

##### Compositing

Lists each scene - clicking on one will take you to the compositing nodes for that scene.

### Special Cases

When switching to a material that is not actually used by any objects, a dummy object (which has no vertices) is created. This is because the only way to control what material is displayed in the Node Editor via Python is by selecting the object that material is assigned to.

The dummy object is automatically deleted once it is no longer needed (when you switch to another material).