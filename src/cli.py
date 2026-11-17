import argparse
import glob
import os
import sys
from src.validator import USDAssetValidator
from src.assembler import USDStageAssembler


def main():
    parser = argparse.ArgumentParser(
        description="OpenUSD Asset Validator & Scene Assembler (Studio Publish Gate)"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing .usd/.usda/.usdc assets to validate and publish",
    )
    parser.add_argument(
        "--output",
        default="output/master_scene.usda",
        help="Output path for the assembled master .usda scene",
    )
    parser.add_argument(
        "--up-axis",
        choices=["Y", "Z"],
        default="Y",
        help="Required studio stage up-axis (default: Y)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as validation failures",
    )
    args = parser.parse_args()

    patterns = ["*.usd", "*.usda", "*.usdc"]
    asset_files = []
    for pat in patterns:
        asset_files.extend(glob.glob(os.path.join(args.input, pat)))

    if not asset_files:
        print(f"[ERROR] No USD files found in '{args.input}'")
        sys.exit(1)

    validator = USDAssetValidator(required_up_axis=args.up_axis)
    assembler = USDStageAssembler(output_path=args.output)

    print(f"=== OpenUSD Publish Gate ({len(asset_files)} assets scanned) ===\n")
    published_count = 0

    for idx, filepath in enumerate(sorted(asset_files)):
        report = validator.validate(filepath)
        passed = report.passed and (not args.strict or len(report.warnings) == 0)

        if passed:
            prim_path = assembler.add_asset(filepath, offset_x=idx * 5.0)
            published_count += 1
            print(f"[PASS] {os.path.basename(filepath)} -> Referenced at {prim_path}")
        else:
            print(f"[FAIL] {os.path.basename(filepath)}")
            for err in report.errors:
                print(f"   x ERROR: {err}")

        for warn in report.warnings:
            print(f"   ! WARN : {warn}")

    assembler.save()
    print(f"\n=== Summary: {published_count}/{len(asset_files)} assets published ===")
    print(f"Master stage written to: {args.output}")


if __name__ == "__main__":
    main()