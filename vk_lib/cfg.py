import os, os.path
import json
import base64

VK_VER = "5.103"

THIS_PATH       = os.path.abspath(os.path.dirname(__file__))
CFG_PATH        = f"{THIS_PATH}/cfg"
PHOTO_DIR       = f"{CFG_PATH}/photo"
VIDEO_DIR       = f"{CFG_PATH}/video"
USER_CFG        = f"{CFG_PATH}/users"

ALL_PATHS   = [ CFG_PATH, PHOTO_DIR, VIDEO_DIR, USER_CFG ]
PATHS       = [ PHOTO_DIR, VIDEO_DIR, USER_CFG ]
USER_SETTINGS_TEMPLATE = {
    "ACCESS_TOKEN"  : str(),    # must be encoded somehow
    "GROUPS_ALIAS"  : dict(),   # alias for a group id
    "DEST_PALBUM"   : str(),    # dest album_id for photo uploading
    "DEST_VALBUM"   : str(),    # dest album_id for video uploading
    "PHOTO_P"       : int(),    # current photo pointer
    "VIDEO_P"       : int(),    # current video pointer
}

def check_paths():
    for dir_path in ALL_PATHS:
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

check_paths()

def encode_token(token):
    return base64.encodebytes(token.encode('utf8')).decode('utf8')

def decode_token(token):
    return base64.decodebytes(token.encode('utf8')).decode('utf8')

def save_user_cfg(alias, cfg_dict):
    with open(f'{USER_CFG}/{alias}.vklib', 'w') as fsettings:
        json.dump(cfg_dict, fsettings, indent=4)

def create_user_cfg(alias, **kwargs):
    settings = USER_SETTINGS_TEMPLATE.copy()
    for key, value in kwargs.items():
        if (key in USER_SETTINGS_TEMPLATE):
            settings[key] = value
    
    # create resource file in ALL_PATHS directories
    for path in PATHS:
        open(f'{path}/{alias}.vklib', 'w').close()

    save_user_cfg(alias, settings)

def load_user_cfg(alias):
    with open(f'{USER_CFG}/{alias}.vklib', 'r') as fsettings:
        settings = USER_SETTINGS_TEMPLATE.copy()
        settings.update(json.load(fsettings))
        return settings