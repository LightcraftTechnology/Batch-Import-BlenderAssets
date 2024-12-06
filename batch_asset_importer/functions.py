import bpy
import os
from . import catalog


def import_fbx_files_and_textures(folder_path):
    props = bpy.context.scene.batch_import_assets_props

    for root, dirs, files in os.walk(folder_path):
        for dir in dirs:
            # Check if FBX file exists in the current folder
            fbx_path = ""
            for file in os.listdir(os.path.join(root, dir)):
                if file.endswith(".fbx"):
                    fbx_path = os.path.join(root, dir, file)
                    break
            if props.is_import_textures:
                mat = create_material(dir)
                mat.use_fake_user = True
                textures = import_textures_from_folder(os.path.join(root, dir))
                assign_textures_to_material(mat, textures)
            if props.is_import_fbx and os.path.isfile(fbx_path):
                bpy.ops.import_scene.fbx(filepath=fbx_path)
                assign_material_to_selected_objects(mat)


def assign_material_to_selected_objects(material):
    for obj in bpy.context.selected_objects:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(material)


def assign_textures_to_material(material, textures):
    props = bpy.context.scene.batch_import_assets_props
    map_names = props.map_names

    node_tree = material.node_tree
    nodes = node_tree.nodes
    n_princ = nodes.get("Principled BSDF")
    n_mat_output = nodes.get("Material Output")

    primary_nodes = {
        map_names.base_color: None,
        map_names.ao: None,
        map_names.metallic: None,
        map_names.roughness: None,
        map_names.glossy: None,
        map_names.opacity: None,
        map_names.normal: None,
        map_names.bump: None,
        map_names.specular: None,
        map_names.displacement: None,
        map_names.emissive: None,
    }
    secondary_nodes = {
        "mix_rgb": None,
        "invert_gloss": None,
        "normal": None,
        "displacement": None,
    }
    tertiary_nodes = {
        "bump": None,
    }

    has_roughness = map_names.roughness in textures
    has_glossy = map_names.glossy in textures and props.use_roughness
    has_diffuse = map_names.base_color in textures and props.use_diffuse
    has_ao = map_names.ao in textures and props.use_ao
    has_normal = map_names.normal in textures and props.use_normal
    has_bump = map_names.bump in textures and props.use_bump
    has_displacement = map_names.displacement in textures and props.use_displacement

    # Create secondary and tertiary nodes
    if has_normal:
        n_normal = nodes.new("ShaderNodeNormalMap")
        n_normal.inputs["Strength"].default_value = props.normal_strength
        secondary_nodes["normal"] = n_normal
    if has_bump:
        n_bump = nodes.new("ShaderNodeBump")
        n_bump.inputs["Distance"].default_value = props.bump_distance
        tertiary_nodes["bump"] = n_bump
    if has_displacement:
        n_disp = nodes.new("ShaderNodeDisplacement")
        n_disp.inputs["Scale"].default_value = props.displacement_scale
        secondary_nodes["displacement"] = n_disp
    if has_glossy and not has_roughness:
        n_invert_gloss = nodes.new("ShaderNodeInvert")
        secondary_nodes["invert_gloss"] = n_invert_gloss
    if has_ao and has_diffuse:
        n_mix_ao = nodes.new("ShaderNodeMixRGB")
        n_mix_ao.blend_type = "MULTIPLY"
        n_mix_ao.inputs["Fac"].default_value = props.ao_factor
        secondary_nodes["mix_rgb"] = n_mix_ao
    
    normal_target = n_bump if has_bump else n_princ

    for texture_type, texture in textures.items():
        if texture_type != map_names.base_color and texture_type != map_names.emissive:
            texture.colorspace_settings.name = "Non-Color"

        if texture_type == map_names.base_color and props.use_diffuse:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            n_tex.select = True
            node_tree.nodes.active = n_tex
            primary_nodes[map_names.base_color] = n_tex
            if has_ao:
                node_tree.links.new(n_tex.outputs["Color"], n_mix_ao.inputs["Color1"])
                node_tree.links.new(n_mix_ao.outputs["Color"], n_princ.inputs["Base Color"])
            else:
                node_tree.links.new(n_tex.outputs["Color"], n_princ.inputs["Base Color"])

        elif texture_type == map_names.normal and props.use_normal:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.normal] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_normal.inputs["Color"])
            node_tree.links.new(n_normal.outputs["Normal"], normal_target.inputs["Normal"])

        elif texture_type == map_names.ao and props.use_ao and has_diffuse:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.ao] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_mix_ao.inputs["Color2"])
            node_tree.links.new(n_mix_ao.outputs["Color"], n_princ.inputs["Base Color"])

        elif texture_type == map_names.metallic and props.use_metallic:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.metallic] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_princ.inputs["Metallic"])

        elif texture_type == map_names.roughness and props.use_roughness:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.roughness] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_princ.inputs["Roughness"])

        elif texture_type == map_names.glossy and not has_roughness and props.use_roughness:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.glossy] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_invert_gloss.inputs["Color"])
            node_tree.links.new(n_invert_gloss.outputs["Color"], n_princ.inputs["Roughness"])

        elif texture_type == map_names.specular and props.use_specular:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.specular] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_princ.inputs["Specular IOR Level"])

        elif texture_type == map_names.displacement and props.use_displacement:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.displacement] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_disp.inputs["Height"])
            node_tree.links.new(n_disp.outputs["Displacement"], n_mat_output.inputs["Displacement"])

        elif texture_type == map_names.opacity and props.use_opacity:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.opacity] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_princ.inputs["Alpha"])
        
        elif texture_type == map_names.bump and props.use_bump:
            n_tex = nodes.new("ShaderNodeTexImage")
            n_tex.image = texture
            primary_nodes[map_names.bump] = n_tex
            node_tree.links.new(n_tex.outputs["Color"], n_bump.inputs["Height"])
            node_tree.links.new(n_bump.outputs["Normal"], n_princ.inputs["Normal"])

    position_nodes(primary_nodes, secondary_nodes, tertiary_nodes, n_princ)


