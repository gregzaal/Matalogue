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
    "description": " Catalogue of node trees in the sidebar to switch between quickly",
    "author": "Greg Zaal",
    "version": (1, 4),
    "blender": (4, 0, 0),
    "location": "Node Editor > Sidebar (N) > Trees",
    "warning": "",
    "wiki_url": "https://github.com/gregzaal/Matalogue",
    "tracker_url": "https://github.com/gregzaal/Matalogue/issues",
    "category": "Node",
}

import bpy


class MatalogueSettings(bpy.types.PropertyGroup):
    expand_mat_options: bpy.props.BoolProperty(
        name="Options", default=False, description="Show settings for controlling which materials are listed"
    )

    selected_only: bpy.props.BoolProperty(
        name="Selected Objects Only", default=False, description="Only show materials used by objects that are selected"
    )

    vis_collections_only: bpy.props.BoolProperty(
        name="Visible Collections Only",
        default=False,
        description=(
            "Only show materials used by objects that are in a visible Collection. "
            '("Selected Objects Only" must be disabled)'
        ),
    )

    all_scenes: bpy.props.BoolProperty(
        name="All Scenes",
        default=False,
        description=(
            "Show materials from all the scenes (not just the current one). "
            '("Selected Objects Only" must be disabled)'
        ),
    )

    show_zero_users: bpy.props.BoolProperty(
        name="0-User Materials",
        default=False,
        description='Also show materials that have no users. ("All Scenes" must be enabled)',
    )


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


def obj_in_visible_collection(obj, scene):
    for oc in obj.users_collection:
        for child in bpy.context.window.view_layer.layer_collection.children:
            if child.is_visible and child.collection == oc:
                return True
    for o in scene.collection.objects:  # Master collection can't be hidden
        if obj == o:
            return True
    return False


def material_on_vis_collection(mat):
    for scene in bpy.data.scenes:
        objs_on_vis_layer = []
        for obj in scene.objects:
            if obj.name != "Matalogue Dummy Object":
                if obj_in_visible_collection(obj, scene):
                    objs_on_vis_layer.append(obj)
        for obj in objs_on_vis_layer:
            for slot in obj.material_slots:
                if slot.material == mat:
                    return True
    return False


checked_groups_names_list = []
materials_from_group = set()


def find_materials_in_groupinstances(empty):
    if empty.instance_collection.name in checked_groups_names_list:
        return None
    for obj in bpy.data.collections[empty.instance_collection.name].objects:
        if obj.instance_type == "COLLECTION" and obj.instance_collection is not None and obj.type == "EMPTY":
            return find_materials_in_groupinstances(obj)
        elif obj.type == "MESH":
            for slot in obj.material_slots:
                if slot.material:
                    materials_from_group.add(slot.material)
    checked_groups_names_list.append(empty.instance_collection.name)  # or no empty mat in group
    return None


def get_materials():
    settings = bpy.context.window_manager.matalogue_settings
    materials = []
    for mat in bpy.data.materials:
        conditions = [
            (settings.show_zero_users or mat.users),
            (settings.all_scenes or material_in_cur_scene(mat)),
            (not settings.selected_only or material_on_sel_obj(mat)),
            (not settings.vis_collections_only or material_on_vis_collection(mat)),
            not mat.library,  # Don't show linked materials since they can't be edited anyway
            mat.use_nodes,
        ]
        if all(conditions):
            materials.append(mat)
    additional_mats = set()
    checked_groups_names_list.clear()
    if settings.selected_only:
        for obj in bpy.context.selected_objects:
            if obj.instance_type == "COLLECTION" and obj.instance_collection is not None and obj.type == "EMPTY":
                find_materials_in_groupinstances(obj)
                additional_mats = additional_mats | materials_from_group
                materials_from_group.clear()
    all_mats = list(set(materials) | additional_mats)
    all_mats = sorted(all_mats, key=lambda x: x.name.lower())
    return all_mats


