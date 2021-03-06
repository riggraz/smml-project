import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import preprocessing, layers, models, optimizers, losses

def train(config, hyperparams, network):
  # load dataset
  train_ds = preprocessing.image_dataset_from_directory(
    config['train_ds_path'],
    validation_split=hyperparams['validation_split'],
    subset='training',
    seed=123,
    image_size=config['img_size'],
    color_mode=config['img_color_mode'],
    batch_size=hyperparams['batch_size'],
  )

  validation_ds = preprocessing.image_dataset_from_directory(
    config['train_ds_path'],
    validation_split=hyperparams['validation_split'],
    subset='validation',
    seed=123,
    image_size=config['img_size'],
    color_mode=config['img_color_mode'],
    batch_size=hyperparams['batch_size'],
  )

  class_names = train_ds.class_names

  # configure dataset for performance
  AUTOTUNE = tf.data.experimental.AUTOTUNE

  train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
  validation_ds = validation_ds.cache().prefetch(buffer_size=AUTOTUNE)

  # build model
  network_architecture = []

  if (network['data_augmentation']):
    data_augmentation = models.Sequential(network['data_augmentation'])
    network_architecture.append(data_augmentation)

  network_architecture.append(layers.experimental.preprocessing.Rescaling(1.0/255))
  network_architecture.extend(network['topology'])
  network_architecture.append(layers.Dense(len(class_names)))

  model = models.Sequential(network_architecture)

  optimizer = None
  if (hyperparams['optimizer'] == 'adam'):
    optimizer = optimizers.Adam(learning_rate=hyperparams['learning_rate'])
  elif (hyperparams['optimizer'] == 'adamax'):
    optimizer = optimizers.Adamax(learning_rate=hyperparams['learning_rate'])
  elif (hyperparams['optimizer'] == 'sgd'):
    optimizer = optimizers.SGD(learning_rate=hyperparams['learning_rate'])
  else:
    optimizer = optimizers.Adam(learning_rate=hyperparams['learning_rate']) # default optimizer

  # compile model
  model.compile(
    optimizer=optimizer,
    loss=losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy'],
  )

  # train model
  history = model.fit(
    train_ds,
    validation_data=validation_ds,
    epochs=hyperparams['epochs'],
    callbacks=network['model_fit_callbacks'],
    # steps_per_epoch=80,
    # validation_steps=20,
  )

  model.summary()

  return (model, history)


def evaluate(model, config):
  # load test set
  test_ds = preprocessing.image_dataset_from_directory(
    config['test_ds_path'],
    image_size=config['img_size'],
    color_mode=config['img_color_mode'],
  )

  # evaluate model
  test_loss, test_acc = model.evaluate(x=test_ds, verbose=0)
  
  # returns 0-1 loss
  return 1 - test_acc

def predict_and_show_errors(model, config):
  # load test set
  test_ds = preprocessing.image_dataset_from_directory(
    config['test_ds_path'],
    image_size=config['img_size'],
    color_mode=config['img_color_mode'],
  )

  wrong_predictions = []
  i = 0

  for image, label in test_ds.unbatch():
    correct_label = label.numpy()

    image = tf.keras.preprocessing.image.img_to_array(image)
    image = tf.expand_dims(image, 0)
    prediction = model.predict(image)
    predicted_label = np.argmax(prediction)

    print("Label:", correct_label, " |", "Prediction:", predicted_label)

    if correct_label != predicted_label:
      wrong_predictions.append((image, correct_label, predicted_label))

    i = i + 1

  print("Wrong predictions #:", len(wrong_predictions))

  plt.figure(figsize=(10, 10))
  i = 0
  for image, correct_label, predicted_label in wrong_predictions:
    if i == 9: break
    ax = plt.subplot(3, 3, i + 1)
    plt.imshow(np.squeeze(image).astype("uint8"))
    plt.title("{} / {}".format(test_ds.class_names[predicted_label], test_ds.class_names[correct_label]))
    plt.axis("off")
    i = i + 1
  plt.show()