"""Train the tomato leaf classifier used by app.py.

Transfer learning: a frozen ImageNet MobileNetV2 extracts features and a small
dense head is trained on top. Training mixes PlantVillage (lab photos),
PlantDoc (real field photos) and an "other" class of non-leaf photos so the
model can reject images that are not tomato leaves.

Expected layout under DATA_DIR:
    pv/<class>/*.jpg     PlantVillage images
    pd/<class>/*.jpg     PlantDoc images
    other/*.jpg          photos that are not tomato leaves

Usage: python train_mobilenet.py <DATA_DIR>              (stage 1: train the head)
       python train_mobilenet.py <DATA_DIR> --finetune   (stage 2: fine-tune the backbone)
"""
import os
import sys

import cv2
import numpy as np
import tensorflow as tf

IMG_SIZE = 224
CLASSES = ["bacterial_spot", "early_blight", "late_blight", "leaf_mold", "septoria",
           "spider_mites", "target_spot", "yellow_curl", "mosaic", "healthy", "other"]
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "tomato_mobilenetv2.h5")

rng = np.random.default_rng(0)


def load(path):
    buf = np.fromfile(path, np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR) if buf.size else None
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def views(img, n):
    """The full image plus n-1 random crops/flips/brightness changes."""
    out = [cv2.resize(img, (IMG_SIZE, IMG_SIZE))]
    h, w = img.shape[:2]
    for _ in range(n - 1):
        s = rng.uniform(0.6, 1.0)
        ch, cw = int(h * s), int(w * s)
        y, x = rng.integers(0, h - ch + 1), rng.integers(0, w - cw + 1)
        v = cv2.resize(img[y:y + ch, x:x + cw], (IMG_SIZE, IMG_SIZE))
        if rng.random() < 0.5:
            v = v[:, ::-1]
        v = np.clip(v.astype(np.float32) * rng.uniform(0.75, 1.25), 0, 255).astype(np.uint8)
        out.append(v)
    return out


def synthetic_other(n):
    """Plain colours, gradients and noise: inputs that are clearly not leaves."""
    imgs = []
    for i in range(n):
        kind = i % 3
        if kind == 0:
            img = np.full((IMG_SIZE, IMG_SIZE, 3), rng.integers(0, 256, 3), np.uint8)
        elif kind == 1:
            a, b = rng.integers(0, 256, 3), rng.integers(0, 256, 3)
            t = np.linspace(0, 1, IMG_SIZE)[None, :, None]
            img = (a * (1 - t) + b * t).repeat(IMG_SIZE, 0).astype(np.uint8)
        else:
            img = rng.integers(0, 256, (IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
        imgs.append(img)
    return imgs


def collect(data_dir):
    """Yield (image view, label index) pairs."""
    for source, n_views in (("pv", 2), ("pd", 6)):
        for c in os.listdir(os.path.join(data_dir, source)):
            folder = os.path.join(data_dir, source, c)
            for f in os.listdir(folder):
                img = load(os.path.join(folder, f))
                if img is not None:
                    for v in views(img, n_views):
                        yield v, CLASSES.index(c)
    folder = os.path.join(data_dir, "other")
    for f in os.listdir(folder):
        img = load(os.path.join(folder, f))
        if img is not None:
            for v in views(img, 2):
                yield v, CLASSES.index("other")
    for img in synthetic_other(150):
        yield img, CLASSES.index("other")


def build_backbone():
    inp = tf.keras.Input((IMG_SIZE, IMG_SIZE, 3))  # RGB scaled to [0, 1], like app.py feeds it
    x = tf.keras.layers.Rescaling(2.0, offset=-1.0)(inp)  # MobileNetV2 expects [-1, 1]
    base = tf.keras.applications.MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                                             include_top=False, pooling="avg", weights="imagenet")
    return tf.keras.Model(inp, base(x, training=False))


def features(backbone, items, chunk=256):
    """Extract backbone features chunk by chunk to keep memory low."""
    feats, labels, imgs = [], [], []
    for img, label in items:
        imgs.append(img)
        labels.append(label)
        if len(imgs) == chunk:
            feats.append(backbone.predict(np.stack(imgs).astype(np.float32) / 255.0, verbose=0))
            imgs = []
            print(f"{len(labels)} views", flush=True)
    if imgs:
        feats.append(backbone.predict(np.stack(imgs).astype(np.float32) / 255.0, verbose=0))
    return np.concatenate(feats), np.array(labels)


def main():
    data_dir = sys.argv[1]
    backbone = build_backbone()
    X, y = features(backbone, collect(data_dir))

    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]
    counts = np.bincount(y, minlength=len(CLASSES))
    class_weight = {i: len(y) / (len(CLASSES) * max(c, 1)) for i, c in enumerate(counts)}

    head = tf.keras.Sequential([
        tf.keras.Input((X.shape[1],)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(len(CLASSES), activation="softmax"),
    ])
    head.compile(tf.keras.optimizers.Adam(1e-3), "sparse_categorical_crossentropy", metrics=["accuracy"])
    head.fit(X, y, epochs=40, batch_size=64, validation_split=0.1, class_weight=class_weight,
             callbacks=[tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)], verbose=2)

    model = tf.keras.Model(backbone.input, head(backbone.output))
    model.save(OUT_PATH)
    print("saved", OUT_PATH)