def dummy_object(delete=False):
    """Return the existing dummy object, or create one if it doesn't exist."""
    scene = bpy.context.scene

    if delete:
        for obj in scene.objects:
            if "Matalogue Dummy Object" in obj.name:
                scene.collection.objects.unlink(obj)
        return "DONE"

    dummy = None
    previous_dummy = [obj for obj in bpy.data.objects if obj.name == "Matalogue Dummy Object"]
    if previous_dummy:
        dummy = previous_dummy[0]
    else:
        m = bpy.data.meshes.new("Matalogue Dummy Mesh")
        dummy = bpy.data.objects.new("Matalogue Dummy Object", m)

    if dummy not in list(obj for obj in scene.objects):
        scene.collection.objects.link(dummy)

    dummy.select_set(True)
    bpy.context.view_layer.objects.active = dummy

    if len(dummy.material_slots) == 0:
        bpy.ops.object.material_slot_add()

    return dummy


#####################################################################
# Operators
#####################################################################


class MATALOGUE_OT_go_to_material(bpy.types.Operator):
    "Show the nodes for this material"
    bl_idname = "matalogue.goto_mat"
    bl_label = "Go To Material"

    mat: bpy.props.StringProperty(default="")

    def execute(self, context):
        dummy_object(delete=True)
        context.space_data.tree_type = "ShaderNodeTree"
        context.space_data.shader_type = "OBJECT"
        mat = bpy.data.materials[self.mat]

        objs_with_mat = 0
        active_set = False
        for obj in context.view_layer.objects:
            obj_materials = [slot.material for slot in obj.material_slots]
            if mat in obj_materials:
                objs_with_mat += 1
                obj.select_set(True)
                if not active_set:  # set first object as active
                    active_set = True
                    context.view_layer.objects.active = obj
                    if mat != obj.active_material:
                        for i, x in enumerate(obj.material_slots):
                            if x.material == mat:
                                obj.active_material_index = i
                                break
            else:
                obj.select_set(False)

        if objs_with_mat == 0:
            self.report({"WARNING"}, "No objects in this scene use '" + mat.name + "' material")
            dummy = dummy_object()
            slot = dummy.material_slots[0]
            slot.material = mat

        return {"FINISHED"}


class MATALOGUE_OT_go_to_group(bpy.types.Operator):
    "Show the nodes inside this group"
    bl_idname = "matalogue.goto_group"
    bl_label = "Go To Group"
    first_run = True

    tree_type: bpy.props.StringProperty(default="")
    tree: bpy.props.StringProperty(default="")

    def execute(self, context):
        try:  # Go up one group as many times as possible - error will occur when the top level is reached
            while True:
                bpy.ops.node.tree_path_parent()
        except RuntimeError:
            pass

        g = bpy.data.node_groups[self.tree]
        context.space_data.tree_type = self.tree_type
        context.space_data.path.append(g)

        current_tree = context.space_data.path[-1].node_tree if len(context.space_data.path) > 0 else None
        if self.first_run and current_tree is not g:
            # Sometimes we need to run this twice? Not sure why...
            self.first_run = False
            self.execute(context)
        return {"FINISHED"}


class MATALOGUE_OT_go_to_geonodes(bpy.types.Operator):
    "Show this Geometry Nodes tree"
    bl_idname = "matalogue.goto_geo"
    bl_label = "Go To Geo Nodes"
    first_run = True

    tree: bpy.props.StringProperty(default="")
    is_tool: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        try:  # Go up one group as many times as possible - error will occur when the top level is reached
            while True:
                bpy.ops.node.tree_path_parent()
        except RuntimeError:
            pass

        g = bpy.data.node_groups[self.tree]
        context.space_data.tree_type = "GeometryNodeTree"
        if self.is_tool:
            context.space_data.geometry_nodes_type = "TOOL"
            context.space_data.path.append(g)
        else:
            context.space_data.geometry_nodes_type = "MODIFIER"
            objs_with_modifier = 0
            active_set = False
            for obj in context.view_layer.objects:
                obj_groups = [mod.node_group for mod in obj.modifiers if mod.type == "NODES"]
                if g in obj_groups:
                    objs_with_modifier += 1
                    obj.select_set(True)
                    if not active_set:  # set first object as active
                        active_set = True
                        context.view_layer.objects.active = obj
                        for mod in obj.modifiers:
                            if g == mod.node_group and not mod.is_active:
                                mod.is_active = True
                                break
                else:
                    obj.select_set(False)
            if objs_with_modifier == 0:
                context.space_data.path.append(g)

        current_tree = context.space_data.path[-1].node_tree if len(context.space_data.path) > 0 else None
        if self.first_run and current_tree is not g:
            # Sometimes we need to run this twice? Not sure why...
            self.first_run = False
            self.execute(context)

        return {"FINISHED"}


