import bpy
import os

from .functions import (
    import_fbx_files_and_textures,
    clear_parents_and_keep_transform,
    delete_empties,
    apply_all_transforms,
    mark_all_objects_as_asset,
    mark_unused_materials_as_asset,
    get_catalogs
)


class BIA_OT_import_assets(bpy.types.Operator):
    bl_idname = "import_assets.batch_import_assets"
    bl_label = "Batch Import Assets"
    bl_description = "Batch import all the FBX files and texture sets in a folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.batch_import_assets_props
        wm_props = context.window_manager.batch_import_assets_wm_props

        folder_name = os.path.basename(props.folder_path)
        props.main_collection_name = folder_name

        # Delete all existing empty collections
        for collection in bpy.data.collections:
            if not collection.objects:
                bpy.data.collections.remove(collection)

        import_fbx_files_and_textures(context.scene.batch_import_assets_props.folder_path)
        clear_parents_and_keep_transform()
        delete_empties()

        if props.is_apply_transforms:
            apply_all_transforms()

        meshes_catalog_uuid, materials_catalog_uuid = get_catalogs(folder_name)
        
        mark_all_objects_as_asset(meshes_catalog_uuid)

        bpy.ops.outliner.orphans_purge(do_recursive=True)

        mark_unused_materials_as_asset(materials_catalog_uuid)

        if props.is_save_blend_file:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        
        wm_props.show_save_info = True
        self.report({'INFO'}, "Batch import completed.")
        return {'FINISHED'}


class BIA_OT_open_save_dialog(bpy.types.Operator):
    bl_idname = "import_assets.open_save_dialog"
    bl_label = "Open Save Dialog"
    bl_description = "Open the save dialog to save the file"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.save_as_mainfile('INVOKE_DEFAULT')
        return {'FINISHED'}


classes = (
    BIA_OT_import_assets,
    BIA_OT_open_save_dialog
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
