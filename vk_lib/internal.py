import vk_api, vk_api.upload
import vk_lib.cfg as cfg
from urllib.parse import urlparse
import requests
import io

def load_from_album(vkapi, album):
    owner_id, album_id = album.split('_')
    count = 1000
    params = {
        "owner_id"  : owner_id,
        "album_id"  : album_id,
        "rev"       : 1,
        "offset"    : 0,
        "count"     : count,
    }
    vk_max_photos = 10000
    iters = vk_max_photos // count # basicaly iters = 10
    ids = []
    try:
        for i in range(iters):
            resp = vkapi.photos.get(**params)
            for photo_item in resp['items']:
                ids.append(f"{photo_item['owner_id']}_{photo_item['id']}\n")
            if resp['count'] < count:
                break
    except Exception as e:
        print(e)
    return ids


def load_from_albums(vkapi, albums):
    ids = []
    for album in albums:
        ids.extend(load_from_album(vkapi, album))
    return ids


def is_photo(name):
    photo_formats = ['jpg', 'png', 'gif', 'bmp']
    return name.split('.')[-1].lower() in photo_formats


def is_video(name):
    video_formats = ['avi', 'mp4', '3gp', 'mpeg', 'mov', 'flv', 'wmv']
    return name.split('.')[-1].lower() in video_formats


def load_from_url(vkapi, url, plda, vlda):
    def load_from_photo_url():
        group_id, album_id = plda.split('_')
        if group_id[0] != '-': group_id = None
        else: group_id = group_id[1:] # remove '-'

        resp = vk_upld.photo(io.BytesIO(requests.get(url).content), album_id, group_id=group_id)
        return [ "photo", f"{resp[0]['owner_id']}_{resp[0]['id']}\n" ]

    def load_from_video_url():
        group_id, album_id = vlda.split('_')
        if group_id[0] != '-': group_id = None
        else: group_id = group_id[1:]
        
        # resp = vk_upld.video(link=url, group_id=group_id, album_id=album_id)
        resp = vk_upld.video(video_file=io.BytesIO(requests.get(url).content), group_id=group_id, album_id=album_id)
        return [ "video", f"{resp['owner_id']}_{resp['video_id']}\n" ]

    name = urlparse(url).path.split('/')[-1]
    vk_upld = vk_api.upload.VkUpload(vkapi)
    if is_photo(name):
        return load_from_photo_url()
    elif is_video(name):
        return load_from_video_url()
    else:
        raise ValueError("Unkown file type %s" % name.split('.')[-1].upper())


def load_from_urls(vkapi, urls, plda, vlda):
    ids = {"photo" : [], "video" : []}
    try:
        for url in urls:
            ret = load_from_url(vkapi, url, plda, vlda)
            ids[ret[0]].append(ret[1])
    except Exception as e:
        print(e)

    return ids