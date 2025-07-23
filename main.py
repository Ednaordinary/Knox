import os
import io
import zipfile
import requests
import traceback
import threading
import time
import cadquery as cq
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from dotenv import load_dotenv

import re

from usps import get_price
from printer import Printer
from counter import Counter
from slicer import Slicer
import visual

load_dotenv()

IP = os.environ.get("BAMBU_IP")
SERIAL = os.environ.get("BAMBU_SN")
ACCESS_CODE = os.environ.get("BAMBU_ACCESS")
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
APP_TOKEN = os.environ.get("APP_TOKEN")

app = AsyncApp(token=SLACK_TOKEN)
printer = Printer(IP, ACCESS_CODE, SERIAL)
print_counter = Counter("count.bin")
slicer = Slicer()
loop = None

@app.event("message")
async def handle_message_events(ack, body, logger):
    await ack()
    print(body)
    if 'event' in body and 'user' in body['event'] and body['event']['user'] != os.environ.get("OWNER"):
        return
    if 'event' in body and 'text' in body['event']:
        cmd = body['event']['text']
        stack = []
        if "print camera" in cmd:
            stack.append(cam(body))
        if "print home" in cmd:
            stack.append(home(body))
            stack.append(cam(body))
        if "print rem" in cmd:
            stack.append(rem(body))
            stack.append(cam(body))
        if "print stop" in cmd or "print off" in cmd:
            stack.append(off(body))
        if "cmd" in cmd:
            stack.append(gcode(body))
            stack.append(cam(body))
        if "print price " in cmd:
            await price(body)
        if "print slice" in cmd:
            await print_slice(body)
        if "print flow" in cmd:
            await print_slice(body, flow=True)
        if len(stack) > 0:
            printer.alloc()
            for i in stack:
                await i
            printer.dealloc()

def create_zip_archive_in_memory(
        text_content: str,
        text_file_name: str = 'file.txt'):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(text_file_name, text_content)
    zip_buffer.seek(0)
    return zip_buffer

def thread_ts_func(body):
    return body['event']['thread_ts'] if 'thread_ts' in body['event'] else body['event']['ts']

async def get_message(channel, ts):
    result = await app.client.conversations_history(
        channel=channel,
        inclusive=True,
        oldest=ts,
        limit=1,
    )
    return result["messages"][0]

def is_valid_gcode(line: str):
    # Remove whitespace and comments
    line = line.split(";")[0].strip()

    # Check if line is empty or starts with a valid G-code command (G or M)
    if not line or not re.match(r"^[GM]\d+", line):
        print("does not start with G or M")
        return False

    # Check for proper parameter formatting
    tokens = line.split()
    for token in tokens[1:]:
        if not re.match(r"^[A-Z]-?\d+(\.\d+)?$", token):
            print("token does not match:", token)
            return False

    return True

def check_gcode(gcode):
    for idx, line in enumerate(gcode.split("\n")):
        if line.split(";")[0].strip() == "":
            continue
        if not is_valid_gcode(line):
            return (False, idx)
    return (True, 0)

async def price(body):
    thread_ts = thread_ts_func(body)
    args = body['event']['text'].split(" ")
    args = [x.strip() for x in args if (x.strip() != "price" and x.strip() != "print")]
    try:
        int(args[0]) # validate its a number, but keep leading zeros
        zip_code = args[0]
        if len(args) >= 2:
            weight = float(args[1]) / 16
        else:
            weight = 3.0 / 16
    except:
        await app.client.chat_postMessage(channel=body['event']['channel'], text="failed to parse! birds cant read", thread_ts=thread_ts)
        print(traceback.format_exc())
        return
    try:
        price = get_price(zip_code, weight)
    except:
        await app.client.chat_postMessage(channel=body['event']['channel'], text="a drone hit me and i died", thread_ts=thread_ts)
        print(traceback.format_exc())
        return
    if price is None:
        price = "death"
    await app.client.chat_postMessage(channel=body['event']['channel'], text="price: $" + str(price), thread_ts=thread_ts)

