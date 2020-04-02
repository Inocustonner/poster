import vk_api
import os, os.path
from ShellFs import ShellFs
import vk_lib.cfg as cfg
import vk_lib.internal as internal
vkapi       = None  # vkApiMethod for current user
user_alias  = ""    # alias for current user session
settings    = {}    # user settings

@ShellFs.func
def vk_me():
    print(vkapi.account.getProfileInfo())


@ShellFs.func
@ShellFs.argument("--login", 
    help="Email or phone number for vk authorization")
@ShellFs.argument("--pass",
    help="Password for vk authorization")
@ShellFs.argument("--token",
    help="Vk token or file containing vk token")
@ShellFs.argument("--alias", "-a", dest="alias",
    help="Load user with given alias")
@ShellFs.argument("--set_alias", "--sa", dest="set_alias",
    help="Creates specifed alias for the session") #TODO make it also capable of renaming
def vk_sess(**auth_kwargs):
    global vkapi
    global user_alias
    global settings
    # create session withou alias
    if not auth_kwargs.get('alias'):
        if auth_kwargs.get('login') and auth_kwargs.get('pass'):
            vkapi_sess = vk_api.VkApi(login=auth_kwargs['login'], password=auth_kwargs['pass'], api_version=cfg.VK_VER)
            vkapi_sess.auth()
        elif auth_kwargs.get('token'):
            tok = auth_kwargs['token']
            if os.path.isfile(tok):
                with open(tok, 'r') as f:
                    tok = f.read()

            vkapi_sess = vk_api.VkApi(token=tok, api_version=cfg.VK_VER)
            #no auth required with token
        else:
            raise ValueError("No satisfying logging arguments were given")

        # create alias for new user
        if not auth_kwargs.get('set_alias'):
            user_alias = input('Enter alias for the current user')
        else:
            user_alias = auth_kwargs['set_alias']

        settings = {}
        if tok:
            settings.update({"ACCESS_TOKEN" : cfg.encode_token(tok)})

        cfg.create_user_cfg(user_alias, **settings)
        vkapi = vkapi_sess.get_api()

    elif auth_kwargs.get('alias'):
        user_alias = auth_kwargs['alias']
        settings = cfg.load_user_cfg(user_alias)
        vkapi_sess = vk_api.VkApi(token=cfg.decode_token(settings["ACCESS_TOKEN"]), api_version=cfg.VK_VER)
        vkapi = vkapi_sess.get_api()

    else:
        raise ValueError("No satisfying logging arguments were given")


@ShellFs.func
@ShellFs.argument("--album", nargs='+', default=[],
    metavar="[g](0..9)+_(0..9)+",
    help="Album id from which load photos to resourses")
@ShellFs.argument("--plda", nargs=1,
    help="Album id to which upload photos")
@ShellFs.argument("--vlda", nargs=1,
    help="Album id to which upload photos")
@ShellFs.argument("--url", nargs='+', default=[],
    help="Url to source which need to be loaded to resourses")
@ShellFs.argument("--urlfile", nargs='+', default=[],
    help="Specifies file with url in each line, that will be loaded to resourses")
@ShellFs.argument("--update", '-u', action="store_true", default=False,
    help="Sets update flag, so previously loaded info will be cleared")
def vk_ldfrom(**kwargs):
    global vkapi
    global user_alias
    global settings

    photo_ids, video_ids = [], []
    plda = kwargs.get("plda") or settings.get("DEST_PALBUM")

    vlda = kwargs.get("vlda") or settings.get("DEST_VALBUM")
    if kwargs.get('album'):
        albums = list(map(lambda x: x.replace('g', '-'), kwargs.get('album')))
        photo_ids.extend(internal.load_from_albums(vkapi, albums))
    
    if kwargs.get('urlfile'):
        for file_ in kwargs.get('urlfile'):
            with open(file_, 'r') as f:
                kwargs.get('url').extend(f.readlines())

    if kwargs.get('url'):
        #TODO add url validation???
        assert plda, "photo loading album must be set, before loading photos to vk"
        ret = internal.load_from_urls(vkapi, kwargs.get('url'), plda, vlda)
        photo_ids.extend(ret["photo"])
        video_ids.extend(ret["video"])

    if kwargs.get("update"):
        open_mode = 'w'
    else:
        open_mode = 'a'

    # write gained ids to resource files
    with open(f"{cfg.PHOTO_DIR}/{user_alias}.vklib", mode=open_mode) as fphoto_res, \
        open(f"{cfg.VIDEO_DIR}/{user_alias}.vklib", mode=open_mode) as fvideo_res:
        fphoto_res.writelines(photo_ids)
        fvideo_res.writelines(video_ids)
    

@ShellFs.func
def vk_set_plda(album):
    global settings
    global user_alias
    settings.update({"DEST_PALBUM" : album.replace('g', '-')})
    cfg.save_user_cfg(user_alias, settings)


@ShellFs.func
def vk_set_vlda(album):
    global settings
    global user_alias
    settings.update({"DEST_VALBUM" : album.replace('g', '-')})
    cfg.save_user_cfg(user_alias, settings)