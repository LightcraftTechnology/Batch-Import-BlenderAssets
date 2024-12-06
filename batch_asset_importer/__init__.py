bl_info = {
    "name": "Batch Import Assets",
    "author": "Mansur Şamil Güngör",
    "version": (0, 0, 4),
    "blender": (4, 2, 0),
    "location": "3D View > Side Panel > BatchImport",
    "description": "An add-on to batch import all the FBX files and texture sets in a folder.",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}


if "bpy" in locals():
    from importlib import reload
    reload(catalog)
    reload(functions)
    reload(operators)
else:
    from . import catalog, functions, operators


import bpy
import os


def is_file_saved():
    return bpy.data.filepath != ""


def update_folder_path(self, context):
    abs_path = os.path.abspath(bpy.path.abspath(self.folder_path))
    if self.folder_path != abs_path:
        self.folder_path = abs_path


class TextureMappingNamesProperties(bpy.types.PropertyGroup):
    base_color: bpy.props.StringProperty(name="Base Color", default="basecolor")
    ao: bpy.props.StringProperty(name="AO", default="ao")
    metallic: bpy.props.StringProperty(name="Metallic", default="metallic")
    roughness: bpy.props.StringProperty(name="Roughness", default="roughness")
    glossy: bpy.props.StringProperty(name="Glossy", default="glossy")
    normal: bpy.props.StringProperty(name="Normal", default="normal")
    bump: bpy.props.StringProperty(name="Bump", default="bump")
    displacement: bpy.props.StringProperty(name="Displacement", default="displacement")
    opacity: bpy.props.StringProperty(name="Opacity", default="opacity")
    emissive: bpy.props.StringProperty(name="Emissive", default="emissive")
    specular: bpy.props.StringProperty(name="Specular", default="specular")


class BatchImportAssetsProperties(bpy.types.PropertyGroup):
    folder_path: bpy.props.StringProperty(
        name="Folder Path",
        description="The path to the folder containing the FBX files and texture sets",
        default="",
        subtype='DIR_PATH',
        update=update_folder_path
    )
    map_names: bpy.props.PointerProperty(type=TextureMappingNamesProperties)
    asset_tag_name: bpy.props.StringProperty(
        name="Asset Tag",
        description="The tag to be added to the imported assets",
        default="Asset"
    )
    asset_tag_meshes_name: bpy.props.StringProperty(
        name="Asset Tag (Meshes)",
        description="The tag to be added to the imported meshes",
        default="Asset"
    )
    asset_tag_materials_name: bpy.props.StringProperty(
        name="Asset Tag (Materials)",
        description="The tag to be added to the imported materials",
        default="Asset"
    )
    is_apply_transforms: bpy.props.BoolProperty(
        name="Apply Transforms",
        description="Apply transforms to the imported objects",
        default=True
    )
    is_save_blend_file: bpy.props.BoolProperty(
        name="Save Blend File",
        description="Save the blend file before importing assets",
        default=True
    )
    use_diffuse: bpy.props.BoolProperty(
        name="Use Diffuse",
        description="Use the diffuse texture if available",
        default=True
    )
    is_import_textures: bpy.props.BoolProperty(
        name="Import Textures",
        description="Import textures from the texture sets",
        default=True
    )
    is_import_fbx: bpy.props.BoolProperty(
        name="Import FBX",
        description="Import the FBX file in the folder",
        default=True
    )
    is_expand_map_settings: bpy.props.BoolProperty(
        name="Expand Map Settings",
        default=True
    )
    use_ao: bpy.props.BoolProperty(
        name="Use AO",
        description="Use the ambient occlusion texture if available",
        default=True
    )
    use_metallic: bpy.props.BoolProperty(
        name="Use Metallic",
        description="Use the metallic texture if available",
        default=True
    )
    use_roughness: bpy.props.BoolProperty(
        name="Use Roughness",
        description="Use the roughness (or glossy) texture if available",
        default=True
    )
    use_normal: bpy.props.BoolProperty(
        name="Use Normal",
        description="Use the normal texture if available",
        default=True
    )
    use_bump: bpy.props.BoolProperty(
        name="Use Bump",
        description="Use the bump texture if available",
        default=False
    )
    use_displacement: bpy.props.BoolProperty(
        name="Use Displacement",
        description="Use the displacement texture if available",
        default=False
    )
    use_opacity: bpy.props.BoolProperty(
        name="Use Opacity",
        description="Use the opacity texture if available",
        default=True
    )
    use_emissive: bpy.props.BoolProperty(
        name="Use Emissive",
        description="Use the emissive texture if available",
        default=True
    )
    use_specular: bpy.props.BoolProperty(
        name="Use Specular",
        description="Use the specular texture if available",
        default=False
    )
    bump_distance: bpy.props.FloatProperty(
        name="Bump Distance",
        description="The distance of the bump effect",
        default=0.01
    )
    displacement_scale: bpy.props.FloatProperty(
        name="Displacement Scale",
        description="The scale of the displacement effect",
        default=0.1
    )
    normal_strength: bpy.props.FloatProperty(
        name="Normal Strength",
        description="The strength of the normal map effect",
        default=1.0
    )
    ao_factor: bpy.props.FloatProperty(
        name="AO Factor",
        description="The factor of the ambient occlusion effect",
        default=1.0
    )
    main_collection_name: bpy.props.StringProperty(
        name="Main Collection Name",
        description="The name of the main collection to import the assets",
        default="Assets"
    )
    asset_type: bpy.props.EnumProperty(
        name="Asset Type",
        description="The type of the assets to be imported",
        items=(
            ("COLLECTION", "Collection", "Save the assets as collections", "COLLECTION", 0),
            ("OBJECT", "Object", "Save the assets as objects", "OBJECT", 1),
        ),
        default="COLLECTION"
    )


