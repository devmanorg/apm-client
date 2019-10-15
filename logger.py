#! /usr/bin/env python3
from functools import partial
import logging
from urllib.parse import urljoin
import os

from keylogger import pyxhook
import requests
import click


DEFAULT_API_HOST = os.getenv('API_HOST', 'http://127.0.0.1:8000')


def OnMouseButtonPress(send, event):
    send()
    logging.info(event.MessageName)


def OnKeyPress(send, event):
    send()
    logging.info('%s — %s', event.MessageName, event.Key)


@click.command()
@click.option('-v', '--verbose', count=True)
@click.option('-h', '--host', default=DEFAULT_API_HOST)
def main(host, verbose):

    log_level = {
        1: logging.INFO,
        2: logging.DEBUG,
    }.get(verbose, logging.WARNING)

    logging.basicConfig(level=log_level)

    new_hook = pyxhook.HookManager()

    with requests.Session() as session:
        play_registration_response = session.post(urljoin(host, '/api/plays/'))
        play_registration_response.raise_for_status()
        play_id = play_registration_response.json()['play_id']
        print(f'Game registered #{play_id}')

        def send_to_server():
            try:
                response = session.post(urljoin(host, f'/api/track/{play_id}/'), timeout=0.5)
                response.raise_for_status()
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                logging.warning('Connection lost')

        new_hook.KeyDown = partial(OnKeyPress, send_to_server)
        new_hook.MouseAllButtonsDown = partial(OnMouseButtonPress, send_to_server)

        try:
            new_hook.start()
            new_hook.join()
        except KeyboardInterrupt:
            exit()
        finally:
            new_hook.cancel()


if __name__ == '__main__':
    main()
