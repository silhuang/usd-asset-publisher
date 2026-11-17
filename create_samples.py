from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf


def create_valid_asset(path="sample_assets/hero_prop_valid.usda"):
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    root = UsdGeom.Xform.Define(stage, "/HeroProp")
    stage.SetDefaultPrim(root.GetPrim())

    # Valid mesh naming (geo_ prefix)
    mesh = UsdGeom.Cube.Define(stage, "/HeroProp/geo_body")
    mesh.CreateSizeAttr(2.0)

    # Valid material + existing texture reference
    mat = UsdShade.Material.Define(stage, "/HeroProp/mat_metal")
    shader = UsdShade.Shader.Define(stage, "/HeroProp/mat_metal/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")

    tex = UsdShade.Shader.Define(stage, "/HeroProp/mat_metal/AlbedoTex")
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
        Sdf.AssetPath("textures/metal_albedo.png")
    )

    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
        tex.ConnectableAPI(), "rgb"
    )
    mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)

    stage.GetRootLayer().Save()
    print(f"Created valid asset: {path}")


def create_broken_asset(path="sample_assets/bad_asset_test.usda"):
    stage = Usd.Stage.CreateNew(path)
    # Mistake 1: Wrong Up-Axis (Z instead of studio standard Y)
    
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    # Mistake 2: Missing defaultPrim!

    # Mistake 3: Non-standard naming (no geo_ prefix, contains FINAL)
    mesh = UsdGeom.Cube.Define(stage, "/Root/Cube_001_FINAL")

    # Mistake 4: Broken texture reference
    mat = UsdShade.Material.Define(stage, "/Root/bad_mat")
    tex = UsdShade.Shader.Define(stage, "/Root/bad_mat/MissingTex")
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
        Sdf.AssetPath("textures/non_existent_texture.png")
    )

    stage.GetRootLayer().Save()
    print(f"Created broken asset: {path}")


if __name__ == "__main__":
    create_valid_asset()
    create_broken_asset()