class MATALOGUE_OT_go_to_light(bpy.types.Operator):
    "Show the nodes for this material"
    bl_idname = "matalogue.goto_light"
    bl_label = "Go To Material"

    light: bpy.props.StringProperty(default="")
    world: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        dummy_object(delete=True)
        context.space_data.tree_type = "ShaderNodeTree"
        if self.world:
            context.space_data.shader_type = "WORLD"
        else:
            context.space_data.shader_type = "OBJECT"
            light = bpy.data.objects[self.light]
            context.view_layer.objects.active = light

        return {"FINISHED"}


class MATALOGUE_OT_go_to_comp(bpy.types.Operator):
    "Show the nodes for this material"
    bl_idname = "matalogue.goto_comp"
    bl_label = "Go To Composite"
    scene: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.space_data.tree_type = "CompositorNodeTree"
        scene = bpy.data.scenes[self.scene]
        context.window.scene = scene

        return {"FINISHED"}


#####################################################################
# UI
#####################################################################


class MATALOGUE_PT_materials(bpy.types.Panel):
    bl_label = "Materials"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

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
                print("WARNING [Mat Panel]: Could not get icon value for %s" % name)
            if mat.users:
                op = col.operator(
                    "matalogue.goto_mat", text=name, emboss=(mat == context.space_data.id), icon_value=icon_val
                )
                op.mat = name
            else:
                row = col.row(align=True)
                op = row.operator(
                    "matalogue.goto_mat", text=name, emboss=(mat == context.space_data.id), icon_value=icon_val
                )
                op.mat = name
                op = row.operator(
                    "matalogue.goto_mat", text="", emboss=(mat == context.space_data.id), icon="ORPHAN_DATA"
                )
                op.mat = name

        if not materials:
            col.label(text="Nothing to show!")

        col = layout.column(align=True)

        box = col.box()
        scol = box.column(align=True)
        scol.prop(
            settings,
            "expand_mat_options",
            toggle=True,
            icon="TRIA_DOWN" if settings.expand_mat_options else "TRIA_RIGHT",
        )
        if settings.expand_mat_options:
            scol.prop(settings, "selected_only")
            r = scol.row()
            r.enabled = not settings.selected_only
            r.prop(settings, "vis_collections_only")
            r = scol.row()
            r.enabled = not settings.selected_only
            r.prop(settings, "all_scenes")
            r = scol.row()
            r.enabled = settings.all_scenes and not settings.selected_only
            r.prop(settings, "show_zero_users")


class MATALOGUE_PT_groups(bpy.types.Panel):
    bl_label = "Groups"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)

        shader_groups = []
        comp_groups = []
        for g in bpy.data.node_groups:
            if g.type == "SHADER":
                shader_groups.append(g)
            elif g.type == "COMPOSITING":
                comp_groups.append(g)

        # col.label(text="Shader Groups")
        for g in shader_groups:
            emboss = False
            if len(context.space_data.path) > 0:
                emboss = context.space_data.path[-1].node_tree.name == g.name
            op = col.operator("matalogue.goto_group", text=g.name, emboss=emboss, icon="NODETREE")
            op.tree_type = "ShaderNodeTree"
            op.tree = g.name

        col.separator()
        col.separator()
        col.separator()

        # col.label(text="Compositing Groups")
        for g in comp_groups:
            emboss = False
            if len(context.space_data.path) > 0:
                emboss = context.space_data.path[-1].node_tree.name == g.name
            op = col.operator("matalogue.goto_group", text=g.name, emboss=emboss, icon="NODETREE")
            op.tree_type = "CompositorNodeTree"
            op.tree = g.name


def draw_geonodes_panel(self, context, conditions, inverse=False):
    def draw_item(context, col, g, indent):
        active = False
        row = col.row()
        for i in range(indent):
            row.label(text="", icon="BLANK1")
        if len(context.space_data.path) > 0:
            active = context.space_data.path[-1].node_tree.name == g.name
        op = row.operator(
            "matalogue.goto_geo",
            text=g.name,
            emboss=active,
            icon=("TOOL_SETTINGS" if g.is_tool else "MODIFIER" if g.is_modifier else "NODETREE"),
        )
        op.tree = g.name
        op.is_tool = g.is_tool
        row.enabled = context.object is not None  # Avoid hard crashing Blender when there's no active object

        # Node trees in this tree:
        if active:
            already_drawn = []
            for node in g.nodes:
                if node.type == "GROUP" and node.node_tree.name not in already_drawn:
                    draw_item(context, col, node.node_tree, indent + 1)
                    already_drawn.append(node.node_tree.name)

    layout = self.layout

    col = layout.column(align=True)

    geo_nodes = []
    for g in bpy.data.node_groups:
        if g.type == "GEOMETRY" and any((getattr(g, c) is True for c in conditions)) != inverse:
            geo_nodes.append(g)

    for g in geo_nodes:
        draw_item(context, col, g, 0)


