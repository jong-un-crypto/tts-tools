import random


# 缓存评论最大SCORE
COMMENTS_CACHE_MAX_SCORE = 2e19

# 默认用户头像
DEFAULT_USER_PROFILE_PHOTO = 'Fkj6tQi3xJwVXi1u2swCElotfdCi'  # 程序猿

# 阅读历史每人保存数目
READING_HISTORY_COUNT_PER_USER = 100

# 用户搜索历史每人保存数目
SEARCHING_HISTORY_COUNT_PER_USER = 4

# 允许用户资料数据缓存更新的TTL限制，秒
# ALLOW_UPDATE_USER_PROFILE_CACHE_TTL_LIMIT = 5

# 允许用户资料数据缓存中统计数据更新的TTL限制，秒
# ALLOW_UPDATE_USER_PROFILE_STATISTIC_CACHE_TTL_LIMIT = 5 + ALLOW_UPDATE_USER_PROFILE_CACHE_TTL_LIMIT

# 系统公告缓存时间，秒
ANNOUNCEMENTS_CACHE_TTL = 48 * 60 * 60


class BaseCacheTTL(object):
    """
    缓存有效期
    为防止缓存雪崩，在设置缓存有效期时采用设置不同有效期的方案
    通过增加随机值实现
    """
    TTL = 0  # 由子类设置
    MAX_DELTA = 10 * 60  # 随机的增量上限

    @classmethod
    def get_val(cls):
        return cls.TTL + random.randrange(0, cls.MAX_DELTA)


class UserProfileCacheTTL(BaseCacheTTL):
    """
    用户资料数据缓存时间, 秒
    """
    TTL = 30 * 60


class UserStatusCacheTTL(BaseCacheTTL):
    """
    用户状态缓存时间，秒
    """
    TTL = 60 * 60


class UserNotExistsCacheTTL(BaseCacheTTL):
    """
    用户不存在结果缓存
    为解决缓存击穿，有效期不宜过长
    """
    TTL = 5 * 60
    MAX_DELTA = 60


class AnnouncementDetailCacheTTL(BaseCacheTTL):
    """
    系统公告详细信息缓存时间，秒
    """
    TTL = 2 * 60 * 60


class AnnouncementNotExistsCacheTTL(BaseCacheTTL):
    """
    公告不存在结果缓存
    为解决缓存击穿，有效期不宜过长
    """
    TTL = 5 * 60
    MAX_DELTA = 60
