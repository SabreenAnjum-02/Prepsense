"""
PrepSense runtime configuration.

Environment variables:
    PREPSENSE_DEV_MODE      — Set to "1" to disable heavyweight AI model loading.
                              TTS returns a beep stub, STT returns a stub transcript,
                              VAD always returns False. API starts in <2 seconds.
    PREPSENSE_TORCH_THREADS — Maximum number of CPU threads PyTorch may use for
                              inference (default: 2). Keeps the laptop responsive
                              while voice models are running.
"""

import os
import logging

logger = logging.getLogger(__name__)

DEV_MODE: bool = os.environ.get("PREPSENSE_DEV_MODE", "0") == "1"
TORCH_NUM_THREADS: int = int(os.environ.get("PREPSENSE_TORCH_THREADS", "2"))


def apply_torch_thread_limit():
    """Apply the configured thread limit to PyTorch, if PyTorch is importable."""
    try:
        import torch
        torch.set_num_threads(TORCH_NUM_THREADS)
        torch.set_num_interop_threads(max(1, TORCH_NUM_THREADS))
        logger.info(
            f"PyTorch threads limited to {TORCH_NUM_THREADS} "
            f"(intra-op={torch.get_num_threads()}, inter-op={torch.get_num_interop_threads()})"
        )
    except ImportError:
        pass
    except RuntimeError:
        # inter-op threads can only be set once; ignore if already set
        pass


if DEV_MODE:
    logger.info("PrepSense DEV_MODE is ON — AI voice models will NOT be loaded.")
