import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", ".."))
ADDON = os.path.abspath(os.path.join(SITE, "..", "Cats-Blender-Plugin-Blender-5x"))
BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
SKIP = (".git", "__pycache__", ".ruff_cache", "tests", "docs", "*.zip")


def crop(name, spec, out):
    raw, r = spec["raw"], spec["rect"]
    height = int(subprocess.check_output(["magick", "identify", "-format", "%h", raw]))
    geom = f"{r['w']}x{r['h']}+{r['x']}+{height - r['y'] - r['h']}"
    dest = os.path.join(out, f"{name}.png")
    subprocess.run(["magick", raw, "-crop", geom, "+repage", dest], check=True)
    if spec.get("trim"):
        box = subprocess.check_output(["magick", dest, "-fuzz", "2%", "-trim", "-format", "%@", "info:"], text=True)
        size, y = box.split("+")[0], int(box.split("+")[2])
        bottom = min(r["h"], y + int(size.split("x")[1]) + 24)
        subprocess.run(["magick", dest, "-crop", f"{r['w']}x{bottom}+0+0", "+repage", dest], check=True)
    print(f"  {name}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=os.path.join(SITE, "src", "assets", "screenshots"))
    args = ap.parse_args()

    root = tempfile.mkdtemp(prefix="cats-shots-")
    try:
        target = os.path.join(root, "extensions", "user_default", "cats_blender_plugin")
        shutil.copytree(ADDON, target, ignore=shutil.ignore_patterns(*SKIP))
        os.makedirs(args.out, exist_ok=True)
        env = dict(os.environ, BLENDER_USER_RESOURCES=root, CATS_MODEL=os.path.abspath(args.model),
                   CATS_ONLY=args.only, CATS_WORK=root)
        blank = os.path.join(root, "blank.blend")
        subprocess.run([BLENDER, "--background", "--factory-startup", "--python-expr",
                        "import bpy; p = bpy.context.preferences; p.view.show_splash = False; "
                        "p.system.use_online_access = False; p.view.ui_scale = 1.0; p.system.use_region_overlap = False; "
                        "bpy.ops.wm.save_userpref(); bpy.ops.wm.read_factory_settings(use_empty=True); "
                        f"bpy.ops.wm.save_as_mainfile(filepath={blank!r})"],
                       env=env, check=True, capture_output=True)
        proc = subprocess.run([BLENDER, "--window-geometry", "0", "0", "1600", "1000",
                               blank, "--python", os.path.join(HERE, "shoot.py")], env=env,
                              capture_output=True, text=True)
        log = [l for l in proc.stdout.splitlines() if l.startswith(("[shot]", "Traceback", "  File", "Error")) or "Error" in l]
        print("\n".join(log[-80:]))
        errors = [l for l in proc.stderr.splitlines() if l.strip()]
        if any("Traceback" in l for l in errors):
            print("\n".join(errors[-40:]))
        crops_file = os.path.join(root, "crops.json")
        if not os.path.exists(crops_file):
            print(proc.stdout[-4000:], proc.stderr[-4000:], sep="\n")
            return 1
        with open(crops_file) as fh:
            for name, spec in json.load(fh).items():
                crop(name, spec, args.out)
        faces = [os.path.join(args.out, f"face-{k}.png") for k in ("aa", "oh", "ch")]
        if all(os.path.exists(f) for f in faces):
            subprocess.run(["magick", *faces, "-resize", "50%", "+append", "+repage",
                            os.path.join(args.out, "visemes-faces.png")], check=True)
            for f in faces:
                os.remove(f)
            print("  visemes-faces.png")
        pair = [os.path.join(args.out, f"bones-{k}.png") for k in ("before", "after")]
        if all(os.path.exists(f) for f in pair):
            subprocess.run(["magick", "-background", "none", pair[0], "-size", "24x1", "xc:none", pair[1], "+append", "+repage",
                            os.path.join(args.out, "bones-compare.png")], check=True)
            print("  bones-compare.png")
        return proc.returncode
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
