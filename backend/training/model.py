"""Deep Neural Network architecture + baseline ML models."""

from __future__ import annotations

from tensorflow import keras
from tensorflow.keras import layers  # noqa: F401


def build_dnn(input_dim: int, learning_rate: float = 1e-3, seed: int = 42) -> keras.Model:
    """Build the MLP used as the primary production model.

    Architecture (documented in README):
        Input
        Dense(256, relu) -> BatchNorm -> Dropout(0.30)
        Dense(128, relu) -> BatchNorm -> Dropout(0.25)
        Dense(64, relu)  -> Dropout(0.20)
        Dense(32, relu)  -> BatchNorm -> Dropout(0.20)
        Dense(1, linear)         # predicts log1p(revenue)

    Huber loss (delta=1) + L2 regularization make training robust to the
    extreme-revenue outliers present in real box-office data.
    """
    keras.utils.set_random_seed(seed)

    regularizer = keras.regularizers.l2(1e-4)

    model = keras.Sequential(
        [
            layers.Input(shape=(input_dim,)),
            layers.Dense(256, activation="relu", kernel_regularizer=regularizer),
            layers.BatchNormalization(),
            layers.Dropout(0.30),
            layers.Dense(128, activation="relu", kernel_regularizer=regularizer),
            layers.BatchNormalization(),
            layers.Dropout(0.25),
            layers.Dense(64, activation="relu", kernel_regularizer=regularizer),
            layers.Dropout(0.20),
            layers.Dense(32, activation="relu", kernel_regularizer=regularizer),
            layers.BatchNormalization(),
            layers.Dropout(0.20),
            layers.Dense(1, activation="linear"),
        ],
        name="revenue_dnn",
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.Huber(delta=1.0),
        metrics=["mae"],
    )
    return model


def train_dnn(
    x_train,
    y_train,
    x_val,
    y_val,
    input_dim: int,
    learning_rate: float,
    epochs: int,
    batch_size: int,
    seed: int,
    model_path: str | None = None,
    verbose: int = 1,
):
    """Train the DNN with EarlyStopping / ReduceLROnPlateau / ModelCheckpoint."""
    model = build_dnn(input_dim=input_dim, learning_rate=learning_rate, seed=seed)

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=25, restore_best_weights=True, verbose=verbose
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=8, min_lr=1e-6, verbose=verbose
        ),
    ]
    if model_path:
        callbacks.append(
            keras.callbacks.ModelCheckpoint(
                filepath=model_path,
                monitor="val_loss",
                save_best_only=True,
                save_weights_only=False,
                verbose=verbose,
            )
        )

    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=verbose,
    )
    return model, history
