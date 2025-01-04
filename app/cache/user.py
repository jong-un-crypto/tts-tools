from flask import current_app, g
import time
import json
from redis.exceptions import RedisError, ConnectionError

from . import constants


# user1  UserCache(1) -> key='user:1:profile' get
# user2  UserCache(2) -> key='user:2:profile' get

# 构建缓存工具,查询mysql，查询redis，缓存数据的更新，返回数据，解决缓存击穿和雪崩问题。
# 需求：实现用户信息的缓存的工具
class UserCache(object):
    """
    用户基本信息缓存工具类
    """

    def __init__(self, user_id):
        # redis数据记录的key 键
        self.key = 'user:{}:profile'.format(user_id)
        self.user_id = user_id
    # 工具类封装：实现代码的封装，代码的复用；
    # 类属性
    #   -> 所有对象共享类属性，也就是说所有对象中读取出的类属性 数据值都相同
    # 对象属性
    #  -> 每个对象单独所有，也就意味着每个对象的数据可以不同

    # 实例方法 （对象方法）
    # 类方法
    # 静态方法
    # 选择的依据：
    # 不同方法可以处理的类中的数据是不一样的
    #  对象方法-> 可以处理对象属性、类属性
    #  类方法-> 既可以通过类名也可以通过cls处理类属性
    #     @classmethod
    #     def func(cls, ...)
    # 静态方法  -> 通过类名可以处理类型属性 UserCache.key
    #    @staticmethod
    #    def func()
    # 需要异常处理的代码：
    # 1、IO操作，网络io和磁盘io
    # 2、参数校验、类型转换等。a = 'a'
    def save(self):
        """
        保存缓存记录
        :return:
        """
        r = current_app.redis_cluster
        try:
            user = User.query.options(load_only(
                User.mobile,
                User.name,
                User.profile_photo,
                User.introduction,
                User.certificate
            )).filter_by(id=self.user_id).first()
        except DatabaseError as e:
            current_app.logger.error(e)
            # 对于这个数据库异常，我们自己封装的get方法无法为调用者做决定，决定返回什么值，所以抛出异常给调用者，由调用者决定
            raise e

        # 在django中 查询单一对象，而数据库不存在，抛出异常  User.DoesNotExists
        # 在sqlalchemy中，查询单一对象，数据库不存爱，不抛出异常，只返回None
        if user is None:
            # 数据库不存在
            try:
                r.setex(self.key, constants.UserNotExistsCacheTTL.get_val(), -1)
            except RedisError as e:
                current_app.logger.error(e)

            return None
        else:
            user_dict = {
                'mobile': user.mobile,
                'name': user.name,
                'photo': user.profile_photo,
                'intro': user.introduction,
                'certi': user.certificate
            }
            try:
                r.setex(self.key, constants.UserProfileCacheTTL.get_val(),
                        json.dumps(user_dict))
            except RedisError as e:
                current_app.logger.error(e)

            return user_dict

    def get(self):
        """
        获取缓存数据
        :return: user dict
        """
        # 先查询redis缓存记录
        # 如果有记录 直接返回
        # 如果没有记录，查询数据库
        #      数据库中如果有记录，设置redis记录  json string
        #      数据库中如果没有记录，设置redis保存不存在的记录 -1
        # 返回
        r = current_app.redis_cluster
        try:
            ret = r.get(self.key)
        except RedisError as e:
            # 记录日志
            current_app.logger.error(e)
            # 在redis出现异常的时候，为了保证我们封装的get方法还能有返回值，可以进入数据库查询的部分
            ret = None

        if ret is not None:
            # 表示redis中有记录值
            # 判断redis记录是表示数据库不存在的-1值还是有意义的缓存记录
            # 切记： python3 从redis中取出的字符串数据是python中的bytes
            if ret == b'-1':
                return None
            else:
                # json.loads方法可以接受bytes类型
                user_dict = json.loads(ret)
                return user_dict
        else:
            return self.save()

    def clear(self):
        """
        清除缓存记录
        :return:
        """
        try:
            r = current_app.redis_cluster
            r.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def determine_user_exists(self):
        """
        通过缓存判断用户id是否存在
        :return: boolean True：存在  False：不存在
        """
        # 查询redis
        # 如果存在Redis记录
        #   如果redis记录为-1,表示不存在
        #   如果redis记录不为-1， 表示用户存在

        # 如果不存在redis记录
        #   去数据库查询，判断是否存在
        #   设置redis缓存记录
        r = current_app.redis_cluster
        try:
            ret = r.get(self.key)
        except RedisError as e:
            # 记录日志
            current_app.logger.error(e)
            # 在redis出现异常的时候，为了保证我们封装的get方法还能有返回值，可以进入数据库查询的部分
            ret = None

        if ret is not None:
            # 表示redis中有记录值
            # 判断redis记录是表示数据库不存在的-1值还是有意义的缓存记录
            # 切记： python3 从redis中取出的字符串数据是python中的bytes
            if ret == b'-1':
                return False
            else:
                return True
        else:
            ret = self.save()
            if ret is not None:
                return True
            else:
                return False