def poll_geonodes_panel(conditions, inverse=False):
    for g in bpy.data.node_groups:
        if g.type == "GEOMETRY" and any((getattr(g, c) is True for c in conditions)) != inverse:
            return True
    return False


class MATALOGUE_PT_geonodes(bpy.types.Panel):
    bl_label = "Geo Nodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="GEOMETRY_NODES")

    def draw(self, context):
        pass


class MATALOGUE_PT_geonodes_modifiers(bpy.types.Panel):
    bl_label = "Modifiers"
    bl_parent_id = "MATALOGUE_PT_geonodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    conditions = ["is_modifier"]
    inverse = False

    @classmethod
    def poll(self, context):
        return poll_geonodes_panel(self.conditions, self.inverse)

    def draw(self, context):
        draw_geonodes_panel(self, context, self.conditions, self.inverse)


class MATALOGUE_PT_geonodes_tools(bpy.types.Panel):
    bl_label = "Tools"
    bl_parent_id = "MATALOGUE_PT_geonodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    conditions = ["is_tool"]
    inverse = False

    @classmethod
    def poll(self, context):
        return poll_geonodes_panel(self.conditions, self.inverse)

    def draw(self, context):
        draw_geonodes_panel(self, context, self.conditions, self.inverse)


class MATALOGUE_PT_geonodes_groups(bpy.types.Panel):
    bl_label = "Groups"
    bl_parent_id = "MATALOGUE_PT_geonodes"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    conditions = ["is_modifier", "is_tool"]
    inverse = True

    @classmethod
    def poll(self, context):
        return poll_geonodes_panel(self.conditions, self.inverse)

    def draw(self, context):
        draw_geonodes_panel(self, context, self.conditions, self.inverse)


class MATALOGUE_PT_lighting(bpy.types.Panel):
    bl_label = "Lighting"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    def draw(self, context):
        layout = self.layout
        lights = [obj for obj in context.view_layer.objects if obj.type == "LIGHT"]

        col = layout.column(align=True)

        for light in lights:
            if light.data.use_nodes:
                op = col.operator(
                    "matalogue.goto_light",
                    text=light.name,
                    emboss=(light.data == context.space_data.id),
                    icon="LIGHT_%s" % light.data.type,
                )
                op.light = light.name
                op.world = False

        if context.scene.world:
            if context.scene.world.use_nodes:
                op = col.operator(
                    "matalogue.goto_light",
                    text="World",
                    emboss=(context.scene.world == context.space_data.id),
                    icon="WORLD",
                )
                op.world = True


class MATALOGUE_PT_compositing(bpy.types.Panel):
    bl_label = "Compositing"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Trees"

    def draw(self, context):
        scenes = bpy.data.scenes
        layout = self.layout

        col = layout.column(align=True)

        for sc in scenes:
            name = sc.name
            op = col.operator("matalogue.goto_comp", text=name, emboss=(sc == context.space_data.id), icon="SCENE_DATA")
            op.scene = name


#####################################################################
# Registration
#####################################################################


classes = [
    MatalogueSettings,
    MATALOGUE_OT_go_to_material,
    MATALOGUE_OT_go_to_group,
    MATALOGUE_OT_go_to_geonodes,
    MATALOGUE_OT_go_to_light,
    MATALOGUE_OT_go_to_comp,
    MATALOGUE_PT_materials,
    MATALOGUE_PT_groups,
    MATALOGUE_PT_geonodes,
    MATALOGUE_PT_geonodes_modifiers,
    MATALOGUE_PT_geonodes_tools,
    MATALOGUE_PT_geonodes_groups,
    MATALOGUE_PT_lighting,
    MATALOGUE_PT_compositing,
]


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.matalogue_settings = bpy.props.PointerProperty(type=MatalogueSettings)


def unregister():
    del bpy.types.WindowManager.matalogue_settings

    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
