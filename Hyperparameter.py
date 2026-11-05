# Dataset: https://www.kaggle.com/datasets/anthonytherrien/dog-vs-cat

import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt
import time

# 1. Configuration
IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 0.001

# 2. Load and split dataset
train_ds = tf.keras.utils.image_dataset_from_directory(
    "data",
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    "data",
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)

# 3. Normalize images
normalization_layer = layers.Rescaling(1./255)

train_ds = train_ds.map(
    lambda x, y: (normalization_layer(x), y)
)

val_ds = val_ds.map(
    lambda x, y: (normalization_layer(x), y)
)

# 4. Build CNN with two Dense layers
model = models.Sequential([
    layers.Input(shape=(128, 128, 3)),

    layers.Conv2D(32, (3, 3), activation='relu'),
    layers.MaxPooling2D(),

    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D(),

    layers.Flatten(),

    layers.Dense(128, activation='relu'),
    layers.Dense(64, activation='relu'),

    layers.Dropout(0.3),

    layers.Dense(1, activation='sigmoid')
])

# 5. Compile model
model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# 6. TensorBoard logging
tensorboard_callback = tf.keras.callbacks.TensorBoard(
    log_dir="logs/experiment7"
)

# 7. Train model
start_time = time.time()

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=[tensorboard_callback]
)

training_time = time.time() - start_time

# 8. Evaluate model
loss, accuracy = model.evaluate(val_ds)

print("\nExperiment 7 Results")
print("Validation Accuracy:", round(accuracy * 100, 2), "%")
print("Validation Loss:", round(loss, 4))
print("Training Time:", round(training_time, 2), "seconds")

# 9. Save model
model.save("experiment7.keras")
print("Model saved successfully!")

# 10. Plot accuracy
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Experiment 7 - Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

# 11. Plot loss
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Experiment 7 - Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()