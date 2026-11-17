# OpenUSD Asset Validator & Scene Assembler

A Python command-line pipeline utility built with Pixar's **OpenUSD (`pxr`)** that automates pre-publish asset sanity checks and non-destructively assembles validated 3D assets into a layered master scene.

## Pipeline Problem Solved

In animation and VFX production, invalid asset publishes (missing `defaultPrim` metadata, mismatched up-axes, broken texture paths, or inconsistent naming conventions) can break downstream lighting and rendering shots. This tool acts as an automated **publish gate**:

1. **Artist-Friendly Validation (`src/validator.py`):** Traverses the USD scene graph to catch common export mistakes early and outputs actionable fix instructions for artists.
2. **Non-Destructive Stage Assembly (`src/assembler.py`):** References validated assets into a unified `/World/Assets` hierarchy with standardized studio stage metadata (`upAxis = "Y"`, `metersPerUnit = 0.01`) and binds a fallback `UsdPreviewSurface` shader if an asset lacks materials.
3. **Production CLI (`src/cli.py`):** Designed for Unix/Linux and Windows studio workflows with `--strict` mode support for CI/CD publish hooks.

## Quickstart

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate.bat

# 2. Install OpenUSD
pip install -r requirements.txt

# 3. Generate sample valid & invalid assets
python create_samples.py

# 4. Run the publish gate and assemble the master scene
python -m src.cli --input sample_assets --output output/master_scene.usda
```

## Example Output

```bash
=== OpenUSD Publish Gate (2 assets scanned) ===

[FAIL] bad_asset_test.usda
   x ERROR: Missing 'defaultPrim'. Set a root Xform as defaultPrim before publishing.
   x ERROR: Invalid upAxis 'Z'. Studio standard requires 'Y'.
   x ERROR: Geometry prim '/Root/Cube_001_FINAL' must start with 'geo_' prefix.
   x ERROR: Broken texture path on '/Root/bad_mat/MissingTex': 'textures/non_existent_texture.png' not found.
   ! WARN : Prim '/Root/Cube_001_FINAL' contains temporary suffix ('FINAL'/'COPY'). Clean up naming.
[PASS] hero_prop_valid.usda -> Referenced at /World/Assets/hero_prop_valid

=== Summary: 1/2 assets published ===
```

## Generated Master Stage (output/master_scene.usda)

```bash
#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 0.01
    upAxis = "Y"
)

def Xform "World"
{
    def Xform "Assets"
    {
        def Xform "hero_prop_valid" (
            prepend references = @../sample_assets/hero_prop_valid.usda@
        )
        {
            double3 xformOp:translate = (5, 0, 0)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
    }

    def Xform "Materials"
    {
        def Material "mat_studio_default"
        {
            token outputs:surface.connect = </World/Materials/mat_studio_default/PreviewSurface.outputs:surface>

            def Shader "PreviewSurface"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.5, 0.5, 0.5)
                float inputs:roughness = 0.4
                token outputs:surface
            }
        }
    }
}
```

## Future Improvements

- **DCC Integration:** Wrap the validator as a pre-export shelf tool inside Autodesk Maya (maya.cmds) or SideFX Houdini (hou).

- **Artist UI:** Build a lightweight PySide6 / Qt panel so artists can visually inspect flagged prims and auto-fix naming or defaultPrim issues with one click.
