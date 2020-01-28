import requests
import os
from dotenv import load_dotenv
import random


VK_API_VERSION = '5.61'
VK_ENTRY_API_URL = 'https://api.vk.com/method/'
COMIC_URL_TEMPLATE = 'https://xkcd.com/{}/info.0.json'
CURRENT_COMIC_URL = 'https://xkcd.com/info.0.json'


def choose_random_image():
    response = requests.request('GET', CURRENT_COMIC_URL)
    comic = response.json()
    return random.randint(1, comic['num'])


def get_image_url_and_comment(image_num):
    comic_url = COMIC_URL_TEMPLATE.format(image_num)
    response = requests.request('GET', comic_url)
    comic = response.json()
    image_url = comic['img']
    image_comment = comic['alt']
    return image_url, image_comment


def download_random_comic():
    image_url, image_comment = get_image_url_and_comment(choose_random_image())
    response = requests.get(image_url)
    response.raise_for_status()
    filename = image_url[image_url.rfind("/")+1:]
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename, image_comment


def get_url_for_uploading_image(token):
    url = '{}{}'.format(VK_ENTRY_API_URL, "photos.getWallUploadServer")
    payload = {
        'v': VK_API_VERSION,
        'access_token': token,
    }
    response = requests.post(url, params=payload)
    response.raise_for_status()
    wall_upload_server = response.json()
    return wall_upload_server['response']['upload_url']


def upload_image(token):
    filename, image_comment = download_random_comic()
    with open(filename, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(get_url_for_uploading_image(token), files=files)
        response.raise_for_status()
        image_upload_result = response.json()
    os.remove(filename)
    return image_upload_result['server'], image_upload_result['photo'], image_upload_result['hash'], image_comment


def save_image_in_group_album(token):
    uploaded_image_server, uploaded_photo, uploaded_hash, image_comment = upload_image(token)
    url = '{}{}'.format(VK_ENTRY_API_URL, "photos.saveWallPhoto")
    payload = {
        'v': VK_API_VERSION,
        'access_token': token,
        'photo': uploaded_photo,
        'server': uploaded_image_server,
        'hash': uploaded_hash,
    }
    response = requests.post(url, params=payload)
    response.raise_for_status()
    saved_image_result = response.json()
    for image in saved_image_result['response']:
        return image['id'], image['owner_id'], image_comment


def publish_image(token, group_id):
    image_id, owner_id, image_comment = save_image_in_group_album(token)
    attachments = "photo{}_{}".format(owner_id, image_id)
    url = '{}{}'.format(VK_ENTRY_API_URL, "wall.post")
    payload = {
        'v': VK_API_VERSION,
        'access_token': token,
        'owner_id': group_id,
        'attachments': attachments,
        'message': image_comment,
    }
    response = requests.post(url, params=payload)
    response.raise_for_status()
    server_answer = response.json()
    print(server_answer)


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("ACCESS_TOKEN")
    group_id = os.getenv("GROUP_ID")
    publish_image(token, group_id)
