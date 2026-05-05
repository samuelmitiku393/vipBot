import logging

def setup_logging():
    # Create logger
    logger = logging.getLogger('bot')
    logger.setLevel(logging.INFO)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create file handler
    fh = logging.FileHandler('bot.log')
    fh.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # Add the handlers to the logger
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    # Set up basic config for other modules
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[ch, fh]
    )

    return logger

logger = logging.getLogger('bot')
