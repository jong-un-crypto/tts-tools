from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from utils import parser
from flask import g, current_app
from flask_restful import inputs

from utils.decorators import login_required
from utils.qiniu_oss import upload

from cache import user as cache_user  # 为导入的模块起别名


class CurrentUserResource(Resource):
    """
    用户自己的数据
    """
    method_decorators = [login_required]

    def get(self):
        """
        获取当前用户自己的数据
        """
        user_data = cache_user.UserProfileCache(g.user_id).get()
        user_data['id'] = g.user_id
        del user_data['mobile']
        return user_data


class PhotoResource(Resource):
    """
    用户图像 （头像，身份证）
    """
    method_decorators = [login_required]

    def patch(self):
        file_parser = RequestParser()
        file_parser.add_argument(
            'photo', type=parser.image_file, required=False, location='files')
        file_parser.add_argument(
            'id_card_front', type=parser.image_file, required=False, location='files')
        file_parser.add_argument(
            'id_card_back', type=parser.image_file, required=False, location='files')
        file_parser.add_argument(
            'id_card_handheld', type=parser.image_file, required=False, location='files')
        files = file_parser.parse_args()

        user_id = g.user_id
        new_user_values = {}
        new_profile_values = {}
        return_values = {'id': user_id}
        need_delete_profile = False

        if files.photo:
            try:
                photo_url = upload(files.photo.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading profile photo image failed.'}, 507
            new_user_values['profile_photo'] = photo_url
            return_values['photo'] = current_app.config['QINIU_DOMAIN'] + photo_url
            need_delete_profile = True

        if files.id_card_front:
            try:
                id_card_front_url = upload(files.id_card_front.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_front image failed.'}, 507
            new_profile_values['id_card_front'] = id_card_front_url
            return_values['id_card_front'] = current_app.config['QINIU_DOMAIN'] + \
                id_card_front_url

        if files.id_card_back:
            try:
                id_card_back_url = upload(files.id_card_back.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_back image failed.'}, 507
            new_profile_values['id_card_back'] = id_card_back_url
            return_values['id_card_back'] = current_app.config['QINIU_DOMAIN'] + \
                id_card_back_url

        if files.id_card_handheld:
            try:
                id_card_handheld_url = upload(files.id_card_handheld.read())
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_handheld image failed.'}, 507
            new_profile_values['id_card_handheld'] = id_card_handheld_url
            return_values['id_card_handheld'] = current_app.config['QINIU_DOMAIN'] + \
                id_card_handheld_url

        if need_delete_profile:
            cache_user.UserProfileCache(user_id).clear()

        return return_values, 201


class UserResource(Resource):
    """
    用户数据资源
    """

    def get(self, target):
        """
        获取target用户的数据
        :param target: 目标用户id
        """
        cache = cache_user.UserProfileCache(target)
        exists = cache.exists()
        if not exists:
            return {'message': 'Invalid target user.'}, 400

        user_data = cache.get()

        user_data['is_following'] = False
        user_data['is_blacklist'] = False

        user_data['id'] = target
        del user_data['mobile']
        return user_data


class ProfileResource(Resource):
    """
    用户资料
    """
    method_decorators = {
        'get': [login_required],
        'patch': [login_required],
    }

    def get(self):
        """
        获取用户资料
        """
        user_id = g.user_id
        user = cache_user.UserProfileCache(user_id).get()
        result = {
            'id': user_id,
            'name': user['name'],
            'photo': user['photo'],
            'mobile': user['mobile']
        }
        # 补充性别生日等信息
        result.update(cache_user.UserAdditionalProfileCache(user_id).get())
        return result

    def _gender(self, value):
        """
        判断性别参数值
        """
        try:
            value = int(value)
        except Exception:
            raise ValueError('Invalid gender.')

        if value in [UserProfile.GENDER.MALE, UserProfile.GENDER.FEMALE]:
            return value
        else:
            raise ValueError('Invalid gender.')

    def patch(self):
        """
        编辑用户的信息
        """
        json_parser = RequestParser()
        json_parser.add_argument('name', type=inputs.regex(
            r'^.{1,7}$'), required=False, location='json')
        json_parser.add_argument(
            'photo', type=parser.image_base64, required=False, location='json')
        json_parser.add_argument(
            'gender', type=self._gender, required=False, location='json')
        json_parser.add_argument(
            'birthday', type=parser.date, required=False, location='json')
        json_parser.add_argument('intro', type=inputs.regex(
            r'^.{0,60}$'), required=False, location='json')
        json_parser.add_argument('real_name', type=inputs.regex(
            r'^.{1,7}$'), required=False, location='json')
        json_parser.add_argument(
            'id_number', type=parser.id_number, required=False, location='json')
        json_parser.add_argument(
            'id_card_front', type=parser.image_base64, required=False, location='json')
        json_parser.add_argument(
            'id_card_back', type=parser.image_base64, required=False, location='json')
        json_parser.add_argument(
            'id_card_handheld', type=parser.image_base64, required=False, location='json')
        args = json_parser.parse_args()

        user_id = g.user_id
        new_user_values = {}
        new_profile_values = {}
        return_values = {'id': user_id}

        need_delete_profilex = False
        need_delete_profile = False

        if args.name:
            new_user_values['name'] = args.name
            return_values['name'] = args.name
            need_delete_profile = True

        if args.photo:
            try:
                photo_url = upload(args.photo)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading profile photo image failed.'}, 507
            new_user_values['profile_photo'] = photo_url
            return_values['photo'] = current_app.config['QINIU_DOMAIN'] + photo_url
            need_delete_profile = True

        if args.gender:
            new_profile_values['gender'] = args.gender
            return_values['gender'] = args.gender
            need_delete_profilex = True

        if args.birthday:
            new_profile_values['birthday'] = args.birthday
            return_values['birthday'] = args.birthday.strftime('%Y-%m-%d')
            need_delete_profilex = True

        if args.intro:
            new_user_values['introduction'] = args.intro
            return_values['intro'] = args.intro
            need_delete_profile = True

        if args.real_name:
            new_profile_values['real_name'] = args.real_name
            return_values['real_name'] = args.real_name

        if args.id_number:
            new_profile_values['id_number'] = args.id_number
            return_values['id_number'] = args.id_number

        if args.id_card_front:
            try:
                id_card_front_url = upload(args.id_card_front)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_front image failed.'}, 507
            new_profile_values['id_card_front'] = id_card_front_url
            return_values['id_card_front'] = current_app.config['QINIU_DOMAIN'] + \
                id_card_front_url

        if args.id_card_back:
            try:
                id_card_back_url = upload(args.id_card_back)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_back image failed.'}, 507
            new_profile_values['id_card_back'] = id_card_back_url
            return_values['id_card_back'] = current_app.config['QINIU_DOMAIN'] + \
                id_card_back_url

        if args.id_card_handheld:
            try:
                id_card_handheld_url = upload(args.id_card_handheld)
            except Exception as e:
                current_app.logger.error('upload failed {}'.format(e))
                return {'message': 'Uploading id_card_handheld image failed.'}, 507
            new_profile_values['id_card_handheld'] = id_card_handheld_url
            return_values['id_card_handheld'] = current_app.config['QINIU_DOMAIN'] + \
                id_card_handheld_url

        if need_delete_profile:
            cache_user.UserProfileCache(user_id).clear()

        if need_delete_profilex:
            cache_user.UserAdditionalProfileCache(user_id).clear()

        return return_values, 201
