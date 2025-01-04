from flask import g, current_app
from functools import wraps

from cache import user as cache_user

def login_required(func):

    def wrapper(*args, **kwargs):
        if g.user_id is not None and g.is_refresh is False:
            return func(*args, **kwargs)
        else:
            return {'message': 'Invalid token'}, 401

    return wrapper


def validate_token_if_using(func):
    """
    如果Authorization中携带了Token，则检验token的有效性，否则放行
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.use_token and not g.user_id:
            return {'message': 'Token has some errors.'}, 401
        else:
            if g.user_id:
                # 判断用户状态
                user_enable = cache_user.UserStatusCache(g.user_id).get()
                if not user_enable:
                    return {'message': 'User denied.'}, 403

            return func(*args, **kwargs)

    return wrapper


def verify_required(func):
    """
    用户必须实名认证通过装饰器
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user_id:
            return {'message': 'User must be authorized.'}, 401
        elif g.is_refresh_token:
            return {'message': 'Do not use refresh token.'}, 403
        elif not g.is_verified:
            return {'message': 'User must be real info verified.'}, 403
        else:
            # 判断用户状态
            user_enable = cache_user.UserStatusCache(g.user_id).get()
            if not user_enable:
                return {'message': 'User denied.'}, 403

            return func(*args, **kwargs)

    return wrapper