def position_nodes(primary_nodes, secondary_nodes, tertiary_nodes, n_princ):
    props = bpy.context.scene.batch_import_assets_props
    map_names = props.map_names

    map_order = [
        map_names.base_color,
        map_names.ao,
        map_names.metallic,
        map_names.roughness,
        map_names.glossy,
        map_names.opacity,
        map_names.normal,
        map_names.bump,
        map_names.specular,
        map_names.displacement,
        map_names.emissive,
    ]

    princ_location = n_princ.location
    x_offset = 400
    y_offset = 300

    valid_primary_nodes = [node for node in primary_nodes.values() if node is not None]
    valid_secondary_nodes = [node for node in secondary_nodes.values() if node is not None]
    valid_tertiary_nodes = [node for node in secondary_nodes.values() if node is not None]

    y_current_offset_primary = y_offset * (len(valid_primary_nodes) - 1) / 2

    i = 0
    x_factor = 1
    if len(valid_secondary_nodes) > 0:
        x_factor += 1
    if len(valid_tertiary_nodes) > 0:
        x_factor += 1

    for map_name in map_order:
        if primary_nodes[map_name] is None:
            continue
        primary_nodes[map_name].location = (princ_location[0] - x_offset * x_factor, princ_location[1] + y_offset * -i + y_current_offset_primary)
        i += 1
    
    if (len(valid_tertiary_nodes) > 0):
        x_factor -= 1
    for node_name, node in tertiary_nodes.items():
        if node is None:
            continue
        if node_name == "bump":
            n_bump = primary_nodes[map_names.bump]
            node.location = (n_bump.location[0] + x_offset * x_factor, n_bump.location[1])

    if (len(valid_secondary_nodes) > 0):
        x_factor -= 1
    for node_name, node in secondary_nodes.items():
        if node is None:
            continue
        if node_name == "mix_rgb":
            n_ao = primary_nodes[map_names.ao]
            node.location = (n_ao.location[0] + x_offset * x_factor, n_ao.location[1] + y_offset / 1.5)
        elif node_name == "invert_gloss":
            n_glossy = primary_nodes[map_names.glossy]
            node.location = (n_glossy.location[0] + x_offset * x_factor, n_glossy.location[1])
        elif node_name == "normal":
            n_normal = primary_nodes[map_names.normal]
            node.location = (n_normal.location[0] + x_offset * x_factor, n_normal.location[1])
        elif node_name == "displacement":
            n_disp = primary_nodes[map_names.displacement]
            node.location = (n_disp.location[0] + x_offset * x_factor, n_disp.location[1])


def import_textures_from_folder(textures_folder):
    textures = {}
    for texture_file in os.listdir(textures_folder):
        texture_path = os.path.join(textures_folder, texture_file)
        if not texture_file.endswith((".png", ".jpg", ".jpeg", ".tga", ".bmp", ".tif", ".tiff")):
            continue
        image = bpy.data.images.load(texture_path, check_existing=True)
        texture_type = get_texture_type(texture_file)
        if not texture_type:
            continue
        textures[texture_type] = image
    return textures


