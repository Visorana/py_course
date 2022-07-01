import urllib.request
import requests
import json
import datetime
import os
import logging
from PIL import Image

logging.basicConfig(level=logging.DEBUG)


class VkApi:
    def __init__(self, token: str):
        self.token = token
        self.name = 'vk'

    def get_path_name(self):
        return self.name

    def get_photos(self, target_id, number_of_photos=5):
        params = {
            'access_token': self.token,
            'v': '5.131',
            'owner_id': target_id,
            'album_id': 'profile',
            'rev': '0',
            'extended': 1,
            'photo_sizes': 0,
            'count': number_of_photos
        }
        req = requests.get('https://api.vk.com/method/photos.get', params).json()
        print(req)
        logging.info('Получен json файл.')
        return req

    def download_photos(self):
        req = self.get_photos(target_id)
        os.mkdir(self.name)
        for photo in req['response']['items']:
            max_size = photo['sizes'][-1]
            image_name = str(photo['likes']['count']) + '.jpg'
            list_files = os.listdir((os.getcwd() + '/' + self.name).replace('/', '\\'))
            if image_name in list_files:
                image_name = str(datetime.date.fromtimestamp(photo['date'])) + '.jpg'
            destination = self.name + '/' + str(image_name)
            urllib.request.urlretrieve(max_size['url'], destination)
        logging.info('Получены все фотографии.')
        list_files = os.listdir((os.getcwd() + '/' + self.name).replace('/', '\\'))
        return list_files


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def create_folder(self, folder):
        href = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': folder}
        requests.put(href, headers=headers, params=params)

    def _get_upload_link(self, destination):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": destination, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload(self, api):
        files = api.download_photos()
        self.create_folder(api.get_path_name())
        for file in files:
            destination = api.get_path_name() + '/' + file
            href = self._get_upload_link(destination).get("href", "")
            requests.put(href, data=open(destination, 'rb'))
            logging.info('Фотография загружена.')
        create_info_file(api)


def create_info_file(api):
    data = dict()
    count = 1
    files = os.listdir((os.getcwd() + '/' + api.get_path_name()).replace('/', '\\'))
    for file in files:
        image = Image.open(api.get_path_name() + '/' + file)
        w, h = image.size
        data[count] = {"file_name": file, "size": str(w) + 'x' + str(h)}
        count += 1
    with open('info.json', 'w') as f:
        json.dump(data, f, indent=4)
    logging.info('Создан json файл с информацией.')


if __name__ == '__main__':
    target_id = input('Введите id пользователя: ')
    token_ya = input('Введите токен Яндекс: ')
    token_vk = input('Введите токен VK: ')
    target_api = VkApi(token_vk)
    disk = YaUploader(token_ya)
    disk.upload(target_api)
    logging.info('Конец программы.')


