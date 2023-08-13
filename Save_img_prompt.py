import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import colorama
from colorama import init, Fore, Back, Style
import os
import json
import time
import socket
import re
import folder_paths as comfy_paths

# by mpiquero
# comfyUI node to save an image and prompt and details

ALLOWED_PROMPT_EXT = ('.txt', '.json')
ALLOWED_IMG_EXT = ('.png', '.jpg', '.jpeg')

#Initialize colorama
colorama.init(autoreset=True)

#---------------------------------------------------------------------------------------------------------------------------------------------------#
# Credits                                                                                                                                           #
# WASasquatch                             https://github.com/WASasquatch/was-node-suite-comfyui    
# Originally from WAS Save Image Class
# Which was orginally from Comfui/node class
#---------------------------------------------------------------------------------------------------------------------------------------------------#

class TextTokens:
    def __init__(self):
                
        self.tokens =  {
            '[time]': str(time.time()).replace('.','_'),
            '[hostname]': socket.gethostname(),
        }

        if '.' in self.tokens['[time]']:
            self.tokens['[time]'] = self.tokens['[time]'].split('.')[0]

        try:
            self.tokens['[user]'] = ( os.getlogin() if os.getlogin() else 'null' )
        except Exception:
            self.tokens['[user]'] = 'null'
        
    def format_time(self, format_code):
        return time.strftime(format_code, time.localtime(time.time()))
        
    def parseTokens(self, text):
        tokens = self.tokens.copy()

        # Update time
        tokens['[time]'] = str(time.time())
        if '.' in tokens['[time]']:
            tokens['[time]'] = tokens['[time]'].split('.')[0]

        for token, value in tokens.items():
            if token.startswith('[time('):
                continue
            text = text.replace(token, value)

        def replace_custom_time(match):
            format_code = match.group(1)
            return self.format_time(format_code)

        text = re.sub(r'\[time\((.*?)\)\]', replace_custom_time, text)

        return text

# Originally from WAS Save API Class and Save Image Class smashed together what i needed

