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
    global vkapi, user_alias, settings
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
    print(f"Settings were loaded successfuly.\nAuthorized as {user_alias}.")


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
    global vkapi, user_alias, settings

    photo_ids, video_ids = [], []
    plda = kwargs.get("plda") or settings.get("DEST_PALBUM")

    vlda = kwargs.get("vlda") or settings.get("DEST_VALBUM")
    if kwargs.get('album'):
        print("Loading resources from album[s]...")
        albums = list(map(lambda x: x.replace('g', '-'), kwargs.get('album')))
        photo_ids.extend(internal.load_from_albums(vkapi, albums))
        print("Album resources were loaded successfuly.")
    
    # move all urls from file[s] to kwargs['url']
    if kwargs.get('urlfile'):
        print("Gettings urls from 'urlfile'")
        for file_ in kwargs.get('urlfile'):
            with open(file_, 'r') as f:
                kwargs.get('url').extend(f.readlines())

    if kwargs.get('url'):
        #TODO add url validation???
        print("Loading resources from url[s]...")
        assert plda and vlda, "photo and video loading albums must be set, before uploading to vk"
        ret = internal.load_from_urls(vkapi, kwargs.get('url'), plda, vlda)
        photo_ids.extend(ret["photo"])
        video_ids.extend(ret["video"])
        print("Resources were loaded successfuly.")

    if kwargs.get("update"):
        open_mode = 'w'
    else:
        open_mode = 'a'

    print("Storing resources...")
    # write gained ids to resource files
    with open(f"{cfg.PHOTO_DIR}/{user_alias}.vklib", mode=open_mode) as fphoto_res, \
        open(f"{cfg.VIDEO_DIR}/{user_alias}.vklib", mode=open_mode) as fvideo_res:
        fphoto_res.writelines(photo_ids)
        fvideo_res.writelines(video_ids)
    print("All resources were stored successfuly.")


@ShellFs.func
@ShellFs.argument("--alias", "-a", dest="alias", required=True,
    help="Alias for the new template")
@ShellFs.argument("--owrite", "-ow", dest="owrite", action="store_true",
    help="If alias was already defined overwrites it")
@ShellFs.argument("--cntPhotos", "--nphotos", "-np", dest="nPhotos", type=int,
    help="Number of photos to be added to each post.")
@ShellFs.argument("--cntVideos", "--nvideos", "-nv", dest="nVideos", type=int,
    help="Number of videos to be added to each post.")
@ShellFs.argument("--pattern", nargs='+', metavar="(p|v|pv|vp)*", default=[],
    help="\
    Before each post will be postponed he will load resources, that he has stored, according to some pattern. \
To n-th post will be applied (n %% <patterns_cnt>)-th pattern.\
Available pattern options :\n\
    'p' - adds photo resource[s] to post.\n\
    'v' - adds video resources[s] to post.\n\
Options can form a sequence so all those, that are in will be used.\
No resource can be used more than once in each sequence. Amount of resource that will be added specified by corresponding (cnt|n)(resource_name) flag\n")
def vk_postdef(**kwargs):
    global user_alias, settings

    #if alias is already defined
    if kwargs['alias'] in settings['POST_TEMPLATES'] and not kwargs.get('owrite'):
        print("Current alias is already in use. If you wanted to overwrite this alias, run this instruction with -ow flag")
        kwargs['alias'] = input("Enter new alias for the template or '--' to stop procedure : ")
        if kwargs['alias'] == '--':
            return
    
    post_template = cfg.POST_TEMPLATE.copy()
    nPhotos = kwargs.get('nPhotos')
    nVideos = kwargs.get('nVideos')
    if  not (nPhotos or nVideos):
        # initiate input sequence
        nPhotos = input("Enter number of photos for each post:\n\t")
        nVideos = input("Enter number of videos for each post:\n\t")
    
    if not (nPhotos or nVideos):
        raise ValueError("One of resource parameters[photo or video] must be > 0")

    post_template.update({'PHOTO_CNT' : nPhotos, 'VIDEO_CNT' : nVideos})
    
    # check whether given pattern is valid according to given PHOTOS_CNT and VIDEO_CNT
    pattern = kwargs.get('pattern')
    pattern_token_list = ['p', 'v']
    # check if pattern wasn't specified, if it wasn't generate one regarding PHOTOS_CNT and VIDEO_CNT
    if pattern == []:
        pattern.append('')
        if nPhotos: pattern[0] += 'p'
        if nVideos: pattern[0] += 'v'
    else:
        # check if all tokens are valid and used only once in each sequence
        prohibit_tokens = {} # dict of prohibit tokens, where token is the key and the value is reason str
        if not nPhotos: prohibit_tokens.update({'p' : "Cannot specifiy 'p' option when no photo resource is used"})
        if not nVideos: prohibit_tokens.update({'v' : "Cannot specifiy 'v' option when no video resource is used"})

        for sequence in pattern:
            for token in sequence:
                if token not in pattern_token_list:
                    raise ValueError(f"Invalid token {token}.")
                elif sequence.count(token) > 1:
                    raise ValueError(f"Option '{token}' is used more then once")
                elif token in prohibit_tokens:
                    raise ValueError(prohibit_tokens[token])

    post_template.update({'PATTERN' : pattern})

    settings['POST_TEMPLATES'].update({kwargs['alias'] : post_template})
    cfg.save_user_cfg(user_alias, settings)