class UserProfileCache(object):
    """
    用户信息缓存
    """

    def __init__(self, user_id):
        self.key = 'user:{}:profile'.format(user_id)
        self.user_id = user_id

    def save(self, user=None, force=False):
        """
        设置用户数据缓存
        """
        rc = current_app.redis_cluster

        # 判断缓存是否存在
        if force:
            exists = False
        else:
            try:
                ret = rc.get(self.key)
            except RedisError as e:
                current_app.logger.error(e)
                exists = False
            else:
                if ret == b'-1':
                    exists = False
                else:
                    exists = True

        if not exists:
            # This user cache data did not exist previously.
            if user is None:
                user = User.query.options(load_only(User.name,
                                                    User.mobile,
                                                    User.profile_photo,
                                                    User.is_media,
                                                    User.introduction,
                                                    User.certificate)) \
                    .filter_by(id=self.user_id).first()

            if user is None:
                return None

            user_data = {
                'mobile': user.mobile,
                'name': user.name,
                'photo': user.profile_photo or '',
                'is_media': user.is_media,
                'intro': user.introduction or '',
                'certi': user.certificate or '',
            }

            try:
                rc.setex(
                    self.key, constants.UserProfileCacheTTL.get_val(), json.dumps(user_data))
            except RedisError as e:
                current_app.logger.error(e)
            return user_data

    def get(self):
        """
        获取用户数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None
        if ret:
            # hit cache
            user_data = json.loads(ret)
        else:
            user_data = self.save(force=True)

        user_data = self._fill_fields(user_data)

        if not user_data['photo']:
            user_data['photo'] = constants.DEFAULT_USER_PROFILE_PHOTO
        user_data['photo'] = current_app.config['QINIU_DOMAIN'] + \
            user_data['photo']
        return user_data

    def _fill_fields(self, user_data):
        """
        补充字段
        """
        user_data['art_count'] = cache_statistic.UserArticlesCountStorage.get(
            self.user_id)
        user_data['follow_count'] = cache_statistic.UserFollowingsCountStorage.get(
            self.user_id)
        user_data['fans_count'] = cache_statistic.UserFollowersCountStorage.get(
            self.user_id)
        user_data['like_count'] = cache_statistic.UserLikedCountStorage.get(
            self.user_id)
        return user_data

    def clear(self):
        """
        清除
        """
        try:
            current_app.redis_cluster.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def exists(self):
        """
        判断用户是否存在
        :return: bool
        """
        rc = current_app.redis_cluster

        # 此处可使用的键有三种选择 user:{}:profile 或 user:{}:status 或 新建
        # status主要为当前登录用户，而profile不仅仅是登录用户，覆盖范围更大，所以使用profile
        try:
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret is not None:
            return False if ret == b'-1' else True
        else:
            # 缓存中未查到
            user_data = self.save(force=True)
            if user_data is None:
                try:
                    rc.setex(
                        self.key, constants.UserNotExistsCacheTTL.get_val(), -1)
                except RedisError as e:
                    current_app.logger.error(e)
                return False
            else:
                return True


class UserStatusCache(object):
    """
    用户状态缓存
    """

    def __init__(self, user_id):
        self.key = 'user:{}:status'.format(user_id)
        self.user_id = user_id

    def save(self, status):
        """
        设置用户状态缓存
        :param status:
        """
        try:
            current_app.redis_cluster.setex(
                self.key, constants.UserStatusCacheTTL.get_val(), status)
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """
        获取用户状态
        :return:
        """
        rc = current_app.redis_cluster

        try:
            status = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            status = None

        if status is not None:
            return status
        else:
            user = User.query.options(load_only(User.status)).filter_by(
                id=self.user_id).first()
            if user:
                self.save(user.status)
                return user.status
            else:
                return False


class UserAdditionalProfileCache(object):
    """
    用户附加资料缓存（如性别、生日等）
    """

    def __init__(self, user_id):
        self.key = 'user:{}:profilex'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户的附加资料（如性别、生日等）
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            return json.loads(ret)
        else:
            profile = UserProfile.query.options(load_only(UserProfile.gender, UserProfile.birthday)) \
                .filter_by(id=self.user_id).first()
            profile_dict = {
                'gender': profile.gender,
                'birthday': profile.birthday.strftime('%Y-%m-%d') if profile.birthday else ''
            }
            try:
                rc.setex(self.key, constants.UserAdditionalProfileCacheTTL.get_val(
                ), json.dumps(profile_dict))
            except RedisError as e:
                current_app.logger.error(e)
            return profile_dict

    def clear(self):
        """
        清除用户的附加资料
        :return:
        """
        try:
            current_app.redis_cluster.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)


class UserSearchingHistoryStorage(object):
    """
    用户搜索历史
    """

    def __init__(self, user_id):
        self.key = 'user:{}:his:searching'.format(user_id)
        self.user_id = user_id

    def save(self, keyword):
        """
        保存用户搜索历史
        :param keyword: 关键词
        :return:
        """
        pl = current_app.redis_master.pipeline()
        pl.zadd(self.key, time.time(), keyword)
        pl.zremrangebyrank(
            self.key, 0, -1*(constants.SEARCHING_HISTORY_COUNT_PER_USER+1))
        pl.execute()

    def get(self):
        """
        获取搜索历史
        """
        try:
            keywords = current_app.redis_master.zrevrange(self.key, 0, -1)
        except ConnectionError as e:
            current_app.logger.error(e)
            keywords = current_app.redis_slave.zrevrange(self.key, 0, -1)

        keywords = [keyword.decode() for keyword in keywords]
        return keywords

    def clear(self):
        """
        清除
        """
        current_app.redis_master.delete(self.key)


class UserArticlesCache(object):
    """
    用户文章缓存
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.key = 'user:{}:art'.format(user_id)

    def get_page(self, page, per_page):
        """
        获取用户的文章列表
        :param page: 页数
        :param per_page: 每页数量
        :return: total_count, [article_id, ..]
        """
        rc = current_app.redis_cluster

        try:
            pl = rc.pipeline()
            pl.zcard(self.key)
            pl.zrevrange(self.key, (page - 1) * per_page, page * per_page)
            total_count, ret = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_count = 0
            ret = []

        if total_count > 0:
            # Cache exists.
            return total_count, [int(aid) for aid in ret]
        else:
            # No cache.
            total_count = cache_statistic.UserArticlesCountStorage.get(
                self.user_id)
            if total_count == 0:
                return 0, []

            ret = Article.query.options(load_only(Article.id, Article.ctime)) \
                .filter_by(user_id=self.user_id, status=Article.STATUS.APPROVED) \
                .order_by(Article.ctime.desc()).all()

            articles = []
            cache = []
            for article in ret:
                articles.append(article.id)
                cache.append(article.ctime.timestamp())
                cache.append(article.id)

            if cache:
                try:
                    pl = rc.pipeline()
                    pl.zadd(self.key, *cache)
                    pl.expire(
                        self.key, constants.UserArticlesCacheTTL.get_val())
                    results = pl.execute()
                    if results[0] and not results[1]:
                        rc.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)

            total_count = len(articles)
            page_articles = articles[(page - 1) * per_page:page * per_page]

            return total_count, page_articles

    def clear(self):
        """
        清除
        """
        rc = current_app.redis_cluster
        rc.delete(self.key)


