"""
Architecture factory for the cross-architecture robustness study (Priority 2).

Maps a ``--model`` name to a SenseFi UT-HAR model class. All current choices
consume the same processed-tensor input shape as the LeNet baseline,
``(N, 1, 250, 90)`` — the ResNet variants carry their own input reshape head —
so the existing data loader, FGSM/PGD attack math, and safety-proxy metric code
work unchanged. Temporal models (RNN/GRU/LSTM/BiLSTM) instead expect
``(N, 250, 90)`` and reshape internally via ``x.view(-1, 250, 90)``; they are
listed here for completeness but are out of scope until after the ResNet stage
is reviewed.

Requires the SenseFi clone directory (``third_party/WiFi-CSI-Sensing-Benchmark``)
to already be importable on ``sys.path`` before ``build_model`` is called; the
existing pipeline scripts add it before constructing the model.
"""

from __future__ import annotations

# Canonical name -> SenseFi UT_HAR_model attribute. Aliases included.
_MODEL_ALIASES = {
    "lenet": "UT_HAR_LeNet",
    "resnet": "UT_HAR_ResNet18",
    "resnet18": "UT_HAR_ResNet18",
    "resnet50": "UT_HAR_ResNet50",
    "resnet101": "UT_HAR_ResNet101",
    # Temporal models (out of scope for the ResNet stage; expect (N,250,90)):
    "rnn": "UT_HAR_RNN",
    "gru": "UT_HAR_GRU",
    "lstm": "UT_HAR_LSTM",
    "bilstm": "UT_HAR_BiLSTM",
    # Attention-based model: ViT-style transformer. Consumes (N,1,250,90)
    # (patch-embeds the 250x90 window); attention weights are not exposed.
    "vit": "UT_HAR_ViT",
    "transformer": "UT_HAR_ViT",
    "attention": "UT_HAR_ViT",
}

# Choices that consume the LeNet-style (N,1,250,90) processed-tensor input.
CNN_LIKE_INPUT = {"lenet", "resnet", "resnet18", "resnet50", "resnet101",
                  "vit", "transformer", "attention"}


def normalize_model_name(model_name: str) -> str:
    return str(model_name).strip().lower().replace("-", "").replace("_", "")


def available_models() -> list[str]:
    return sorted(_MODEL_ALIASES.keys())


def build_model(model_name: str):
    """Instantiate a SenseFi UT-HAR model by name.

    The default ``lenet`` returns exactly ``UT_HAR_LeNet()`` so existing
    behavior is unchanged when callers omit ``--model``.
    """
    key = normalize_model_name(model_name)
    if key not in _MODEL_ALIASES:
        raise ValueError(
            f"Unknown model '{model_name}'. Available: {available_models()}"
        )
    import UT_HAR_model as M  # provided by the SenseFi clone (must be on sys.path)

    factory = getattr(M, _MODEL_ALIASES[key])
    return factory()
