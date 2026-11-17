import os
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf


class USDStageAssembler:
    """Assembles validated USD assets into a layered master scene."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.stage = Usd.Stage.CreateNew(output_path)

        # Configure studio stage defaults
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.y)
        UsdGeom.SetStageMetersPerUnit(self.stage, 0.01)

        world = UsdGeom.Xform.Define(self.stage, "/World")
        self.stage.SetDefaultPrim(world.GetPrim())
        UsdGeom.Xform.Define(self.stage, "/World/Assets")
        UsdGeom.Xform.Define(self.stage, "/World/Materials")

        self.fallback_mat = self._create_fallback_material()

    def _create_fallback_material(self) -> UsdShade.Material:
        mat = UsdShade.Material.Define(self.stage, "/World/Materials/mat_studio_default")
        shader = UsdShade.Shader.Define(
            self.stage, "/World/Materials/mat_studio_default/PreviewSurface"
        )
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0.5, 0.5, 0.5)
        )
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        return mat

    def add_asset(self, asset_path: str, offset_x: float = 0.0) -> str:
        base_name = os.path.splitext(os.path.basename(asset_path))[0]
        prim_name = "".join(c if c.isalnum() or c == "_" else "_" for c in base_name)
        prim_path = f"/World/Assets/{prim_name}"

        asset_xform = UsdGeom.Xform.Define(self.stage, prim_path)
        if offset_x != 0.0:
            asset_xform.AddTranslateOp().Set(Gf.Vec3d(offset_x, 0.0, 0.0))

        # Relative reference from output directory to the source asset
        rel_path = os.path.relpath(
            os.path.abspath(asset_path),
            start=os.path.dirname(os.path.abspath(self.output_path)),
        ).replace("\\", "/")

        asset_xform.GetPrim().GetReferences().AddReference(rel_path)

        # Bind fallback material if asset has no material prims
        asset_stage = Usd.Stage.Open(asset_path)
        has_material = any(
            p.IsA(UsdShade.Material) for p in asset_stage.Traverse()
        )
        
        if not has_material:
            UsdShade.MaterialBindingAPI.Apply(asset_xform.GetPrim()).Bind(
                self.fallback_mat
            )

        return prim_path

    def save(self):
        self.stage.GetRootLayer().Save()