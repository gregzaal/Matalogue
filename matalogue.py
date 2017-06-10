# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Matalogue",
    "description": " Catalogue of node trees in the toolbar to switch between quickly",
    "author": "Greg Zaal",
    "version": (1, 2),
    "blender": (2, 76, 0),
    "location": "Node Editor > Toolbar (T) > Trees",
    "warning": "",
    "wiki_url": "https://github.com/gregzaal/Matalogue",
    "tracker_url": "https://github.com/gregzaal/Matalogue/issues",
    "category": "Node"}

import bpy


'''
TODOs:
    Assign material to selected objects
    Recenter view (don't change zoom) (add preference to disable) - talk to devs about making space_data.edit_tree.view_center editable
    Create new material and optionally...
        assign to selected objects
        duplicate from active
'''


class MatalogueSettings(bpy.types.PropertyGroup):
    expand_mat_options = bpy.props.BoolProperty(
        name="Options",
        default=False,
        description="Show settings for controlling which materials are listed")

    selected_only = bpy.props.BoolProperty(
        name="Selected Objects Only",
        default=False,
        description="Only show materials used by objects that are selected")

    vis_layers_only = bpy.props.BoolProperty(
        name="Visible Layers Only",
        default=False,
        description="Only show materials used by objects that are on a visible layer. (\"Selected Objects Only\" must be disabled)")

    all_scenes = bpy.props.BoolProperty(
        name="All Scenes",
        default=False,
        description="Show materials from all the scenes (not just the current one). (\"Selected Objects Only\" must be disabled)")

    show_zero_users = bpy.props.BoolProperty(
        name="0-User Materials",
        default=False,
        description="Also show materials that have no users. (\"All Scenes\" must be enabled)")


#####################################################################
# Functions
#####################################################################

def material_in_cur_scene(mat):
    scene = bpy.context.scene
    for obj in scene.objects:
        if obj.name != "Matalogue Dummy Object":
            for slot in obj.material_slots:
                if slot.material == mat:
                    return True
    return False

def material_on_sel_obj(mat):
    selection = bpy.context.selected_objects
    for obj in selection:
        if obj.name != "Matalogue Dummy Object":
            for slot in obj.material_slots:
                if slot.material == mat:
                    return True
    return False

def material_on_vis_layer(mat):
    for scene in bpy.data.scenes:
        objs_on_vis_layer = []
        for obj in scene.objects:
            if obj.name != "Matalogue Dummy Object":
                for i, sl in enumerate(scene.layers):
                    if sl and obj.layers[i]:
                        objs_on_vis_layer.append(obj)
                        break
        for obj in objs_on_vis_layer:
            for slot in obj.material_slots:
                if slot.material == mat:
                    return True
    return False

checked_groups_names_list = []
materials_from_group = set()

def find_materials_in_groupinstances(empty):
    if empty.dupli_group.name in checked_groups_names_list:
        # print('already checked group: ' + empty.dupli_group.name)
        return None
    for obj in bpy.data.groups[empty.dupli_group.name].objects:
        if obj.dupli_group and obj.type == 'EMPTY':
            return find_materials_in_groupinstances(obj)
        elif obj.type == "MESH":
            for slot in obj.material_slots:
                if slot.material:
                    materials_from_group.add(slot.material)
                    # print('added material to list: ' + slot.material.name)
    checked_groups_names_list.append(empty.dupli_group.name)  # or no empty mat in group
    return None

def get_materials():
    settings = bpy.context.window_manager.matalogue_settings
    materials = []
    for mat in bpy.data.materials:
        conditions = [
            (settings.show_zero_users or mat.users),
            (settings.all_scenes or material_in_cur_scene(mat)),
            (not settings.selected_only or material_on_sel_obj(mat)),
            (not settings.vis_layers_only or material_on_vis_layer(mat)),
            not mat.library,  # don't allow editing of linked library materials - TODO make this optional (can help to be able to look at the nodes, even if you can't edit it)
            mat.use_nodes]
        if all(conditions):
            materials.append(mat)
    additional_mats = set()
    checked_groups_names_list.clear()
    if settings.selected_only:
        for obj in bpy.context.selected_objects:
            if obj.dupli_group and obj.type == 'EMPTY':
                find_materials_in_groupinstances(obj)
                additional_mats = additional_mats | materials_from_group
                materials_from_group.clear()
    return list(set(materials) | additional_mats)

