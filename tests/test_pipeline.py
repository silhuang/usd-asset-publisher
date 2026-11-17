import os
import tempfile
import unittest
from pxr import Usd, UsdGeom, UsdShade, Sdf
from src.validator import USDAssetValidator
from src.assembler import USDStageAssembler


class TestUSDPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = self.test_dir.name
        self.validator = USDAssetValidator(required_up_axis="Y")

    def tearDown(self):
        self.test_dir.cleanup()

    def _create_asset(self, filename, set_default=True, up_axis="Y", mesh_name="geo_cube", tex_rel=None):
        path = os.path.join(self.root, filename)
        stage = Usd.Stage.CreateNew(path)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y if up_axis == "Y" else UsdGeom.Tokens.z)

        xform = UsdGeom.Xform.Define(stage, "/Asset")
        if set_default:
            stage.SetDefaultPrim(xform.GetPrim())

        UsdGeom.Cube.Define(stage, f"/Asset/{mesh_name}")

        if tex_rel:
            shader = UsdShade.Shader.Define(stage, "/Asset/Shader")
            shader.CreateIdAttr("UsdUVTexture")
            shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(tex_rel))

        stage.GetRootLayer().Save()
        return path

    def test_valid_asset_passes(self):
        asset_path = self._create_asset("valid.usda")
        report = self.validator.validate(asset_path)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.errors), 0)

    def test_missing_default_prim_and_wrong_axis_fail(self):
        asset_path = self._create_asset("bad.usda", set_default=False, up_axis="Z", mesh_name="Cube_FINAL")
        report = self.validator.validate(asset_path)
        self.assertFalse(report.passed)
        self.assertTrue(any("defaultPrim" in e for e in report.errors))
        self.assertTrue(any("upAxis" in e for e in report.errors))
        self.assertTrue(any("geo_" in e for e in report.errors))
        self.assertTrue(any("FINAL" in w for w in report.warnings))

    def test_missing_texture_fails(self):
        asset_path = self._create_asset("missing_tex.usda", tex_rel="textures/does_not_exist.png")
        report = self.validator.validate(asset_path)
        self.assertFalse(report.passed)
        self.assertTrue(any("Broken texture path" in e for e in report.errors))

    def test_assembler_creates_master_stage(self):
        asset_path = self._create_asset("prop.usda")
        out_path = os.path.join(self.root, "out", "master.usda")
        assembler = USDStageAssembler(out_path)
        prim_path = assembler.add_asset(asset_path)
        assembler.save()

        self.assertEqual(prim_path, "/World/Assets/prop")
        stage = Usd.Stage.Open(out_path)
        self.assertEqual(stage.GetDefaultPrim().GetName(), "World")
        self.assertTrue(stage.GetPrimAtPath("/World/Assets/prop").IsValid())


if __name__ == "__main__":
    unittest.main()