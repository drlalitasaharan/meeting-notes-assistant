from redis import Redis


def get_redis():
    return Redis(
        host="redis",
        port=6379,
        db=0,
        socket_connect_timeout=5,
        socket_keepalive=True,
        health_check_interval=30,
        retry_on_timeout=True,
        socket_timeout=10,
    )