def visual_runner(gcode_path):
    save, _ = os.path.splitext(gcode_path)
    save = save + ".mp4"
    visual.visualize(gcode_path, save)
    return save
    
def visual_thread(gcode_path, body):
    save = visual_runner(gcode_path)
    thread_ts = thread_ts_func(body)
    with open(save, "rb") as video:
        asyncio.run_coroutine_threadsafe(
            app.client.files_upload_v2(channel=body['event']['channel'], thread_ts=thread_ts, file=video),
            loop,
        ).result() # dont close file reader while reading

async def print_slice(body, flow=None):
    thread_ts = thread_ts_func(body)
    print_counter.inc()
    print_id = print_counter.get()
    if 'thread_ts' in body['event']:
        message = await get_message(body['event']['channel'], body['event']['thread_ts'])
    else:
        message = body['event']
    if 'files' not in message:
        await app.client.chat_postMessage(channel=body['event']['channel'], text="nothing to slice !!", thread_ts=thread_ts)
        return
    headers = {
        "Authorization": "Bearer " + SLACK_TOKEN
    }
    files = []
    prefix = "prints/" + str(print_id)
    export_path = prefix + "/export"
    os.makedirs(export_path, exist_ok=True)
    for idx, file in enumerate(message['files']):
        if file['title'].lower().endswith('.stl'):
            with requests.get(file['url_private'], headers=headers) as content:
                save_path = prefix + "/" + str(idx) + ".stl"
                with open(path, 'wb') as disk_file:
                    disk_file.write(content.content)
                files.append(save_path)
        elif file['title'].lower().endswith('.step'):
            with requests.get(file['url_private'], headers=headers) as content:
                save_path = prefix + "/" + str(idx) + ".step"
                with open(save_path, 'wb') as disk_file:
                    disk_file.write(content.content)
                try:
                    step = cq.importers.importStep(save_path)
                    save_path = prefix + "/" + str(idx) + ".stl"
                    cq.exporters.export(step, save_path)
                except:
                    print(traceback.format_exc())
                    await app.client.chat_postMessage(channel=body['event']['channel'], text="failed to steal step file" + file['name'], thread_ts=thread_ts)
                else:
                    files.append(save_path)
    validate = [prefix + "/" + x for x in os.listdir(prefix) if x.endswith(".stl")]
    for file in files:
        if file not in validate:
            name = message['files'][int(file.split("/")[-1][:-4])]['name']
            await app.client.chat_postMessage(channel=body['event']['channel'], text="could not convert step: " + name, thread_ts=thread_ts)
    split = []
    for i in validate:
        try:
            print(validate)
            name = message['files'][int(i.split("/")[-1][:-4])]['name']
            mesh = trimesh.load(i)
            #mesh.show()
            split_mesh = mesh.split(only_watertight = False)
            split_mesh = [m for m in split_mesh if m.faces.shape[0] > 4] # this is the minimum amount of points for a  3D object
            #split_mesh[0].show()
            print(split_mesh)
            if len(split_mesh) > 1:
                original_path, _ = os.path.splitext(i)
                not_okay = 0
                for idx, n in enumerate(split_mesh):
                    if not n.is_watertight:
                        not_okay += 1
                    save_path = original_path + "-" + str(idx) + ".stl"
                    n.export(save_path)
                    split.append(save_path)
                if not_okay > 0:
                    await app.client.chat_postMessage(channel=body['event']['channel'], text=("an object in " if not_okay == 1 else str(not_okay) + " objects in ") + name + (" is" if not_okay == 1 else " are") + " not manifold and may not print right", thread_ts=thread_ts)
            else:
                if not mesh.is_watertight:
                    await app.client.chat_postMessage(channel=body['event']['channel'], text=name + " is not manifold and may not print right", thread_ts=thread_ts)
                split.append(i)
        except:
            print(traceback.format_exc())
            await app.client.chat_postMessage(channel=body['event']['channel'], text=("part of " if len(validate) > 1 else "") + "the print blew up", thread_ts=thread_ts)
            return
    slicer.slice(split, export_path)
    gcode = [export_path + "/" + x for x in os.listdir(export_path) if x.endswith(".gcode")]
    plates = []
    for g in gcode:
        filament, time = slicer.get_grams(g)
        plates.append((filament, time))
    if len(plates) == 0:
        plates_response = "i dropped the print"
    elif len(plates) == 1:
        plates_response = plates[0][1] + ", *" + str(round(plates[0][0], 2)) + "g*"
    else:
        plates_response = "\n".join([f"Plate {str(idx)}: {x[1]} ({round(x[0], 2)}g)" for idx, x in enumerate(plates)])
        plates_response += "\nTotal: *" + str(round(sum([x[0] for x in plates]), 2)) + "g*"
    await app.client.chat_postMessage(channel=body['event']['channel'], text=plates_response, thread_ts=thread_ts)
    if flow and len(plates) != 0:
        for gcode_path in gcode:
            threading.Thread(target=visual_thread, args=[gcode_path, body]).start()
        args = body['event']['text'].split(" ")
        args = [x.strip() for x in args if (x.strip() != "print" and x.strip() != "flow")]
        try:
            int(args[0]) # validate its a number, but keep leading zeros
            zip_code = args[0]
            weight = sum([x[0] for x in plates]) / 28.35 # grams -> ounces
            weight = weight / 16 # ounces -> pounds
        except:
            await app.client.chat_postMessage(channel=body['event']['channel'], text="failed to parse! birds cant read", thread_ts=thread_ts)
            print(traceback.format_exc())
            return
        try:
            price = get_price(zip_code, weight)
        except:
            await app.client.chat_postMessage(channel=body['event']['channel'], text="a drone hit me and i died", thread_ts=thread_ts)
            print(traceback.format_exc())
            return
        if price is None:
            price = "death"
        await app.client.chat_postMessage(channel=body['event']['channel'], text="price: $" + str(price), thread_ts=thread_ts)