def finetune(data_dir, epochs=6, trainable_layers=40):
    """Second stage: unfreeze the top of MobileNetV2 and train end to end.

    Field photos (PlantDoc) are repeated 3x because they are scarce but are
    what users actually upload.
    """
    load_size = IMG_SIZE + 32
    imgs, labels = [], []

    def add(path, label, repeat=1):
        img = load(path)
        if img is not None:
            img = cv2.resize(img, (load_size, load_size))
            imgs.extend([img] * repeat)
            labels.extend([label] * repeat)

    for source, repeat in (("pv", 1), ("pd", 3)):
        for c in os.listdir(os.path.join(data_dir, source)):
            folder = os.path.join(data_dir, source, c)
            for f in os.listdir(folder):
                add(os.path.join(folder, f), CLASSES.index(c), repeat)
    for f in os.listdir(os.path.join(data_dir, "other")):
        add(os.path.join(data_dir, "other", f), CLASSES.index("other"))
    for img in synthetic_other(150):
        imgs.append(cv2.resize(img, (load_size, load_size)))
        labels.append(CLASSES.index("other"))
    X, y = np.stack(imgs), np.array(labels)
    del imgs
    print(f"{len(y)} fine-tune images")

    def augment(img, label):
        img = tf.image.random_crop(img, (IMG_SIZE, IMG_SIZE, 3))
        img = tf.image.random_flip_left_right(img)
        img = tf.cast(img, tf.float32) / 255.0
        img = tf.image.random_brightness(img, 0.15)
        img = tf.image.random_saturation(img, 0.8, 1.2)
        return tf.clip_by_value(img, 0.0, 1.0), label

    ds = (tf.data.Dataset.from_tensor_slices((X, y)).shuffle(len(y), seed=0)
          .map(augment, num_parallel_calls=tf.data.AUTOTUNE).batch(32).prefetch(2))

    model = tf.keras.models.load_model(OUT_PATH, compile=False)
    base = next(l for l in model.layers if l.name.startswith("mobilenetv2"))
    base.trainable = True
    for layer in base.layers[:-trainable_layers]:
        layer.trainable = False
    for layer in base.layers:  # keep BatchNorm statistics from ImageNet
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False

    counts = np.bincount(y, minlength=len(CLASSES))
    class_weight = {i: len(y) / (len(CLASSES) * max(c, 1)) for i, c in enumerate(counts)}
    model.compile(tf.keras.optimizers.Adam(1e-5), "sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(ds, epochs=epochs, class_weight=class_weight, verbose=2)
    model.save(OUT_PATH)
    print("saved", OUT_PATH)


if __name__ == "__main__":
    if "--finetune" in sys.argv:
        finetune(sys.argv[1])
    else:
        main()
