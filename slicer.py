import os
import subprocess

class Slicer:
    def __init__(self):
        pass
    def get_grams(self, path):
        with open(path, "r") as gcode_file:
            gcode = gcode_file.readlines()
        filament_line = None
        filament_match_string = "; filament used [cm3] ="
        time_line = None
        time_match_string = "total estimated time:"
        for i in gcode:
            if filament_match_string in i:
                filament_line = i
            if time_match_string in i:
                time_line = i
        filament = float(filament_line[len(filament_match_string):]) * 1.26 # generic g/cm3
        time = time_line.split(":")[2].strip()
        print(filament, time)
        return (filament, time)
    def slice(self, paths, out):
        # yes this is gross
        # doing it anyways
        subprocess.run("./OrcaSlicer.AppImage --load-settings \"orca-input/a1.json;orca-input/standard.json\" --load-filaments \"orca-input/pla.json\" -arrange 2 --orient 2 --slice 0 --outputdir " + str(out) + " --slice 0 " + " ".join(paths), shell=True, cwd=os.getcwd())
