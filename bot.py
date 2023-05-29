import vk_api
import os
from vk_api.keyboard import VkKeyboard
from dotenv import load_dotenv
from random import randrange

load_dotenv()

# загружаем данные из переменной окружения .env
token = os.getenv('token')
VKtoken = os.getenv('VKtoken')

vk = vk_api.VkApi(token=token)
vk_session = vk_api.VkApi(token=VKtoken)
vk_request = vk_session.get_api()

def write_msg(user_vk_id: str or int, message: str, attachment=None, keyboard=None) -> dict:
    """ Функция отправляет сообщение через VK API указанному пользователю VK """

    params = {
        'user_id': user_vk_id,
        'message': message,
        'random_id': randrange(10 ** 7),
    }

    if attachment is not None and isinstance(attachment, str):
        params['attachment'] = attachment
    if keyboard is not None and isinstance(keyboard, vk_api.keyboard.VkKeyboard):
        params['keyboard'] = keyboard.get_keyboard()

    response = vk.method('messages.send', params)

    if isinstance(response, int):
        return {'result': True, 'id_msg': response}
    else:
        return {'result': False, 'error': response}


def get_user_info(user_vk_id: str or int) -> dict:
    """ Функция позволяет получить данные пользователя VK, используя метод
    VK API users.get. (имя, фамилия, пол, город). """

    params = {'user_ids': f'{user_vk_id}',
              'fields': 'bdate, sex, city'
              }

    response = vk_request.users.get(**params)
    first_name = response[0].get('first_name')
    last_name = response[0].get('last_name')
    city = response[0].get('city')
    if city is not None:
        city = city.get('id')
    gender = response[0].get('sex')

    user_info = {
        'first_name': first_name,
        'last_name': last_name,
        'city': city,
        'gender': gender
    }
    return user_info


def user_search(user_vk_id: str or int, age_from=None, age_to=None) -> list:
    """ Функция позволяет получить список словарей с данными пользователей по указанным параметрам, используя метод """

    info_user = get_user_info(user_vk_id)
    if info_user.get('sex') == 1:
        sex = 2
    else:
        sex = 1
    params = {
              'sort': 0,
              'status': 6,
              'has_foto': 1,
              'city': info_user.get('city'),
              'sex': sex,
              'age_from': age_from,
              'age_to': age_to,
              'fields': 'bdate, sex',
              'count': 1000
              }
    response = vk_request.users.search(**params)
    return response.get('items')


def get_user_photos(user_vk_id: str or int) -> list:
    """ Функция позволяет получить фотографии указанного профиля VK, с помощью метода VK API photos.get """

    params = {
        'owner_id': f'{user_vk_id}',
        'album_id': 'profile',
        'rev': 0,
        'extended': 1,
              }
    response = vk_request.photos.get(**params)
    likes_ids_list = []
    try:
        for photos in response.get('items'):
            for photo in photos.get('sizes'):
                if 'm' in photo.get('type'):
                    likes_ids = {'like': (photos.get('likes').get('count')),
                                 'photo_id': (photos.get('id')),
                                 'photo_url': (photo.get('url'))}
                    likes_ids_list.append(likes_ids)
        return sorted(likes_ids_list, key=lambda x: x.get('like'), reverse=True)[:3]
    except AttributeError:
        return likes_ids_list[0:3]