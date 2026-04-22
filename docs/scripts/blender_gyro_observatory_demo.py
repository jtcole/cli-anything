#!/usr/bin/env python3
"""Build a complex Blender demo scene with real preview checkpoints."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
BLENDER_HARNESS_ROOT = REPO_ROOT / "blender" / "agent-harness"
sys.path.insert(0, str(BLENDER_HARNESS_ROOT))

from cli_anything.blender.core import preview as preview_mod
from cli_anything.blender.core.animation import add_keyframe, set_current_frame, set_frame_range, set_fps
from cli_anything.blender.core.lighting import add_camera, add_light
from cli_anything.blender.core.materials import assign_material, create_material, set_material_property
from cli_anything.blender.core.modifiers import add_modifier
from cli_anything.blender.core.objects import add_object
from cli_anything.blender.core.render import set_render_settings, generate_bpy_script
from cli_anything.blender.core.scene import create_scene, save_scene
from cli_anything.blender.core.session import Session
from cli_anything.blender.utils import blender_backend


def _object_index(project: Dict, name: str) -> int:
    for index, obj in enumerate(project.get("objects", [])):
        if obj.get("name") == name:
            return index
    raise KeyError(f"Object not found: {name}")


def _material_index(project: Dict, name: str) -> int:
    for index, material in enumerate(project.get("materials", [])):
        if material.get("name") == name:
            return index
    raise KeyError(f"Material not found: {name}")


def _assign(project: Dict, material_name: str, object_name: str) -> None:
    try:
        object_index = _object_index(project, object_name)
    except KeyError:
        return
    assign_material(project, _material_index(project, material_name), object_index)


def _add_orbit_nodes(project: Dict, material_name: str) -> None:
    radius = 3.25
    for index in range(8):
        angle = math.tau * index / 8.0
        x = round(math.cos(angle) * radius, 4)
        y = round(math.sin(angle) * radius, 4)
        node_name = f"OrbitNode{index + 1:02d}"
        add_object(
            project,
            mesh_type="sphere",
            name=node_name,
            location=[x, y, 3.15],
            scale=[0.12, 0.12, 0.12],
            mesh_params={"radius": 1.0, "segments": 20, "rings": 12},
        )
        _assign(project, material_name, node_name)


def _build_blockout(project: Dict) -> None:
    add_object(project, mesh_type="plane", name="Ground", mesh_params={"size": 20.0}, location=[0, 0, 0])
    add_object(
        project,
        mesh_type="cylinder",
        name="BasePlinth",
        location=[0, 0, 0.42],
        mesh_params={"radius": 2.9, "depth": 0.84, "vertices": 48},
    )
    add_modifier(project, "bevel", _object_index(project, "BasePlinth"), params={"width": 0.08, "segments": 3})
    add_object(
        project,
        mesh_type="cylinder",
        name="InnerDais",
        location=[0, 0, 1.02],
        mesh_params={"radius": 1.95, "depth": 0.38, "vertices": 48},
    )
    add_modifier(project, "bevel", _object_index(project, "InnerDais"), params={"width": 0.04, "segments": 2})
    add_object(
        project,
        mesh_type="sphere",
        name="CoreSphere",
        location=[0, 0, 3.2],
        scale=[0.72, 0.72, 0.72],
        mesh_params={"radius": 1.0, "segments": 36, "rings": 18},
    )
    add_modifier(
        project,
        "subdivision_surface",
        _object_index(project, "CoreSphere"),
        params={"levels": 2, "render_levels": 3},
    )
    add_object(
        project,
        mesh_type="torus",
        name="RingA",
        location=[0, 0, 3.2],
        rotation=[90, 0, 0],
        mesh_params={"major_radius": 2.4, "minor_radius": 0.14, "major_segments": 64, "minor_segments": 18},
    )
    add_object(
        project,
        mesh_type="torus",
        name="RingB",
        location=[0, 0, 3.2],
        rotation=[0, 90, 0],
        mesh_params={"major_radius": 1.7, "minor_radius": 0.1, "major_segments": 64, "minor_segments": 18},
    )
    add_object(
        project,
        mesh_type="torus",
        name="RingC",
        location=[0, 0, 3.2],
        rotation=[45, 0, 45],
        mesh_params={"major_radius": 1.08, "minor_radius": 0.08, "major_segments": 56, "minor_segments": 16},
    )
    add_object(
        project,
        mesh_type="cylinder",
        name="Spindle",
        location=[0, 0, 3.2],
        mesh_params={"radius": 0.14, "depth": 4.6, "vertices": 28},
    )


def _build_supports(project: Dict) -> None:
    pylons = [
        ("PylonNorth", [0.0, 2.7, 2.0]),
        ("PylonSouth", [0.0, -2.7, 2.0]),
        ("PylonEast", [2.7, 0.0, 2.0]),
        ("PylonWest", [-2.7, 0.0, 2.0]),
    ]
    for name, location in pylons:
        add_object(
            project,
            mesh_type="cube",
            name=name,
            location=location,
            scale=[0.2, 0.2, 1.4],
        )
        add_modifier(project, "bevel", _object_index(project, name), params={"width": 0.035, "segments": 2})

    struts = [
        ("StrutNE", [1.75, 1.75, 2.55], [24, 0, 45]),
        ("StrutNW", [-1.75, 1.75, 2.55], [24, 0, -45]),
        ("StrutSE", [1.75, -1.75, 2.55], [-24, 0, 45]),
        ("StrutSW", [-1.75, -1.75, 2.55], [-24, 0, -45]),
    ]
    for name, location, rotation in struts:
        add_object(
            project,
            mesh_type="cylinder",
            name=name,
            location=location,
            rotation=rotation,
            mesh_params={"radius": 0.1, "depth": 2.25, "vertices": 18},
        )


def _build_details(project: Dict) -> None:
    add_object(
        project,
        mesh_type="cone",
        name="UpperCrown",
        location=[0, 0, 5.04],
        mesh_params={"radius1": 0.62, "radius2": 0.16, "depth": 0.75, "vertices": 36},
    )
    add_modifier(project, "bevel", _object_index(project, "UpperCrown"), params={"width": 0.02, "segments": 2})
    add_object(
        project,
        mesh_type="cone",
        name="LowerAnchor",
        location=[0, 0, 1.38],
        rotation=[180, 0, 0],
        mesh_params={"radius1": 0.56, "radius2": 0.16, "depth": 0.62, "vertices": 36},
    )
    add_modifier(project, "bevel", _object_index(project, "LowerAnchor"), params={"width": 0.02, "segments": 2})

    for index, rotation in enumerate([0, 45, 90, 135], start=1):
        name = f"FieldFin{index}"
        add_object(
            project,
            mesh_type="cube",
            name=name,
            location=[0, 0, 3.2],
            rotation=[0, 0, rotation],
            scale=[0.055, 1.4, 0.55],
        )
        add_modifier(project, "bevel", _object_index(project, name), params={"width": 0.015, "segments": 2})

    add_object(
        project,
        mesh_type="sphere",
        name="UpperEmitter",
        location=[0, 0, 4.35],
        scale=[0.18, 0.18, 0.18],
        mesh_params={"radius": 1.0, "segments": 24, "rings": 12},
    )
    add_object(
        project,
        mesh_type="sphere",
        name="LowerEmitter",
        location=[0, 0, 2.05],
        scale=[0.14, 0.14, 0.14],
        mesh_params={"radius": 1.0, "segments": 24, "rings": 12},
    )
    _add_orbit_nodes(project, "SignalWhite")


def _add_animation(project: Dict) -> None:
    set_frame_range(project, 1, 120)
    set_fps(project, 24)

    add_keyframe(project, _object_index(project, "RingA"), 1, "rotation", [90, 0, 0], interpolation="LINEAR")
    add_keyframe(project, _object_index(project, "RingA"), 120, "rotation", [90, 0, 360], interpolation="LINEAR")

    add_keyframe(project, _object_index(project, "RingB"), 1, "rotation", [0, 90, 0], interpolation="LINEAR")
    add_keyframe(project, _object_index(project, "RingB"), 120, "rotation", [360, 90, 0], interpolation="LINEAR")

    add_keyframe(project, _object_index(project, "RingC"), 1, "rotation", [45, 0, 45], interpolation="LINEAR")
    add_keyframe(project, _object_index(project, "RingC"), 120, "rotation", [45, 360, 405], interpolation="LINEAR")

    add_keyframe(project, _object_index(project, "CoreSphere"), 1, "scale", [0.72, 0.72, 0.72], interpolation="BEZIER")
    add_keyframe(project, _object_index(project, "CoreSphere"), 60, "scale", [0.84, 0.84, 0.84], interpolation="BEZIER")
    add_keyframe(project, _object_index(project, "CoreSphere"), 120, "scale", [0.72, 0.72, 0.72], interpolation="BEZIER")

    set_current_frame(project, 60)


def _add_materials(project: Dict) -> None:
    create_material(project, name="FoundationStone", color=[0.16, 0.18, 0.22, 1.0], metallic=0.0, roughness=0.92)
    create_material(project, name="ObsidianMetal", color=[0.06, 0.07, 0.1, 1.0], metallic=0.35, roughness=0.18)
    create_material(project, name="BrushedBrass", color=[0.78, 0.63, 0.28, 1.0], metallic=0.92, roughness=0.24)
    create_material(project, name="AzureCore", color=[0.2, 0.78, 1.0, 1.0], metallic=0.0, roughness=0.08)
    set_material_property(project, _material_index(project, "AzureCore"), "emission_color", [0.2, 0.78, 1.0, 1.0])
    set_material_property(project, _material_index(project, "AzureCore"), "emission_strength", 4.8)
    create_material(project, name="SignalWhite", color=[0.94, 0.96, 1.0, 1.0], metallic=0.0, roughness=0.15)
    set_material_property(project, _material_index(project, "SignalWhite"), "emission_color", [0.94, 0.96, 1.0, 1.0])
    set_material_property(project, _material_index(project, "SignalWhite"), "emission_strength", 1.35)


def _assign_materials(project: Dict) -> None:
    for object_name in ("Ground",):
        _assign(project, "FoundationStone", object_name)
    for object_name in ("BasePlinth", "InnerDais", "UpperCrown", "LowerAnchor"):
        _assign(project, "ObsidianMetal", object_name)
    for object_name in (
        "RingA",
        "RingB",
        "RingC",
        "Spindle",
        "PylonNorth",
        "PylonSouth",
        "PylonEast",
        "PylonWest",
        "StrutNE",
        "StrutNW",
        "StrutSE",
        "StrutSW",
        "FieldFin1",
        "FieldFin2",
        "FieldFin3",
        "FieldFin4",
    ):
        _assign(project, "BrushedBrass", object_name)
    for object_name in ("CoreSphere", "UpperEmitter", "LowerEmitter"):
        _assign(project, "AzureCore", object_name)


def _configure_scene(project: Dict) -> None:
    project["world"]["background_color"] = [0.025, 0.03, 0.045]
    set_render_settings(project, preset="eevee_preview")
    add_camera(
        project,
        name="HeroCam",
        location=[8.6, -8.4, 6.2],
        rotation=[62, 0, 46],
        focal_length=62,
        set_active=True,
    )
    hero_camera = project["cameras"][-1]
    hero_camera["dof_enabled"] = True
    hero_camera["dof_focus_distance"] = 8.7
    hero_camera["dof_aperture"] = 2.2

    add_light(project, light_type="SUN", name="SunKey", rotation=[-38, 0, 26], power=2.6)
    add_light(project, light_type="AREA", name="SideFill", location=[-5.5, 4.0, 4.2], rotation=[62, 0, -32], power=1250)
    add_light(project, light_type="POINT", name="CoreBounce", location=[0, 0, 3.2], power=180)


def _write_build_manifest(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _capture_stage(
    session: Session,
    stage_name: str,
    stage_log: List[Dict],
    preview_root: Path,
    started: bool,
) -> bool:
    if not started:
        live_payload = preview_mod.live_start(
            session,
            recipe="quick",
            root_dir=str(preview_root),
            force=True,
            refresh_hint_ms=1000,
            live_mode="manual",
            publish_reason=f"stage:{stage_name}",
            command=f"blender_gyro_observatory_demo.py --stage {stage_name}",
        )
    else:
        live_payload = preview_mod.live_push(
            session,
            recipe="quick",
            root_dir=str(preview_root),
            force=True,
            refresh_hint_ms=1000,
            publish_reason=f"stage:{stage_name}",
            command=f"blender_gyro_observatory_demo.py --stage {stage_name}",
        )
    stage_log.append(
        {
            "stage": stage_name,
            "bundle_id": live_payload.get("current_bundle_id"),
            "bundle_count": live_payload.get("bundle_count"),
            "session_path": live_payload.get("_session_path"),
            "current_manifest_path": live_payload.get("current_manifest_path"),
            "current_bundle_dir": live_payload.get("current_bundle_dir"),
        }
    )
    return True


def build_demo(output_dir: Path, use_live_preview: bool = True) -> Dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_root = output_dir / "live-root"
    project_path = output_dir / "gyro_observatory.blend-cli.json"
    manifest_path = output_dir / "build_manifest.json"
    final_render_path = output_dir / "renders" / "gyro_observatory_final.png"

    project = create_scene(name="gyro-observatory", profile="preview")
    _configure_scene(project)
    _add_materials(project)

    session = Session()
    stage_log: List[Dict] = []
    live_started = False

    _build_blockout(project)
    save_scene(project, str(project_path))
    session.set_project(project, str(project_path))
    if use_live_preview:
        live_started = _capture_stage(session, "01_blockout", stage_log, preview_root, live_started)

    _build_supports(project)
    _assign_materials(project)
    save_scene(project, str(project_path))
    if use_live_preview:
        live_started = _capture_stage(session, "02_supports", stage_log, preview_root, live_started)

    _build_details(project)
    _assign_materials(project)
    save_scene(project, str(project_path))
    if use_live_preview:
        live_started = _capture_stage(session, "03_details", stage_log, preview_root, live_started)

    _add_animation(project)
    save_scene(project, str(project_path))
    if use_live_preview:
        live_started = _capture_stage(session, "04_animation", stage_log, preview_root, live_started)
        live_payload = preview_mod.live_stop(session, recipe="quick", root_dir=str(preview_root))
    else:
        live_payload = None

    set_render_settings(project, preset="eevee_high", resolution_x=1600, resolution_y=1600, samples=128)
    set_current_frame(project, 60)
    save_scene(project, str(project_path))
    render_script = generate_bpy_script(project, str(final_render_path), frame=60, animation=False)
    final_render = blender_backend.render_scene_headless(render_script, str(final_render_path), timeout=480)

    payload = {
        "project_path": str(project_path),
        "preview_root": str(preview_root),
        "stage_log": stage_log,
        "live_session": live_payload,
        "final_render": final_render,
    }
    _write_build_manifest(manifest_path, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=f"/root/preview-artifacts/20260422/blender-gyro-observatory",
        help="Directory for the generated scene, preview bundles, and final render.",
    )
    parser.add_argument(
        "--no-live-preview",
        action="store_true",
        help="Skip stage-by-stage preview bundle capture.",
    )
    args = parser.parse_args()

    result = build_demo(Path(args.output_dir).expanduser().resolve(), use_live_preview=not args.no_live_preview)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
