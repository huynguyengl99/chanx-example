# noqa

bind = "0.0.0.0:8000"
loglevel = "info"
accesslog = "-"
errorlog = "-"

forwarded_allow_ips = "*"

worker_class = "gevent"
workers = 1
