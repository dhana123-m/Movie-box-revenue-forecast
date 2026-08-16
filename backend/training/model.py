"""Deep Neural Network architecture + baseline ML models.

The architecture is fully configurable so the hyper-parameter tuning script
(training/hyperparameter_tuning.py) can sweep units / dropout / L2 / learning
rate while keeping the exact same building blocks.
"""

from __future__ import annotations

from tensorflow import keras
from tensorflow.keras import layers  # noqa: F401

DEFAULT_UNITS = (512, 256, 128, 64)
DEFAULT_DROPOUTS = (0.35, 0.30, 0.25, 0.20)
# BatchNorm after every hidden layer (chosen by hyper-parameter tuning).
DEFAULT_BATCH_NORM = (True, True, True, True)
DEFAULT_L2 = 1e-4


def build_dnn(
    input_dim: int,
    learning_rate: float = 1e-3,
    seed: int = 42,
    units: tuple[int, ...] = DEFAULT_UNITS,
    dropouts: tuple[float, ...] = DEFAULT_DROPOUTS,
    batch_norm: tuple[bool, ...] = DEFAULT_BATCH_NORM,
    l2: float = DEFAULT_L2,
) -> keras.Model:
    """Build the MLP used as the primary production model.

    Default architecture (chosen by hyper-parameter tuning — see
    models/evaluation/tuning_results.*):
        Input
        Dense(512, relu) -> BatchNorm -> Dropout(0.35)
        Dense(256, relu) -> BatchNorm -> Dropout(0.30)
        Dense(128, relu) -> BatchNorm -> Dropout(0.25)
        Dense(64, relu)  -> BatchNorm -> Dropout(0.20)
        Dense(1, linear)         # predicts log1p(revenue)

    Huber loss (delta=1) + L2 regularization make training robust to the
    extreme-revenue outliers present in real box-office data.
    """
    keras.utils.set_random_seed(seed)

    layers_spec = list(zip(units, dropouts, batch_norm))

    regularizer = keras.regularizers.l2(l2)
    model = keras.Sequential(name="revenue_dnn")
    model.add(layers.Input(shape=(input_dim,)))

    for n_units, dropout, use_bn in layers_spec:
        model.add(layers.Dense(n_units, activation="relu", kernel_regularizer=regularizer))
        if use_bn:
            model.add(layers.BatchNormalization())
        model.add(layers.Dropout(dropout))

    model.add(layers.Dense(1, activation="linear"))

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=keras.losses.Huber(delta=1.0),
        metrics=["mae"],
    )
    return model


def describe_architecture(
    units: tuple[int, ...] = DEFAULT_UNITS,
    dropouts: tuple[float, ...] = DEFAULT_DROPOUTS,
    batch_norm: tuple[bool, ...] = DEFAULT_BATCH_NORM,
    l2: float = DEFAULT_L2,
) -> list[str]:
    """Human-readable layer list for metrics.json / the UI."""
    labels = ["Input"]
    for n_units, dropout, use_bn in zip(units, dropouts, batch_norm):
        block = f"Dense({n_units}, relu)"
        if use_bn:
            block += " + BatchNorm"
        block += f" + Dropout({dropout:.2f})"
        labels.append(block)
    labels.append("Dense(1, linear)")
    return labels


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
    units: tuple[int, ...] = DEFAULT_UNITS,
    dropouts: tuple[float, ...] = DEFAULT_DROPOUTS,
    batch_norm: tuple[bool, ...] = DEFAULT_BATCH_NORM,
    l2: float = DEFAULT_L2,
):
    """Train the DNN with EarlyStopping / ReduceLROnPlateau / ModelCheckpoint."""
    model = build_dnn(
        input_dim=input_dim,
        learning_rate=learning_rate,
        seed=seed,
        units=units,
        dropouts=dropouts,
        batch_norm=batch_norm,
        l2=l2,
    )

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
