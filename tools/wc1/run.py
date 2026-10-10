"""Run a war.exe build headless in DOSBox-X and take screenshots.

usage: python3 -m wc1.run <exe> [--at 10,20,30] [--name tag] [--keys ...]

Creates build/run/<tag>/ with C:\\WAR (the exe, DOS4GW.EXE, drivers, PATH.WAR
pointing at D:) and the CD ISO mounted as D:. Screenshots of the virtual X
display are written as build/run/<tag>/shot_<t>.png.
"""
import argparse
import os
import shutil
import subprocess

from . import path

CONF = """[sdl]
output=surface
[dosbox]
machine=svga_s3
memsize=16
[cpu]
core=normal
cycles={cycles}
[mixer]
nosound=true
[autoexec]
mount c c
imgmount d "{iso}" -t iso
c:
cd \\war
WAR.EXE
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--at", default="12,24")
    ap.add_argument("--name", default=None)
    ap.add_argument("--cycles", default="max")
    a = ap.parse_args()
    tag = a.name or os.path.splitext(os.path.basename(a.exe))[0]
    d = path("build", "run", tag)
    war = os.path.join(d, "c", "war")
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(war)
    shutil.copy(a.exe, os.path.join(war, "WAR.EXE"))
    shutil.copy(path("original", "install", "dos4gw.exe"), os.path.join(war, "DOS4GW.EXE"))
    shutil.copytree(path("original", "cd", "files", "DRIVERS"), os.path.join(war, "DRIVERS"))
    with open(os.path.join(war, "PATH.WAR"), "wb") as f:
        f.write(b"D:\0")
    with open(os.path.join(d, "dosbox.conf"), "w") as f:
        f.write(CONF.format(cycles=a.cycles, iso=path("original", "cd", "WAR1.iso")))
    times = [int(t) for t in a.at.split(",")]
    script = ["dosbox-x -conf dosbox.conf -fastlaunch -nogui -time-limit %d >dosbox.log 2>&1 &"
              % (times[-1] + 5)]
    prev = 0
    for t in times:
        script.append(f"sleep {t - prev}; import -window root shot_{t}.png")
        prev = t
    script.append("wait")
    subprocess.run(["xvfb-run", "-a", "-s", "-screen 0 1024x768x24", "bash", "-c",
                    "\n".join(script)], cwd=d, check=True)
    for t in times:
        print(os.path.join(d, f"shot_{t}.png"))


if __name__ == "__main__":
    main()
