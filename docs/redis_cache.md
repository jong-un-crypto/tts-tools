# 1 User Cache

hash 还是pb序列化

用户资料

| key                    | 类型 | 说明                                            | 举例 |
| ---------------------- | ---- | ----------------------------------------------- | ---- |
| user:{user_id}:profile | hash | user_id用户的数据缓存，包括手机号、用户名、头像 |      |

用户扩展资料

| key                     | 类型   | 说明                   | 举例 |
| ----------------------- | ------ | ---------------------- | ---- |
| user:{user_id}:profilex | string | user_id用户的性别 生日 |      |

用户状态

| key                   | 类型   | 说明                | 举例 |
| --------------------- | ------ | ------------------- | ---- |
| user:{user_id}:status | string | user_id用户是否可用 |      |

# 2 Announcement Cache

| key                        | 类型   | 说明 | 举例                               |
| -------------------------- | ------ | ---- | ---------------------------------- |
| announce                   | zset   |      | [{'pickle data', announcement_id}] |
| announce:{announcement_id} | string |      | 'pickle data'                      |