def dummy_object(delete=False):
    ''' Return the existing dummy object, or create one if it doesn't exist. '''
    scene = bpy.context.scene

    if delete:
        for obj in scene.objects:
            if "Matalogue Dummy Object" in obj.name:
                scene.objects.unlink(obj)
        return "DONE"

    dummy = None
    previous_dummy = [obj for obj in bpy.data.objects if obj.name == "Matalogue Dummy Object"]
    if previous_dummy:
        dummy = previous_dummy[0]
    else:
        m = bpy.data.meshes.new("Matalogue Dummy Mesh")
        dummy = bpy.data.objects.new("Matalogue Dummy Object", m)

    if dummy not in list(obj for obj in scene.objects):
        scene.objects.link(dummy)

    dummy.select = True
    scene.objects.active = dummy

    if len(dummy.material_slots) == 0:
        bpy.ops.object.material_slot_add()

    return dummy


#####################################################################
# Operators
#####################################################################

class TLGoToMat(bpy.types.Operator):

    'Show the nodes for this material'
    bl_idname = 'matalogue.goto_mat'
    bl_label = 'Go To Material'
    mat = bpy.props.StringProperty(default = "")

    def execute(self, context):
        dummy_object(delete=True)
        scene = context.scene
        context.space_data.tree_type = 'ShaderNodeTree'
        context.space_data.shader_type = 'OBJECT'
        mat = bpy.data.materials[self.mat]

        objs_with_mat = 0
        active_set = False
        for obj in scene.objects:
            obj_materials = [slot.material for slot in obj.material_slots]
            if mat in obj_materials:
                objs_with_mat += 1
                obj.select = True
                if not active_set:  # set first object as active
                    active_set = True
                    scene.objects.active = obj
                    if mat != obj.active_material:
                        for i, x in enumerate(obj.material_slots):
                            if x.material == mat:
                                obj.active_material_index = i
                                break
            else:
                obj.select = False

        if objs_with_mat == 0:
            self.report({'WARNING'}, "No objects in this scene use '" + mat.name + "' material")
            dummy = dummy_object()
            slot = dummy.material_slots[0]
            slot.material = mat

        return {'FINISHED'}


class TLGoToGroup(bpy.types.Operator):

    'Show the nodes inside this group'
    bl_idname = 'matalogue.goto_group'
    bl_label = 'Go To Group'
    tree_type = bpy.props.StringProperty(default = "")
    tree = bpy.props.StringProperty(default = "")

    def execute(self, context):
        try:  # Go up one group as many times as possible - error will occur when the top level is reached
            while True:
                bpy.ops.node.tree_path_parent()
        except:
            pass

        context.space_data.tree_type = self.tree_type
        context.space_data.path.append(bpy.data.node_groups[self.tree])

        return {'FINISHED'}


class TLGoToLight(bpy.types.Operator):

    'Show the nodes for this material'
    bl_idname = 'matalogue.goto_light'
    bl_label = 'Go To Material'
    light = bpy.props.StringProperty(default = "")
    world = bpy.props.BoolProperty(default = False)

    def execute(self, context):
        dummy_object(delete=True)
        scene = context.scene
        context.space_data.tree_type = 'ShaderNodeTree'
        if self.world:
            context.space_data.shader_type = 'WORLD'
        else:
            context.space_data.shader_type = 'OBJECT'
            light = bpy.data.objects[self.light]
            scene.objects.active = light

        return {'FINISHED'}


class TLGoToComp(bpy.types.Operator):

    'Show the nodes for this material'
    bl_idname = 'matalogue.goto_comp'
    bl_label = 'Go To Composite'
    scene = bpy.props.StringProperty(default = "")

    def execute(self, context):
        context.space_data.tree_type = 'CompositorNodeTree'
        scene = bpy.data.scenes[self.scene]
        context.screen.scene = scene

        return {'FINISHED'}


#####################################################################
# UI
#####################################################################

