import os
from dataclasses import dataclass, field
from pxr import Usd, UsdGeom, UsdShade


@dataclass
class ValidationReport:
    asset_path: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str):
        self.passed = False
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)


class USDAssetValidator:
    """Runs studio publish-gate sanity checks on an OpenUSD asset."""

    def __init__(self, required_up_axis: str = "Y"):
        self.required_up_axis = required_up_axis

    def validate(self, asset_path: str) -> ValidationReport:
        report = ValidationReport(asset_path=asset_path)

        if not os.path.exists(asset_path):
            report.add_error(f"File does not exist: {asset_path}")
            return report

        stage = Usd.Stage.Open(asset_path)
        if not stage:
            report.add_error("Unable to open file as a valid USD stage.")
            return report

        # 1. Check defaultPrim (required for clean referencing downstream)
        default_prim = stage.GetDefaultPrim()
        if not default_prim or not default_prim.IsValid():
            report.add_error(
                "Missing 'defaultPrim'. Set a root Xform as defaultPrim before publishing."
            )

        # 2. Check Stage Up-Axis
        up_axis = UsdGeom.GetStageUpAxis(stage)
        if up_axis != self.required_up_axis:
            report.add_error(
                f"Invalid upAxis '{up_axis}'. Studio standard requires '{self.required_up_axis}'."
            )

        asset_dir = os.path.dirname(os.path.abspath(asset_path))

        # 3. Traverse Scene Graph for Naming & Texture Dependency Checks
        for prim in stage.Traverse():
            name = prim.GetName()

            if "FINAL" in name.upper() or "COPY" in name.upper():
                report.add_warning(
                    f"Prim '{prim.GetPath()}' contains temporary suffix ('FINAL'/'COPY'). Clean up naming."
                )

            # Geometry naming convention check
            if prim.IsA(UsdGeom.Gprim) and not name.startswith("geo_"):
                report.add_error(
                    f"Geometry prim '{prim.GetPath()}' must start with 'geo_' prefix."
                )

            # Shader texture path check
            if prim.IsA(UsdShade.Shader):
                shader = UsdShade.Shader(prim)
                file_input = shader.GetInput("file")
                if file_input:
                    asset_val = file_input.Get()
                    if asset_val and asset_val.path:
                        resolved = os.path.normpath(os.path.join(asset_dir, asset_val.path))
                        if not os.path.exists(resolved):
                            report.add_error(
                                f"Broken texture path on '{prim.GetPath()}': '{asset_val.path}' not found."
                            )

        return report