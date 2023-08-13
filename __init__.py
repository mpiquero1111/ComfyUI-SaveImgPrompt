#import shutil
import folder_paths
import os, sys, subprocess
# import filecmp


try:
  print("### Loading: Save img prompt")
  from .Save_img_prompt import NODE_CLASS_MAPPINGS
except:
  img_path = os.path.dirname(__file__)
  #requirements_path = os.path.join(img_path, "requirements.txt")
  #print("!! Installing requirements...")
  #subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_path])
  #print("!! Installing requirements finished...")
  from .Save_img_prompt import NODE_CLASS_MAPPINGS

comfy_path = os.path.dirname(folder_paths.__file__)

# def setup_js():     
   #js_dest_path = os.path.join(comfy_path, "web", "extensions", "txtinfo")
   #js_src_path = os.path.join(webp_path, "txtinfo", "txtinfo.js")
     
   ## Creating folder if it's not present, then Copy. 
   #print("Copying JS files for Workflow loading")
   #if (os.path.isdir(js_dest_path)==False):
    # os.mkdir(js_dest_path)
    # shutil.copy(js_src_path, js_dest_path)
  # else:
    # shutil.copy(js_src_path, js_dest_path)                  


__all__ = ['NODE_CLASS_MAPPINGS']