class BatchImportAssetsWMProperties(bpy.types.PropertyGroup):
    show_save_info: bpy.props.BoolProperty(default=False)


class BIA_PT_main_panel(bpy.types.Panel):
    bl_label = "Batch Import Assets"
    bl_idname = "BIA_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BatchImport'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.batch_import_assets_props
        wm_props = context.window_manager.batch_import_assets_wm_props

        box = layout.box()
        if not is_file_saved():
            col = box.column(align=True)
            col.label(text="You must save the file")
            col.label(text="before you can import")
            col.label(text="assets.")

            row = layout.row()
            row.scale_y = 2.0
            row.operator("import_assets.open_save_dialog", text="Save File", icon="FILE_TICK")
            return

        col = box.column(align=True)
        col.label(text="Folder Path:")
        col.prop(props, "folder_path", text="")

        col = box.column(align=True)
        col.prop(props, "is_import_fbx", text="Import FBX", toggle=True)
        col.prop(props, "is_import_textures", text="Import Textures", toggle=True)

        if props.is_import_textures:
            box0 = box.box()
            row = box0.row(align=True)
            row.alignment = "LEFT"
            row.prop(
                props, "is_expand_map_settings", text="Map Settings",
                icon="TRIA_DOWN" if props.is_expand_map_settings else "TRIA_RIGHT", emboss=False
            )

            if props.is_expand_map_settings:
                col = box0.column(align=True)
                col.prop(props, "use_diffuse", text="Use Diffuse", toggle=True)
                row = col.row(align=True)
                row.prop(props, "use_ao", text="Use AO", toggle=True)
                row.enabled = props.use_diffuse
                col.prop(props, "use_metallic", text="Use Metallic", toggle=True)
                col.prop(props, "use_roughness", text="Use Roughness", toggle=True)
                col.prop(props, "use_specular", text="Use Specular", toggle=True)
                col.prop(props, "use_normal", text="Use Normal", toggle=True)
                col.prop(props, "use_bump", text="Use Bump", toggle=True)
                col.prop(props, "use_displacement", text="Use Displacement", toggle=True)
                col.prop(props, "use_opacity", text="Use Opacity", toggle=True)
                col.prop(props, "use_emissive", text="Use Emissive", toggle=True)

                col = box0.column(align=True)
                if props.use_ao and props.use_diffuse:
                    col.prop(props, "ao_factor", text="AO Factor")
                if props.use_normal:
                    col.prop(props, "normal_strength", text="Normal Strength")
                if props.use_bump:
                    col.prop(props, "bump_distance", text="Bump Distance")
                if props.use_displacement:
                    col.prop(props, "displacement_scale", text="Disp Scale")
        
        col = box.column()
        col.prop(props, "is_apply_transforms", text="Apply Transforms")
        col.prop(props, "is_save_blend_file", text="Save Blend File")

        if wm_props.show_save_info:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Assets previews are ", icon="INFO")
            col.label(text="being generated. Please wait")
            col.label(text="a while and save the file")
            col.label(text="again to keep the previews.")
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Model Asset Type:")
        row = col.row(align=True)
        row.prop(props, "asset_type", expand=True)

        row = layout.row()
        row.scale_y = 2.0
        row.operator("import_assets.batch_import_assets", text="Import Assets", icon="IMPORT")


classes = (
    TextureMappingNamesProperties,
    BatchImportAssetsWMProperties,
    BatchImportAssetsProperties,
    BIA_PT_main_panel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    operators.register()

    bpy.types.Scene.batch_import_assets_props = bpy.props.PointerProperty(type=BatchImportAssetsProperties)
    bpy.types.WindowManager.batch_import_assets_wm_props = bpy.props.PointerProperty(type=BatchImportAssetsWMProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    operators.unregister()

    del bpy.types.Scene.batch_import_assets_props
    del bpy.types.WindowManager.batch_import_assets_wm_props


if __name__ == "__main__":
    register()
