import subprocess

class Slicer:
    def __init__(self):
        pass
    def get_grams(self, path):
        with open(path, "r") as gcode_file:
            gcode = gcode_file.readlines()
        line = None
        match_string = "; filament used [cm3] ="
        for i in gcode:
            if match_string in i:
                line = i
                break
        filament = float(line[len(match_string):]) * 1.26 # generic g/cm3
        return filament
    def slice(self, paths, out):
        # yes this is gross
        # doing it anyways
        subprocess.run("OrcaSlicer.AppImage --load-settings \"orca-input/a1.json;orca-input/standard.json\" --load-filaments \"orca-input/pla.json\" -arrange 2 --orient 2 --slice 0 --outputdir " + str(out) + " --slice 0 " + " ".join(paths), shell=True)
