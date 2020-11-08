from flask_redis import FlaskRedis
from datetime import datetime
import hashlib
import time

CHARS = 'w01qrJlpTkn7z8W2gYMSsLR6b4hBZHOIjEUeQfGPFCdto3AcNK5uavxy9XDmiV'
HASH_URL_COUNT = 'urlcount'
TOTAL_LENGTH = 7


def int2base(x, base) -> str:
    if x == 0:
        return CHARS[0]

    digits = []

    while x:
        digits.append(CHARS[int(x % base)])
        x = int(x / base)

    digits.reverse()

    return ''.join(digits)


def convert_to_hash(index: int) -> str:
    return int2base(index, len(CHARS))


def generate_form_hash(redis_client: FlaskRedis) -> str:
    time_ms = time.time() * 1000
    unique_hash = hashlib.sha224(str(time_ms).encode('utf-8')).hexdigest()
    redis_client.set(unique_hash, 1)
    redis_client.expire(unique_hash, 60 * 15)  # 15 minutes
    return unique_hash


def get_and_increment_index(redis_client: FlaskRedis) -> int:
    if redis_client.exists(HASH_URL_COUNT) == 0:
        redis_client.set(HASH_URL_COUNT, 0)

    return redis_client.incr(HASH_URL_COUNT)


def set_hash(redis_client: FlaskRedis, hash: str, url: str):
    redis_client.set(hash, url)
    redis_client.set(url, hash)


def check_url_exists(redis_client: FlaskRedis, url: str) -> str:
    if redis_client.exists(url) > 0:
        return str(redis_client.get(url).decode('utf-8'))
    return None


def check_hash_exists(redis_client: FlaskRedis, hash: str) -> str:
    if redis_client.exists(hash) > 0:
        return str(redis_client.get(hash).decode('utf-8'))
    return None


def increment_view_counter(redis_client: FlaskRedis, hash: str):
    now_dt = datetime.utcnow()
    date_str = '{}{}{}'.format(now_dt.year, now_dt.month, now_dt.day)
    # Total Counter
    if redis_client.exists('{}-counter'.format(hash)) == 0:
        redis_client.set('{}-counter'.format(hash), 0)

    # Per Day Counter
    if redis_client.exists(hash + date_str) == 0:
        redis_client.set(hash + date_str, 0)
        redis_client.lpush('{}-date-list'.format(hash), hash + date_str)

    day_count = redis_client.incr(hash + date_str)
    total_count = redis_client.incr('{}-counter'.format(hash))

    print('Day {} Counter for Hash {} incremented to {}'.format(
        hash + date_str, hash, day_count))
    print('Total Counter for Hash {} incremented to {}'.format(hash, total_count))


def get_statistics_for_link(redis_client: FlaskRedis, hash: str, found_url: str) -> dict:
    stats = {'result': True, 'hash': hash, 'url': found_url}
    stats['total_count'] = str(redis_client.get(
        '{}-counter'.format(hash)).decode('utf-8'))
    day_list = [str(el.decode('utf-8'))
                for el in redis_client.lrange('{}-date-list'.format(hash), 0, -1)]
    stats['counter_per_day'] = [{day: redis_client.get(
        day).decode('utf-8')} for day in day_list]

    return stats
