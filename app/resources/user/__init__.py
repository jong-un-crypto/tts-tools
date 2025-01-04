from flask import Blueprint
from flask_restful import Api

from . import passport
from . import profile
from utils.output import output_json

user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, catch_all_404s=True)
user_api.representation('application/json')(output_json)

user_api.add_resource(passport.SMSVerificationCodeResource, '/v1/sms/codes/<mobile:mobile>',
                      endpoint='SMSVerificationCode')

user_api.add_resource(passport.AuthorizationResource, '/v1/authorizations',
                      endpoint='Authorization')

user_api.add_resource(profile.UserResource, '/v1/users/<int(min=1):target>',
                      endpoint='User')

user_api.add_resource(profile.CurrentUserResource, '/v1/user',
                      endpoint='CurrentUser')

user_api.add_resource(profile.ProfileResource, '/v1/user/profile',
                      endpoint='Profile')

user_api.add_resource(profile.PhotoResource, '/v1/user/photo',
                      endpoint='Photo')