async def home(body):
    thread_ts = thread_ts_func(body)
    #await app.client.chat_postMessage(channel=body['event']['channel'], text="homing printer..", thread_ts=thread_ts)
    printer.home()
    await app.client.chat_postMessage(channel=body['event']['channel'], text="printer homed", thread_ts=thread_ts)

async def cam(body):
    # very often will not work because of fast allocation
    try:
        image = printer.get_camera_image()
    except:
        return
    else:
        file = io.BytesIO()
        image.save(file, format='PNG')
        file.seek(0)
        file = file.read()
        thread_ts = thread_ts_func(body)
        #await app.client.chat_postMessage(channel=body['event']['channel'], text=":<", thread_ts=thread_ts)
        await app.client.files_upload_v2(channel=body['event']['channel'], thread_ts=thread_ts, file=file)

async def rem(body):
    thread_ts = thread_ts_func(body)
    with open("rem.gcode", "r") as file:
        gcode = file.read()
    valid = check_gcode(gcode)
    if not valid[0]:
        await app.client.chat_postMessage(channel=body['event']['channel'], text="gcode error on line " + str(valid[1]), thread_ts=thread_ts)
        return
    cmds = [x for x in gcode.split("\n") if x.split(";")[0].strip() != ""]
    for idx, line in enumerate(cmds):
        printer.gcode(line)
    await app.client.chat_postMessage(channel=body['event']['channel'], text="removed print from bed", thread_ts=thread_ts)
        
async def gcode(body):
    cmds = body['event']['text'].split("\n")
    thread_ts = thread_ts_func(body)
    for cmd in cmds:
        gcode = cmd.replace("cmd", "").strip()
        try:
            printer.gcode(gcode)
        except:
            await app.client.chat_postMessage(channel=body['event']['channel'], text="failed to run gcode!", thread_ts=thread_ts)

async def off(body):
    thread_ts = thread_ts_func(body)
    printer.gcode("M18 X Y Z", gcode_check=False)
    await app.client.chat_postMessage(channel=body['event']['channel'], text="printer stopped", thread_ts=thread_ts)

async def main():
    global loop
    loop = asyncio.get_running_loop()
    handler = AsyncSocketModeHandler(app, APP_TOKEN)
    await handler.start_async()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