class UserArticleCollectionsCache(object):
    """
    用户收藏文章缓存
    """

    def __init__(self, user_id):
        self.user_id = user_id
        self.key = 'user:{}:art:collection'.format(user_id)

    def get_page(self, page, per_page):
        """
        获取用户的文章列表
        :param page: 页数
        :param per_page: 每页数量
        :return: total_count, [article_id, ..]
        """
        rc = current_app.redis_cluster

        try:
            pl = rc.pipeline()
            pl.zcard(self.key)
            pl.zrevrange(self.key, (page - 1) * per_page, page * per_page)
            total_count, ret = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_count = 0
            ret = []

        if total_count > 0:
            # Cache exists.
            return total_count, [int(aid) for aid in ret]
        else:
            # No cache.
            total_count = cache_statistic.UserArticleCollectingCountStorage.get(
                self.user_id)
            if total_count == 0:
                return 0, []

            ret = Collection.query.options(load_only(Collection.article_id, Collection.utime)) \
                .filter_by(user_id=self.user_id, is_deleted=False) \
                .order_by(Collection.utime.desc()).all()

            collections = []
            cache = []
            for collection in ret:
                collections.append(collection.article_id)
                cache.append(collection.utime.timestamp())
                cache.append(collection.article_id)

            if cache:
                try:
                    pl = rc.pipeline()
                    pl.zadd(self.key, *cache)
                    pl.expire(
                        self.key, constants.UserArticleCollectionsCacheTTL.get_val())
                    results = pl.execute()
                    if results[0] and not results[1]:
                        rc.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)

            total_count = len(collections)
            page_articles = collections[(page - 1) * per_page:page * per_page]

            return total_count, page_articles

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)

    def determine_collect_target(self, target):
        """
        判断用户是否收藏了指定文章
        :param target:
        :return:
        """
        total_count, collections = self.get_page(1, -1)
        return target in collections


