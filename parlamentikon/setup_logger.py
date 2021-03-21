import logging
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

#logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Sněmovna")
