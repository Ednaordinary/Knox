This is a modified version of https://github.com/rtzam/gcody optimized for previews (This project is archived but works well enough)

It supports the following mechanisms versus the original (only for .animated), assuming you modify the code directly:

 - Rendering to a specific frame count

 - Rendering sparsely (not rendering every gcode path change)

 - Ignoring unimportable commands

 - Fixed importing of some commands

 - Downsampling gcode commands for faster render (this doesn't look great)

 - Rendering via LineCollection (theoretically faster)

 - Higher res video (does not increase render time significantly, default 300 dpi)

Tried, failed to add:

 - blitting (save_fig appears unable to save without rendering every object. super hard to work around)

Sample preview with defaults:

https://github.com/user-attachments/assets/53f0b07a-9894-4931-9e07-fe54fa01fd72

```py
import visual
visual.visualize("plate_1.gcode", "plate_1.mp4")
```
