#!/usr/bin/env python3
"""Redis subscriber for testing erie.publisher.redis.Redis."""

import argparse
import logging
import redis
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Redis subscriber for testing")
    parser.add_argument("--host", default="localhost", help="Redis host")
    parser.add_argument("--port", type=int, default=6379, help="Redis port")
    parser.add_argument("--channel", default="erie", help="Redis channel to subscribe")
    parser.add_argument("--db", type=int, default=0, help="Redis database number")
    args = parser.parse_args()

    client = redis.Redis(host=args.host, port=args.port, db=args.db, decode_responses=True)
    pubsub = client.pubsub()
    pubsub.subscribe(args.channel)

    logger.info(f"Subscribed to {args.channel} on {args.host}:{args.port}")

    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                logger.info(f"Received: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                logger.info(f"Received (raw): {message['data']}")
        elif message["type"] == "subscribe":
            logger.info(f"Subscribed to channel: {message['channel']}")


if __name__ == "__main__":
    main()