import urllib.request
import requests
import json
import datetime
import os
import logging
from PIL import Image
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logging.basicConfig(level=logging.DEBUG)


class VkApi:
    def __init__(self, token: str):
        self.token = token

    def get_photos(self, target_id, album_id, number_of_photos=5):
        params = {
            'access_token': self.token,
            'v': '5.131',
            'owner_id': target_id,
            'album_id': album_id,
            'rev': '0',
            'extended': 1,
            'photo_sizes': 0,
            'count': number_of_photos
        }
        req = requests.get('https://api.vk.com/method/photos.get', params).json()
        logging.info('Получен json файл.')
        return req

    def download_photos(self):
        req = self.get_photos(target_id, album_id, number_of_photos)
        os.mkdir(folder_name)
        count = 1
        for photo in req['response']['items']:
            max_size = photo['sizes'][-1]
            image_name = str(photo['likes']['count']) + '.jpg'
            list_files = os.listdir((os.getcwd() + '/' + folder_name).replace('/', '\\'))
            if image_name in list_files:
                image_name = str(datetime.date.fromtimestamp(photo['date'])) + '.jpg'
                if image_name in list_files:
                    image_name = str(datetime.date.fromtimestamp(photo['date'])) + '(' + str(count) + ')' + '.jpg'
                    count += 1
            destination = folder_name + '/'+ str(image_name)
            urllib.request.urlretrieve(max_size['url'], destination)
        logging.info('Получены все фотографии.')
        list_files = os.listdir((os.getcwd() + '/' + folder_name).replace('/', '\\'))
        return list_files


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def create_folder(self):
        href = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': folder_name}
        requests.put(href, headers=headers, params=params)
        logging.info('Создана папка на диске.')

    def _get_upload_link(self, destination):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": destination, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload(self):
        files = target_api.download_photos()
        self.create_folder()
        count = 0
        for file in files:
            destination = folder_name + '/' + file
            href = self._get_upload_link(destination).get("href", "")
            requests.put(href, data=open(destination, 'rb'))
            count += 1
            logging.info(f'Фотографий загружено: {count}/{len(files)}')


class GoogleUploader:
    def __init__(self):
        scopes = ['https://www.googleapis.com/auth/drive']
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
        self.creds = flow.run_local_server(port=0)

    def create_folder(self):
        service = build('drive', 'v3', credentials=self.creds)
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata, fields='id'
                                      ).execute()
        logging.info('Создана папка на диске.')
        return file.get("id")

    def upload(self):
        service = build('drive', 'v3', credentials=self.creds)
        folder_id = self.create_folder()
        files = target_api.download_photos()
        count = 0
        for file in files:
            destination = folder_name + '/' + file
            file_metadata = {
                'name': destination,
                'parents': [folder_id]
            }
            media = MediaFileUpload(destination,
                                    mimetype='image/jpeg', resumable=True)
            service.files().create(body=file_metadata, media_body=media,
                                   fields='id').execute()
            count += 1
            logging.info(f'Фотографий загружено: {count}/{len(files)}')


def create_info_file():
    data = dict()
    count = 1
    files = os.listdir((os.getcwd() + '/' + folder_name).replace('/', '\\'))
    for file in files:
        image = Image.open(folder_name + '/' + file)
        w, h = image.size
        data[count] = {"file_name": file, "size": str(w) + 'x' + str(h)}
        count += 1
    with open('info.json', 'w') as f:
        json.dump(data, f, indent=4)
    logging.info('Создан json файл с информацией.')


if __name__ == '__main__':
    target_id = input('Введите id владельца (Если сообщество, то укажите id со знаком "-"): ')
    album_id = input('Где хранятся нужные фотографии? Ответ на латинице("wall" - стена, '
                     '"profile" - профиль, "saved" - сохраненные, "album" - альбом): ')
    if album_id == 'album':
        album_id = input('Введите id альбома: ')
    number_of_photos = int(input('Количество фотографий для скачивания: '))
    folder_name = input('Название папки для фотографий: ')
    token_vk = input('Введите токен VK: ')
    while True:
        cloud = input('Диск для загрузки фото(Яндекс, Google): ')
        if cloud == 'Яндекс':
            token_ya = input('Введите токен Яндекс: ')
            target_cloud = YaUploader(token_ya)
            break
        elif cloud == 'Google':
            target_cloud = GoogleUploader()
            print('Не забудьте в рабочий каталог добавить файл "credentials.json" '
                  'с учетными данными OAuth client ID для аутентификации.')
            break
        else:
            print('Несуществующий диск.')
    target_api = VkApi(token_vk)
    target_cloud.upload()
    create_info_file()
    logging.info('Конец программы.')