class Save_img_prompt:
    def __init__(self):
        self.output_dir = comfy_paths.output_directory
        self.type = os.path.basename(self.output_dir)

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "output_path": ("STRING", {"default": '[time(%Y-%m-%d)]', "multiline": False}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "filename_delimiter": ("STRING", {"default":"_"}),
                "filename_number_padding": ("INT", {"default":4, "min":1, "max":9, "step":1}),
                "filename_number_start": (["false", "true"],),
                "img_extension": (['png', 'jpeg'], ),
                "prompt_extension": (["txt", "json"], ),
                "quality": ("INT", {"default": 100, "min": 1, "max": 100, "step": 1}),
                "overwrite_mode": (["false", "prefix_as_filename"],),
                "show_history": (["false", "true"],),
                "show_history_by_prefix": (["true", "false"],),
                "embed_workflow": (["true", "false"],),
                "show_previews": (["true", "false"],),
                "save_prompt": (["true","false"],)
                },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"
            },
            }

    RETURN_TYPES = ()
    FUNCTION = "Save_img_prompt"
    OUTPUT_NODE = True

    CATEGORY = "IO"

    def Save_img_prompt(self, 
                        images,
                        unique_id,
                        output_path=None, 
                        filename_prefix="ComfyUI", 
                        filename_delimiter='_', 
                        filename_number_padding=4,
                        filename_number_start='false',
                        show_history='false', 
                        show_history_by_prefix="true", 
                        img_extension='png',
                        quality=100,
                        overwrite_mode='false',
                        show_previews="true",
                        prompt=None, 
                        extra_pnginfo=None, 
                        embed_workflow="true",
                        save_prompt="true",
                        prompt_extension="txt"):
        
        delimiter = filename_delimiter
        number_padding = filename_number_padding if filename_number_padding > 1 else 4

        # Define token system
        tokens = TextTokens()

        original_output = self.output_dir
        # Parse prefix tokens
        filename_prefix = tokens.parseTokens(filename_prefix)

        # Setup output path
        if output_path in [None, '', "none", "."]:
            output_path = self.output_dir
        else:
            output_path = tokens.parseTokens(output_path)

        if not os.path.isabs(output_path):
            output_path = os.path.join(self.output_dir, output_path)

        base_output = os.path.basename(output_path)
        if output_path.endswith("ComfyUI/output") or output_path.endswith("ComfyUI\output"):
            base_output = ""

        # Check output destination
        if output_path.strip() != '':
            if not os.path.exists(output_path.strip()):
                # print(Fore.GREEN + "+ Face detailer initialized" + Style.RESET_ALL)
                print(Fore.GREEN + "+ The path specified doesn\'t exist! Creating directory.")
                os.makedirs(output_path, exist_ok=True)

        # Find existing counter values
        if filename_number_start == 'true':
            pattern = f"(\\d{{{filename_number_padding}}}){re.escape(delimiter)}{re.escape(filename_prefix)}"
        else:
            pattern = f"{re.escape(filename_prefix)}{re.escape(delimiter)}(\\d{{{filename_number_padding}}})"
        existing_counters = [
            int(re.search(pattern, filename).group(1))
            for filename in os.listdir(output_path)
            if re.match(pattern, os.path.basename(filename))
        ]
        existing_counters.sort(reverse=True)

        # Set initial counter value
        if existing_counters:
            counter = existing_counters[0] + 1
        else:
            counter = 1

        # Set IMG Extension
        img_file_extension = '.' + img_extension
        if img_file_extension not in ALLOWED_IMG_EXT:
            print(Fore.RED + "+ The extension"+ {img_extension} + " is not valid. The valid formats are: " + {', '.join(sorted(ALLOWED_IMG_EXT))})
            img_file_extension = ".png"

        # Set PROMPT Extension
        prompt_file_extension = '.' + prompt_extension
        if prompt_file_extension not in ALLOWED_PROMPT_EXT:
            print(Fore.RED + "+ The extension"+ {prompt_extension} + " is not valid. The valid formats are: " + {', '.join(sorted(ALLOWED_PROMPT_EXT))})
            prompt_file_extension = ".txt"

        results = list()
        
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            metadata = PngInfo()
            if embed_workflow == 'true':
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                    prompt_json = "{ \"prompt\":" + json.dumps(prompt, indent=4)
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                        prompt_json = prompt_json + "," + json.dumps(extra_pnginfo, indent=4)
            else: 
                if save_prompt == "true":  
                    metadata.add_text("prompt", json.dumps(prompt))
                    prompt_json = "\"prompt\":" + json.dumps(prompt, indent=4)
            if overwrite_mode == 'prefix_as_filename':
                img_file = f"{filename_prefix}{img_file_extension}"
                prompt_file = f"{filename_prefix}{prompt_file_extension}"
            else:
                if filename_number_start == 'true':
                    img_file = f"{counter:0{number_padding}}{delimiter}{filename_prefix}{img_file_extension}"
                    prompt_file = f"{counter:0{number_padding}}{delimiter}{filename_prefix}{prompt_file_extension}"
                else:
                    img_file = f"{filename_prefix}{delimiter}{counter:0{number_padding}}{img_file_extension}"
                    prompt_file = f"{filename_prefix}{delimiter}{counter:0{number_padding}}{prompt_file_extension}"
                if os.path.exists(os.path.join(output_path, img_file)):
                    counter += 1
                if os.path.exists(os.path.join(output_path, prompt_file)):
                    counter += 1
            try:
                img_output_file = os.path.abspath(os.path.join(output_path, img_file))
                prompt_output_file = os.path.abspath(os.path.join(output_path, prompt_file))
                if img_extension == 'png':
                    img.save(img_output_file,
                             pnginfo=metadata, optimize=True)
                elif img_extension == 'jpeg':
                    img.save(img_output_file,
                             quality=quality, optimize=True)
                if save_prompt == "true":                 
                    with open(prompt_output_file, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(prompt_json)

                print(Fore.GREEN + f"+ File(s) saved to: {img_output_file}", end='')

                if show_history != 'true' and show_previews == 'true':
                    subfolder = self.get_subfolder_path(img_output_file, original_output)
                    results.append({
                        "filename": img_file,
                        "subfolder": subfolder,
                        "type": self.type
                    })

            except OSError as e:
                print(Fore.RED + " + Unable to save file to: ", end='')
                print({img_output_file})
                print(e)
            except Exception as e:
                print(Fore.RED + " + Unable to save file due to the to the following error: ", end='')
                print(e)
            if overwrite_mode == 'false':
                counter += 1

        filtered_paths = []
        if show_history == 'true' and show_previews == 'true':
            history_paths = None

            if history_paths:
            
                for image_path in history_paths:
                    image_subdir = self.get_subfolder_path(image_path, self.output_dir)
                    current_subdir = self.get_subfolder_path(img_output_file, self.output_dir)
                    if not os.path.exists(image_path):
                        continue
                    if show_history_by_prefix == 'true' and image_subdir != current_subdir:
                        continue
                    if show_history_by_prefix == 'true' and not os.path.basename(image_path).startswith(filename_prefix):
                        continue
                    filtered_paths.append(image_path)


                filtered_paths.reverse()

        if filtered_paths:
            for image_path in filtered_paths:
                subfolder = self.get_subfolder_path(image_path, self.output_dir)
                image_data = {
                    "filename": os.path.basename(image_path),
                    "subfolder": subfolder,
                    "type": self.type
                }
                results.append(image_data)

        if show_previews == 'true':
            return {"ui": {"images": results}}
        else:
            return {"ui": {"images": []}}
            

    def get_subfolder_path(self, image_path, output_path):
        output_parts = output_path.strip(os.sep).split(os.sep)
        image_parts = image_path.strip(os.sep).split(os.sep)
        common_parts = os.path.commonprefix([output_parts, image_parts])
        subfolder_parts = image_parts[len(common_parts):]
        subfolder_path = os.sep.join(subfolder_parts[:-1])
        return subfolder_path
    
    
NODE_CLASS_MAPPINGS = {
    "Save IMG Prompt": Save_img_prompt
}