class UserArticleAttitudeCache(object):
    """
    用户文章态度缓存数据
    """

    def __init__(self, user_id):
        self.key = 'user:{}:art:attitude'.format(user_id)
        self.user_id = user_id

    def get_all(self):
        """
        获取用户文章态度数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.hgetall(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 为了防止缓存击穿
            if b'-1' in ret:
                return {}
            else:
                # In order to be consistent with db data type.
                return {int(aid): int(attitude) for aid, attitude in ret.items()}

        ret = Attitude.query.options(load_only(Attitude.article_id, Attitude.attitude)) \
            .filter(Attitude.user_id == self.user_id, Attitude.attitude != None).all()

        attitudes = {}
        for atti in ret:
            attitudes[atti.article_id] = atti.attitude

        pl = rc.pipeline()
        try:
            if attitudes:
                pl.hmset(self.key, attitudes)
                pl.expire(
                    self.key, constants.UserArticleAttitudeCacheTTL.get_val())
            else:
                pl.hmset(self.key, {-1: -1})
                pl.expire(
                    self.key, constants.UserArticleAttitudeNotExistsCacheTTL.get_val())
            results = pl.execute()
            if results[0] and not results[1]:
                rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return attitudes

    def get_article_attitude(self, article_id):
        """
        获取指定文章态度
        :param article_id:
        :return:
        """
        if hasattr(g, 'article_attitudes'):
            attitudes = g.article_attitudes
        else:
            attitudes = self.get_all()
            g.article_attitudes = attitudes

        return attitudes.get(article_id, -1)

    def determine_liking_article(self, article_id):
        """
        判断是否对文章点赞
        :param article_id:
        :return:
        """
        return self.get_article_attitude(article_id) == Attitude.ATTITUDE.LIKING

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)


class UserCommentLikingCache(object):
    """
    用户评论点赞缓存数据
    """

    def __init__(self, user_id):
        self.key = 'user:{}:comm:liking'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户文章评论点赞数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.smembers(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # 为了防止缓存击穿
            if b'-1' in ret:
                return []
            else:
                # In order to be consistent with db data type.
                return set([int(cid) for cid in ret])

        ret = CommentLiking.query.options(load_only(CommentLiking.comment_id)) \
            .filter(CommentLiking.user_id == self.user_id, CommentLiking.is_deleted == False).all()

        cids = [com.comment_id for com in ret]
        pl = rc.pipeline()
        try:
            if cids:
                pl.sadd(self.key, *cids)
                pl.expire(
                    self.key, constants.UserCommentLikingCacheTTL.get_val())
            else:
                pl.sadd(self.key, -1)
                pl.expire(
                    self.key, constants.UserCommentLikingNotExistsCacheTTL.get_val())
            results = pl.execute()
            if results[0] and not results[1]:
                rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return set(cids)

    def determine_liking_comment(self, comment_id):
        """
        判断是否对文章点赞
        :param comment_id:
        :return:
        """
        if hasattr(g, self.key):
            liking_comments = getattr(g, self.key)
        else:
            liking_comments = self.get()
            setattr(g, self.key, liking_comments)

        return comment_id in liking_comments

    def clear(self):
        """
        清除
        """
        current_app.redis_cluster.delete(self.key)

def get_user_articles(user_id):
    """
    获取用户的所有文章列表 已废弃
    :param user_id:
    :return:
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()

    ret = r.zrevrange('user:{}:art'.format(user_id), 0, -1)
    if ret:
        r.zadd('user:art', timestamp, user_id)
        return [int(aid) for aid in ret]

    ret = r.hget('user:{}'.format(user_id), 'art_count')
    if ret is not None and int(ret) == 0:
        return []

    ret = Article.query.options(load_only(Article.id, Article.ctime))\
        .filter_by(user_id=user_id, status=Article.STATUS.APPROVED)\
        .order_by(Article.ctime.desc()).all()

    articles = []
    cache = []
    for article in ret:
        articles.append(article.id)
        cache.append(article.ctime.timestamp())
        cache.append(article.id)

    if cache:
        pl = r.pipeline()
        pl.zadd('user:art', timestamp, user_id)
        pl.zadd('user:{}:art'.format(user_id), *cache)
        pl.execute()

    return articles
