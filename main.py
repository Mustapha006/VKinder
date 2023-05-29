import vk_api
import os
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.exceptions import ApiError
from datetime import datetime
from db.functions import DbVkSearch
from dotenv import load_dotenv
from bot import user_search, get_user_info, get_user_photos, write_msg

load_dotenv()

# загружаем данные из переменной окружения .env
token = os.getenv('token')
VKtoken = os.getenv('VKtoken')

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
db_vk = DbVkSearch()


def main():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            request = event.text.lower()
            user_info = get_user_info(event.user_id)

            if request == "привет":
                write_msg(event.user_id,
                          f"{user_info['first_name']}, в каком году вы родились ?")

            elif request.isdigit() and len(request) == 4:
                date = int(str(datetime.now())[:4]) - int(request)
                if not db_vk.user_in_db(event.user_id):
                    db_vk.add_new_user(event.user_id,
                                       name=f"{user_info['first_name']} {user_info['last_name']}",
                                       age=date,
                                       sex=user_info['gender'],
                                       city=user_info['city'])
                keyboard = VkKeyboard(one_time=True)
                keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
                write_msg(event.user_id,
                          f"{user_info['first_name']}, рад приветствовать вас!\n"
                          f" Для поиска пары нажмите кнопку ниже)",
                          keyboard=keyboard)

            elif request == "найти пару":
                age_user = db_vk.get_age_user(event.user_id)
                variants_list = user_search(user_vk_id=event.user_id,
                                            age_from=age_user - 2,
                                            age_to=age_user + 2)
                for variant in variants_list:
                    try:
                        variant_id = variant.get('id')
                        if not db_vk.variant_in_db_for_user(event.user_id, variant_id):
                            photo = [x['photo_id'] for x in get_user_photos(variant_id)]
                            attachment_photo = [f'photo{variant_id}_{x}' for x in photo]
                            keyboard = VkKeyboard()

                            buttons = ['Дизлайк', 'Лайк', 'Далее']
                            button_colors = [VkKeyboardColor.NEGATIVE, VkKeyboardColor.POSITIVE,
                                             VkKeyboardColor.PRIMARY]

                            for button, button_collor in zip(buttons, button_colors):
                                keyboard.add_button(button, button_collor)
                            keyboard.add_line()
                            keyboard.add_button(f'Вывести понравившихся', VkKeyboardColor.SECONDARY)
                            db_vk.add_new_variants(event.user_id,
                                                   id_vk=variant_id,
                                                   name=f"{variant.get('first_name')} {variant.get('last_name')}",
                                                   age=variant.get('bdate'),
                                                   sex=variant.get('sex'),
                                                   city=user_info.get('city'),
                                                   )
                            write_msg(event.user_id,
                                      f"{variant.get('first_name')} "
                                      f"{variant.get('last_name')}\n"
                                      f"Ссылка на профиль: https://vk.com/id"
                                      f"{variant_id}\n",
                                      attachment=','.join(attachment_photo),
                                      keyboard=keyboard)
                            break
                        else:
                            continue
                    except ApiError:
                        continue

            elif request == 'лайк':
                variant_id = db_vk.count_new_variant(event.user_id)
                db_vk.new_status_for_variants(event.user_id, str(variant_id), 'LIKE')

            elif request == 'дизлайк':
                variant_id = db_vk.count_new_variant(event.user_id)
                db_vk.new_status_for_variants(event.user_id, str(variant_id), 'DISLIKE')

            elif request == 'далее':
                age_user = db_vk.get_age_user(event.user_id)
                variants_list = user_search(user_vk_id=event.user_id,
                                            age_from=age_user - 2,
                                            age_to=age_user + 2)
                for variant in variants_list:
                    try:
                        variant_id = variant.get('id')
                        if not db_vk.variant_in_db_for_user(event.user_id, variant_id):
                            photo = [x['photo_id'] for x in get_user_photos(variant_id)]
                            attachment_photo = [f'photo{variant_id}_{x}' for x in photo]
                            db_vk.add_new_variants(event.user_id,
                                                   id_vk=variant_id,
                                                   name=f"{variant.get('first_name')} {variant.get('last_name')}",
                                                   age=variant.get('bdate'),
                                                   sex=variant.get('sex'),
                                                   city=user_info.get('city'),
                                                   )
                            write_msg(event.user_id, f"Вам может подойти {variant.get('first_name')} "
                                                     f"{variant.get('last_name')}\n"
                                                     f"Ссылка на профиль: https://vk.com/id"
                                                     f"{variant.get('id')}\n",
                                      attachment=','.join(attachment_photo))
                            break
                        else:
                            continue
                    except ApiError:
                        continue

            elif request == 'вывести понравившихся':
                list_like_variants = db_vk.get_all_variants_for_user(event.user_id, 'LIKE')
                sting_like_variant = "\n".join(list_like_variants)
                write_msg(event.user_id, f"""Понравившиеся:\n{sting_like_variant}""")

            elif request == "пока":
                write_msg(event.user_id, f"До новых встреч!\n для моей активации напишите: `привет`")

            else:
                write_msg(event.user_id, "Не понял вашего ответа...")


if __name__ == "__main__":
    print('Working...')
    main()
    db_vk.close()
