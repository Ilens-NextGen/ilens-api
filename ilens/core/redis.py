from redis import Redis
import json

class RedisDB():
    def __init__(self, *args, **kwargs):
        self.redis = Redis(*args, **kwargs)
        
    def get(self, key, is_json=False):
        if is_json:
            return json.loads(self.redis.get(key))
        return self.redis.get(key)
    
    def set(self, key, value, expire=None, is_json=False):
        if is_json:
            value = json.dumps(value)
        return self.redis.set(key, value, ex=expire)

redisCI = RedisDB(host='34.229.72.206', port=6379, db=0)