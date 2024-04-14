import base64
import urllib
from io import BytesIO
import json
import torch
import torchvision.transforms as transforms
from PIL import Image
import redis
from threading import Thread
import sqlite3
from sqlite3 import Error


r = redis.Redis(host='127.0.0.1', port=6379)

# Preload the pre-trained model
model = torch.hub.load('pytorch/vision:v0.10.0', 'inception_v3', pretrained=True)
model.eval()

preprocess = transforms.Compose([
    transforms.Resize((299, 299)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
categories = []

database = r"instance/database.db"


# SQLite Database
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def create_result_in_db(conn, result):
    sql = ''' INSERT INTO todo(url, content, date_created)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, result)
    conn.commit()
    return cur.lastrowid


# Image Classification
def preprocess_image(image_data):
    try:
        decoded_image = base64.b64decode(image_data)

        image = Image.open(BytesIO(decoded_image)).convert('RGB')

        preprocessed_image = preprocess(image)

        return preprocessed_image.unsqueeze(0)
    except Exception as e:
        print("Error preprocessing image: ", str(e))
        return None


def generate_predictions(image):
    with torch.no_grad():

        output = model(image)

        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top5_prob, top5_catid = torch.topk(probabilities, 5)

        labels = [categories[top5_catid[i]] for i in range(top5_prob.size(0))]
        probs = [top5_prob[i].item() for i in range(top5_prob.size(0))]

        return labels, probs


def listen_image():
    conn = create_connection(database)
    while True:
        message = r.brpop("image")
        data = json.loads(message[1])

        image_data = data['image']

        preprocessed_image = preprocess_image(image_data)

        if preprocessed_image is not None:
            labels, probs = generate_predictions(preprocessed_image)

            result = ""
            for i in range(5):
                result += str(i + 1) + ". " + labels[i] + " (" + str(round(probs[i], 4)) + ") \n"
            print(result)

            new_task = (data["url"], result, data["timestamp"])

            with conn:
                create_result_in_db(conn, new_task)


if __name__ == '__main__':
    urllib.request.urlretrieve("https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt",
                               "imagenet_classes.txt")
    with open("imagenet_classes.txt", "r") as f:
        categories = [s.strip() for s in f.readlines()]

    Thread(target=listen_image).start()

    #response = requests.get("http://r.ddmcdn.com/s_f/o_1/cx_462/cy_245/cw_1349/ch_1349/w_720/APL/uploads/2015/06/caturday-shutterstock_149320799.jpg")

