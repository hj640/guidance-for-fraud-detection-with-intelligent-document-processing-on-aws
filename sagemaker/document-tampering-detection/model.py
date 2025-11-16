import numpy as np
import pandas as pd
import os
import tensorflow as tf
from sklearn.model_selection import train_test_split
import argparse
import json
import random

# Modeling
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPool2D
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import RMSprop
import boto3
from numpy import array
from PIL import Image, ImageChops, ImageEnhance

np.random.seed(2)
tf.random.set_seed(2)
random.seed(2)

def convert_to_ela_image(path, quality):
    filename = path
    resaved_filename = 'tempresaved.jpg'
    im = Image.open(filename)
    bm = im.convert('RGB')
    im.close()
    im=bm
    im.save(resaved_filename, 'JPEG', quality = quality)
    resaved_im = Image.open(resaved_filename)
    ela_im = ImageChops.difference(im, resaved_im)
    extrema = ela_im.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale = 255.0 / max_diff
    ela_im = ImageEnhance.Brightness(ela_im).enhance(scale)
    im.close()
    bm.close()
    resaved_im.close()
    del filename
    del resaved_filename
    del im
    del bm
    del resaved_im
    del extrema
    del max_diff
    del scale
    return ela_im

def prepare_dataset(image_path, label):
    image_data = {'image_path': [], 'label': []}
    for img in os.listdir(image_path):
        if img.endswith(('jpg', 'png', 'jpeg', 'JPEG', 'tif', 'tiff', 'TIF', 'TIFF', 'bmp')):
            temp_path = image_path+"/"+str(img)
            image_data['image_path'].append(temp_path)
            image_data['label'].append(label)
    return image_data


def _parse_args():
    parser = argparse.ArgumentParser()

    # Data, model, and output directories
    # model_dir is always passed in from SageMaker. By default this is a S3 path under the default bucket.
    parser.add_argument('--model_dir', type=str)
    parser.add_argument('--sm-model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ.get('SM_HOSTS')))
    parser.add_argument('--current-host', type=str, default=os.environ.get('SM_CURRENT_HOST'))

    return parser.parse_known_args()


if __name__ == "__main__":
    args, unknown = _parse_args()
    
    s3 = boto3.client("s3")

    print("ARGS", args)

    custom_path_original = f'{args.train}/Au/'
    custom_path_tampered = f'{args.train}/Tp/'
    
    tampered_image_data=pd.DataFrame(prepare_dataset(custom_path_tampered, 1))
    original_image_data=pd.DataFrame(prepare_dataset(custom_path_original, 0))
    dataset=pd.concat([tampered_image_data, original_image_data], axis=0)

    X = []
    Y = []
    for index, row in dataset.iterrows():
        X.append(array(convert_to_ela_image(row[0], 90).resize((128, 128))) / 255.0)
        Y.append(row[1])
    X = np.array(X)
    Y = to_categorical(Y, 2)
    
    X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size = 0.2, random_state=5)
    
    # VGG-16 CNN Model 
    model = tf.keras.models.Sequential()
    
    # Block 1
    model.add(Conv2D(32, (3,3), padding='same', activation='relu', input_shape=(128,128,3)))
    model.add(Conv2D(32, (3,3), padding='same', activation='relu'))
    model.add(MaxPool2D(2,2))
    model.add(Dropout(0.25))
    
    # Block 2
    model.add(Conv2D(64, (3,3), padding='same', activation='relu'))
    model.add(Conv2D(64, (3,3), padding='same', activation='relu'))
    model.add(MaxPool2D(2,2))
    model.add(Dropout(0.3))
    
    # Classifier - keep it moderate
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))  
    model.add(Dropout(0.5))
    model.add(Dense(2, activation='softmax'))
    
    optimizer = RMSprop(learning_rate=0.0005)
    model.compile(optimizer=optimizer, loss="categorical_crossentropy", metrics=["accuracy"])
    
    epochs = 30
    batch_size = 32  
    
    history = model.fit(X_train, Y_train, batch_size=batch_size, epochs=epochs, 
              validation_data=(X_val, Y_val), verbose=2)
    
    
    model.save(os.path.join(args.sm_model_dir, '000000001'))