@ShellFs.func
@ShellFs.argument("-hm", nargs='+', default=["00:00"], metavar="HH:MM",
    help="Option specifies hour-minute pairs for posts.")
@ShellFs.argument("-d", type=int,
    help="Option specifies day, from what do posts, of for a month.")
@ShellFs.argument("-m", type=int,
    help="Options specifies month, from what do posts, of the year.")
@ShellFs.argument("--nDays", "-nd", dest="ndays", required=True, type=int,
    help="Number of days to post.")
@ShellFs.argument("--group", "-g", dest="group", required=True, # for this time it's only for groups
    help="Id(positive) or alias of the destonation group.")
def vk_postpone(template_alias, **kwargs):
    global settings, user_alias, vkapi
    if template_alias not in settings['POST_TEMPLATES']:
        raise ValueError(f"No {template_alias} template alias defined")

    time_list = internal.form_time_list(kwargs.get('hm'), kwargs.get('d'), kwargs.get('m'), kwargs.get('ndays'))
    template = settings['POST_TEMPLATES'][template_alias]
    # load resources
    with open(f"{cfg.PHOTO_DIR}/{user_alias}.vklib", 'r') as fpr, \
        open(f"{cfg.VIDEO_DIR}/{user_alias}.vklib", 'r') as fvr:
        photo_res = fpr.readlines() #TODO define behavior when out of resource but pattern requiers it
        photo_res_len = len(photo_res)

        video_res = fvr.readlines()
        video_res_len = len(video_res)

    if kwargs.get('group') in settings['GROUPS_ALIAS']:
        owner_id = settings['GROUPS_ALIAS'][kwargs.get('group')]
    else:
        owner_id = -int(kwargs.get('group'))
    pattern_list = template['PATTERN'].copy()
    photo_cnt = template['PHOTO_CNT']
    video_cnt = template['VIDEO_CNT']
    
    for i in range(len(time_list)):
        post_time = time_list[i]
        pattern = pattern_list[i % len(pattern_list)]

        attachments = []
        if 'p' in pattern and settings['PHOTO_P'] < photo_res_len - photo_cnt:
            for i in range(photo_cnt):
                attachments.append(f"photo{photo_res[settings['PHOTO_P']].rstrip()}")
                settings['PHOTO_P'] += 1

        if 'v' in pattern and settings['VIDEO_P'] < video_res_len - video_cnt:
            for i in range(video_cnt):
                attachments.append(f"video{video_res[settings['VIDEO_P']].rstrip()}")
                settings['VIDEO_P'] += 1

        vkapi.wall.post(owner_id=owner_id, from_group=True, attachments=','.join(attachments), publish_date=post_time)

    cfg.save_user_cfg(user_alias, settings)


@ShellFs.func
def vk_set_plda(album):
    global settings, user_alias
    settings.update({"DEST_PALBUM" : album.replace('g', '-')})
    cfg.save_user_cfg(user_alias, settings)


@ShellFs.func
def vk_set_vlda(album):
    global settings, user_alias
    settings.update({"DEST_VALBUM" : album.replace('g', '-')})
    cfg.save_user_cfg(user_alias, settings)

@ShellFs.func
def vk_set_group_alias(group, alias):
    global settings, user_alias
    settings['GROUPS_ALIAS'].update({ alias : -int(group) })
    cfg.save_user_cfg(user_alias, settings)