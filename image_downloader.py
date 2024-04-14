import base64
import requests
import json
import redis
from threading import Thread


r = redis.Redis(host='127.0.0.1', port=6379)


def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        encoded_image = base64.b64encode(response.content).decode("utf-8")
        return encoded_image

    except Exception as e:
        print("Error downloading image: ", str(e))
        return None


def listen_download():
    while True:
        message = r.brpop("download")
        data = json.loads(message[1])

        timestamp = data["timestamp"]
        print(timestamp)
        url = data["url"]

        image_data = download_image(url)

        if image_data is not None:
            message = {
                "timestamp": timestamp,
                "url": url,
                "image": image_data
            }

            r.lpush("image", json.dumps(message))


if __name__ == '__main__':
    Thread(target=listen_download).start()