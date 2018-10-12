import asyncio
import logging
from os.environ import get as eget

from replayserver import Server
from replayserver.receive.mergestrategy import MergeStrategies
from replayserver.logging import logger

__all__ = ["main"]


def main():
    env_config = {
        "merger_grace_period_time": ("REPLAY_GRACE_PERIOD", 30),
        "replay_merge_strategy": ("REPLAY_MERGE_STRATEGY", "FOLLOW_STREAM"),
        "sent_replay_delay": ("REPLAY_DELAY", 5 * 60),
        "replay_forced_end_time": ("REPLAY_FORCE_END_TIME", 5 * 60 * 60),
        "server_port": ("PORT", 15000),
        "db_host": ("MYSQL_HOST", None),
        "db_port": ("MYSQL_PORT", None),
        "db_user": ("MYSQL_USER", None),
        "db_password": ("MYSQL_PASSWORD", None),
        "db_name": ("MYSQL_DB", None),
        "replay_store_path": ("REPLAY_DIR", None)
    }

    config = {
        "sent_replay_position_update_interval": 1,
    }

    config.update({k: eget(**v) for k, v in env_config.items()})
    config = {"config_" + k: v for k, v in config.items()}

    logger.setLevel(eget("LOG_LEVEL", logging.INFO))
    for key in config:
        if config[key] is None:
            logger.critical((f"Missing config key: {key}"
                             f"Set it using env var {config[key][0]}."))

    strat_str = config["config_replay_merge_strategy"]
    try:
        config["config_replay_merge_strategy"] = MergeStrategies(strat_str)
    except ValueError:
        logger.critical(f"{strat_str} is not a valid replay merge strategy")
        return 1

    server = Server.build(**config)
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(server.start())
    try:
        loop.run_forever()
        return 0
    except Exception as e:
        logger.critical(f"Critical server error! {e.__class__}: {str(e)}")
        loop.run_until_complete(server.stop())
        return 1
    finally:
        loop.close()
