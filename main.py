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
    response.raise_for_status()
    comic = response.json()
    return random.randint(1, comic['num'])


def get_image_url(image_num):
    comic_url = COMIC_URL_TEMPLATE.format(image_num)
    response = requests.request('GET', comic_url)
    response.raise_for_status()
    comic = response.json()
    image_url = comic['img']
    return image_url


def get_image_comment(image_num):
    comic_url = COMIC_URL_TEMPLATE.format(image_num)
    response = requests.request('GET', comic_url)
    response.raise_for_status()
    comic = response.json()
    image_comment = comic['alt']
    return image_comment


def download_random_comic(image_url):
    response = requests.get(image_url)
    response.raise_for_status()
    filename = image_url[image_url.rfind("/")+1:]
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def get_url_for_uploading_image(token):
    url = '{}{}'.format(VK_ENTRY_API_URL, "photos.getWallUploadServer")
    payload = {
        'v': VK_API_VERSION,
        'access_token': token,
    }
    response = requests.post(url, params=payload)
    wall_upload_server = response.json()
    check_for_vk_errors(wall_upload_server)
    return wall_upload_server['response']['upload_url']


def upload_image(filename, upload_url, token):
    with open(filename, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        image_upload_result = response.json()
        check_for_vk_errors(image_upload_result)
    return image_upload_result['server'], image_upload_result['photo'], image_upload_result['hash']


def save_image_in_group_album(uploaded_image_server, uploaded_photo, uploaded_hash, token):
    url = '{}{}'.format(VK_ENTRY_API_URL, "photos.saveWallPhoto")
    payload = {
        'v': VK_API_VERSION,
        'access_token': token,
        'photo': uploaded_photo,
        'server': uploaded_image_server,
        'hash': uploaded_hash,
    }
    response = requests.post(url, params=payload)
    saved_image_result = response.json()
    check_for_vk_errors(saved_image_result)
    for image in saved_image_result['response']:
        return image['id'], image['owner_id']


def publish_image(image_id, owner_id, group_id, image_comment, token):
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
    server_answer = response.json()
    check_for_vk_errors(server_answer)


def check_for_vk_errors(json_data):
    if 'error' in json_data:
        raise requests.exceptions.HTTPError(json_data['error'])


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("ACCESS_TOKEN")
    group_id = os.getenv("GROUP_ID")
    random_image_num = choose_random_image()
    image_url = get_image_url(random_image_num)
    image_comment = get_image_comment(random_image_num)
    filename = download_random_comic(image_url)
    try:
        upload_url = get_url_for_uploading_image(token)
        uploaded_image_server, uploaded_photo, uploaded_hash = upload_image(filename, upload_url, token)
        image_id, owner_id = save_image_in_group_album(uploaded_image_server, uploaded_photo, uploaded_hash, token)
        publish_image(image_id, owner_id, group_id, image_comment, token)
    except requests.exceptions.HTTPError as error:
        print('Поймали ошибку: ', error)
    finally:
        os.remove(filename)