def get_texture_type(texture_name):
    props = bpy.context.scene.batch_import_assets_props
    names = props.map_names

    name_mappings = {
        names.base_color: ["basecolor", "albedo", "diffuse", "color", "col"],
        names.ao: ["ao", "ambientocclusion"],
        names.metallic: ["metallic", "metal", "metalness"],
        names.roughness: ["roughness", "rough"],
        names.glossy: ["glossy", "gloss"],
        names.normal: ["normal", "nor"],
        names.bump: ["bump"],
        names.displacement: ["displacement", "disp"],
        names.opacity: ["opacity", "alpha"],
        names.emissive: ["emissive", "emit"],
        names.specular: ["specular", "spec"],
    }

    for key, values in name_mappings.items():
        identifier = texture_name.split("_")[-1].split(".")[0]
        if identifier.lower() in values:
            return key
    return None


def create_material(material_name):
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]

    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Metallic"].default_value = 0.0
    return material


#-----Object Functions-----#
def get_main_collection():
    props = bpy.context.scene.batch_import_assets_props
    main_collection = bpy.data.collections.get(props.main_collection_name)
    if not main_collection:
        main_collection = bpy.data.collections.new(props.main_collection_name)
        bpy.context.scene.collection.children.link(main_collection)
    return main_collection


def clear_parent_and_keep_transform(obj):
    if obj.parent is not None:
        obj_mat = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = obj_mat
    return obj


def clear_parent(obj):
    if obj.parent is not None:
        obj.parent = None
    return obj


def clear_parents_and_keep_transform():
    for obj in bpy.context.view_layer.objects:
        clear_parent_and_keep_transform(obj)


def clear_parents_of_all_objects():
    for obj in bpy.context.view_layer.objects:
        clear_parent(obj)


def delete_empties():
    for obj in bpy.context.view_layer.objects:
        if obj.type == "EMPTY":
            bpy.data.objects.remove(obj)


def apply_all_transforms():
    for obj in bpy.context.view_layer.objects:
        obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def mark_all_objects_as_asset(meshes_catalog_uuid):
    props = bpy.context.scene.batch_import_assets_props
    objects = list(bpy.context.view_layer.objects)
    i = 0
    for obj in objects:
        i += 1
        print("Total Objects: ", len(objects))
        print(f"Processing: {obj.name}")
        print(f"Progress: {i}/{len(objects)}")
        if obj.type != "MESH":
            continue
        # First create a collection for the asset
        if props.asset_type == "COLLECTION":
            col = bpy.data.collections.new(obj.name)
            main_collection = get_main_collection()
            main_collection.children.link(col)

            for parent_col in obj.users_collection:
                parent_col.objects.unlink(obj)
            col.objects.link(obj)

            col.asset_mark()
            col.asset_generate_preview()
            col.asset_data.catalog_id = meshes_catalog_uuid
        else:
            obj.asset_mark()
            obj.asset_generate_preview()
            obj.asset_data.catalog_id = meshes_catalog_uuid


def mark_unused_materials_as_asset(materials_catalog_uuid):
    for mat in bpy.data.materials:
        if not mat.use_fake_user or mat.users != 1:
            continue
        mat.asset_mark()
        mat.asset_generate_preview()
        mat.asset_data.catalog_id = materials_catalog_uuid


#-----Catalog Management Functions-----#
def get_blend_folder_path():
    return os.path.dirname(os.path.abspath(bpy.path.abspath(bpy.data.filepath)))


def create_catalog_file():
    catalog_file = catalog.AssetCatalogFile(get_blend_folder_path(), load_from_file=True)
    catalog_file.ensure_exists()
    return catalog_file


def add_new_catalog(catalog_file, catalog_name, main_catalog_name="", is_main_catalog=False):
    if is_main_catalog:
        catalog_file.add_catalog(catalog_name)
    else:
        catalog_file.add_catalog(
            f"{main_catalog_name}-{catalog_name}",
            f"{main_catalog_name}/{catalog_name}") 
    catalog_file.write()


def get_catalogs(main_catalog_name):
    catalog_file = create_catalog_file()

    meshes_name = "Models"
    materials_name = "Materials"

    # Add main catalog
    add_new_catalog(catalog_file, main_catalog_name, is_main_catalog=True)

    # Add mesh catalog
    add_new_catalog(catalog_file, meshes_name, main_catalog_name)
    
    # Add material catalog
    add_new_catalog(catalog_file, materials_name, main_catalog_name)

    meshes_uuid = ""
    materials_uuid = ""
    for path, catalog in catalog_file.catalogs.items():
        if catalog.name == f"{main_catalog_name}-{meshes_name}":
            meshes_uuid = catalog.uuid
        elif catalog.name == f"{main_catalog_name}-{materials_name}":
            materials_uuid = catalog.uuid
    
    return (meshes_uuid, materials_uuid)
