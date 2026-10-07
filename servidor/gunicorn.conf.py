import os

bind = "0.0.0.0:" + os.getenv("PORT", "3000")
workers = int(os.getenv("WEB_WORKERS", "3"))
threads = int(os.getenv("WEB_THREADS", "4"))
worker_class = "gthread"
# a atualização do TOTVS pode levar minutos (consultas grandes passam pelo servidor)
timeout = int(os.getenv("WEB_TIMEOUT", "660"))
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "*"
