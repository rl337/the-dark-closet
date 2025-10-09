#!/usr/bin/env python3
"""
Build script to generate procedural character assets and integrate them into the game.
This replaces the need for external asset files and npm packages.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import json

# Add src to path for imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from the_dark_closet.assets import generate_character_assets


def create_asset_config(assets: dict, output_dir: Path) -> None:
    """Create a configuration file for the generated assets."""
    config = {
        "name": "pinocchio-character",
        "canvas": {"width": 256, "height": 256},
        "assetsRoot": str(output_dir),
        "outputRoot": str(output_dir / "frames"),
        "parts": {
            "head": "body/head.png",
            "torso": "body/torso.png", 
            "left_arm": "body/left_arm.png",
            "right_arm": "body/right_arm.png",
            "left_leg": "body/left_leg.png",
            "right_leg": "body/right_leg.png",
            "hat": "gear/hat.png",
            "eyes_open": "face/eyes/eyes_open.png",
            "eyes_closed": "face/eyes/eyes_closed.png",
            "mouth_neutral": "face/mouths/mouth_neutral.png",
            "mouth_open": "face/mouths/mouth_open.png"
        },
        "layerOrder": [
            "left_leg",
            "right_leg", 
            "torso",
            "left_arm",
            "right_arm",
            "head",
            "eyes_open",
            "mouth_neutral",
            "hat"
        ],
        "animations": {
            "idle": {
                "frames": [
                    {
                        "transforms": {
                            "left_arm": {"dx": 0, "dy": 0},
                            "right_arm": {"dx": 0, "dy": 2},
                            "left_leg": {"dx": 0, "dy": 0},
                            "right_leg": {"dx": 0, "dy": 1}
                        },
                        "face": {"eyes": "eyes_open", "mouth": "mouth_neutral"}
                    },
                    {
                        "transforms": {
                            "left_arm": {"dx": 0, "dy": 1},
                            "right_arm": {"dx": 0, "dy": 0},
                            "left_leg": {"dx": 0, "dy": 1},
                            "right_leg": {"dx": 0, "dy": 0}
                        },
                        "face": {"eyes": "eyes_open", "mouth": "mouth_neutral"}
                    },
                    {
                        "transforms": {
                            "left_arm": {"dx": 0, "dy": 2},
                            "right_arm": {"dx": 0, "dy": 0},
                            "left_leg": {"dx": 0, "dy": 0},
                            "right_leg": {"dx": 0, "dy": 2}
                        },
                        "face": {"eyes": "eyes_open", "mouth": "mouth_neutral"}
                    },
                    {
                        "transforms": {
                            "left_arm": {"dx": 0, "dy": 1},
                            "right_arm": {"dx": 0, "dy": 1},
                            "left_leg": {"dx": 0, "dy": 1},
                            "right_leg": {"dx": 0, "dy": 1}
                        },
                        "face": {"eyes": "eyes_open", "mouth": "mouth_neutral"}
                    }
                ]
            },
            "talk": {
                "frames": [
                    {
                        "transforms": {},
                        "face": {"eyes": "eyes_open", "mouth": "mouth_open"}
                    },
                    {
                        "transforms": {},
                        "face": {"eyes": "eyes_open", "mouth": "mouth_neutral"}
                    },
                    {
                        "transforms": {},
                        "face": {"eyes": "eyes_open", "mouth": "mouth_open"}
                    },
                    {
                        "transforms": {},
                        "face": {"eyes": "eyes_closed", "mouth": "mouth_open"}
                    },
                    {
                        "transforms": {},
                        "face": {"eyes": "eyes_open", "mouth": "mouth_neutral"}
                    }
                ]
            }
        }
    }
    
    config_path = output_dir / "character_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created asset configuration: {config_path}")


def main():
    """Main build function."""
    print("Building procedural character assets...")
    
    # Set up output directory
    output_dir = ROOT / "generated_assets"
    
    # Generate assets
    assets = generate_character_assets(output_dir)
    
    print(f"Generated {len(assets)} character assets:")
    for name, path in assets.items():
        print(f"  {name}: {path}")
    
    # Create configuration file
    create_asset_config(assets, output_dir)
    
    print(f"\nAsset generation complete!")
    print(f"Assets saved to: {output_dir}")
    print(f"Configuration saved to: {output_dir / 'character_config.json'}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