class MatalogueMaterials(bpy.types.Panel):

    bl_label = "Materials"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Trees"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def draw(self, context):
        settings = context.window_manager.matalogue_settings
        layout = self.layout
        materials = get_materials()

        col = layout.column(align=True)

        for mat in materials:
            name = mat.name
            try:
                icon_val = layout.icon(mat)
            except:
                icon_val = 1
                print ("WARNING [Mat Panel]: Could not get icon value for %s" % name)
            if mat.users:
                op = col.operator('matalogue.goto_mat', text=name, emboss=(mat==context.space_data.id), icon_value=icon_val)
                op.mat = name
            else:
                row = col.row(align=True)
                op = row.operator('matalogue.goto_mat', text=name, emboss=(mat==context.space_data.id), icon_value=icon_val)
                op.mat = name
                op = row.operator('matalogue.goto_mat', text="", emboss=(mat==context.space_data.id), icon='ERROR')
                op.mat = name

        if not materials:
            col.label("Nothing to show!")

        col = layout.column(align=True)

        box = col.box()
        scol = box.column(align=True)
        scol.prop(settings, 'expand_mat_options', toggle=True, icon='TRIA_DOWN' if settings.expand_mat_options else 'TRIA_RIGHT')
        if settings.expand_mat_options:
            scol.prop(settings, "selected_only")
            r = scol.row()
            r.enabled = not settings.selected_only
            r.prop(settings, "vis_layers_only")
            r = scol.row()
            r.enabled = not settings.selected_only
            r.prop(settings, "all_scenes")
            r = scol.row()
            r.enabled = (settings.all_scenes and not settings.selected_only)
            r.prop(settings, "show_zero_users")


class MatalogueGroups(bpy.types.Panel):

    bl_label = "Groups"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Trees"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)

        shader_groups = []
        comp_groups = []
        for g in bpy.data.node_groups:
            if g.type == 'SHADER':
                shader_groups.append(g)
            elif g.type == 'COMPOSITING':
                comp_groups.append(g)

        # col.label("Shader Groups")
        for g in shader_groups:
            emboss = False
            if len(context.space_data.path) > 0:
                emboss = context.space_data.path[-1].node_tree.name==g.name
            op = col.operator('matalogue.goto_group', text=g.name, emboss=emboss, icon='NODETREE')
            op.tree_type = "ShaderNodeTree"
            op.tree = g.name

        col.separator()
        col.separator()
        col.separator()

        # col.label("Compositing Groups")
        for g in comp_groups:
            emboss = False
            if len(context.space_data.path) > 0:
                emboss = context.space_data.path[-1].node_tree.name==g.name
            op = col.operator('matalogue.goto_group', text=g.name, emboss=emboss, icon='NODETREE')
            op.tree_type = "CompositorNodeTree"
            op.tree = g.name


class MatalogueLighting(bpy.types.Panel):

    bl_label = "Lighting"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Trees"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'CYCLES'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        lights = [obj for obj in scene.objects if obj.type == 'LAMP']

        col = layout.column(align=True)

        for light in lights:
            if light.data.use_nodes:
                name = light.name
                op = col.operator('matalogue.goto_light', text=name, emboss=(light.data==context.space_data.id), icon='LAMP_%s' % light.data.type)
                op.light = name
                op.world = False

        if context.scene.world.use_nodes:
            op = col.operator('matalogue.goto_light', text="World", emboss=(context.scene.world==context.space_data.id), icon='WORLD')
            op.world = True


class MatalogueCompositing(bpy.types.Panel):

    bl_label = "Compositing"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "TOOLS"
    bl_category = "Trees"

    def draw(self, context):
        scenes = bpy.data.scenes
        layout = self.layout

        col = layout.column(align=True)

        for sc in scenes:
            name = sc.name
            op = col.operator('matalogue.goto_comp', text=name, emboss=(sc==context.space_data.id), icon='SCENE_DATA')
            op.scene = name


#####################################################################
# Registration
#####################################################################

def register():
    bpy.utils.register_module(__name__)

    bpy.types.WindowManager.matalogue_settings = bpy.props.PointerProperty(type=MatalogueSettings)

def unregister():
    del bpy.types.WindowManager.matalogue_settings

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
