"""LettuceDetect Hallucination Detector service.

Integrates directly with the official KRLabsOrg LettuceDetect model.
Loads the model once at startup and provides thread-safe inference.
"""

import logging
import time
from typing import Any
from app.config import settings
from app.schemas.verification import (
    HallucinationSpan,
    VerificationSummary,
)

logger = logging.getLogger(__name__)


class DetectorService:
    """Service wrapping LettuceDetect HallucinationDetector."""

    def __init__(self) -> None:
        self._detector: Any = None
        self._model_path: str = settings.model_path
        self._device: str = settings.device
        self._load_error: str | None = None
        self._is_loading: bool = False

    @property
    def is_loaded(self) -> bool:
        """Return True if model is loaded and ready for inference."""
        return self._detector is not None

    @property
    def model_path(self) -> str:
        """Return the current model path or identifier."""
        return self._model_path

    @property
    def device(self) -> str:
        """Return device used for inference."""
        return self._device

    def load_model(self) -> None:
        """Load the LettuceDetect model into memory.

        Should be called once during application startup.
        """
        if self._detector is not None:
            logger.info("Detector model is already loaded.")
            return

        self._is_loading = True
        logger.info(
            "Loading LettuceDetect model '%s' on device '%s'...",
            self._model_path,
            self._device,
        )
        t0 = time.time()
        try:
            from lettucedetect.models.inference import HallucinationDetector

            self._detector = HallucinationDetector(
                method=settings.detector_method,
                model_path=self._model_path,
                device=self._device,
                max_length=settings.max_length,
            )
            elapsed = time.time() - t0
            self._load_error = None
            logger.info(
                "LettuceDetect model loaded successfully in %.2f seconds.", elapsed
            )
        except Exception as e:
            self._detector = None
            self._load_error = str(e)
            logger.error("Failed to load LettuceDetect model: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to load detector model: {e}") from e
        finally:
            self._is_loading = False

    def predict(
        self,
        context: list[str],
        answer: str,
        question: str | None = None,
        min_confidence: float = 0.0,
    ) -> tuple[list[HallucinationSpan], VerificationSummary, float]:
        """Run hallucination detection over the provided context and answer.

        Args:
            context: List of reference context passages.
            answer: Model-generated answer to inspect.
            question: Optional user question/query.
            min_confidence: Confidence threshold to filter spans (0.0 to 1.0).

        Returns:
            Tuple of:
                - List of HallucinationSpan objects
                - VerificationSummary object
                - Execution time in milliseconds
        """
        if not self.is_loaded:
            raise RuntimeError(
                "Detector model is not loaded. Call load_model() first or check startup logs."
            )

        if not answer or not answer.strip():
            raise ValueError("Answer text cannot be empty.")

        if not context:
            raise ValueError("Context cannot be empty.")

        t0 = time.perf_counter()
        try:
            raw_predictions = self._detector.predict(
                context=context,
                question=question,
                answer=answer,
                output_format="spans",
                min_confidence=min_confidence,
            )
        except Exception as e:
            logger.error("Error during detector inference: %s", e, exc_info=True)
            raise RuntimeError(f"Detector inference error: {e}") from e

        execution_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Parse spans into schema objects
        spans: list[HallucinationSpan] = []
        max_conf: float | None = None

        for item in raw_predictions:
            start = item.get("start", 0)
            end = item.get("end", 0)
            text = item.get("text", "")
            confidence = item.get("confidence")
            category = item.get("category")

            if confidence is not None:
                confidence = float(confidence)
                if max_conf is None or confidence > max_conf:
                    max_conf = confidence

            spans.append(
                HallucinationSpan(
                    start=start,
                    end=end,
                    text=text,
                    confidence=confidence,
                    category=category,
                )
            )

        # Compute summary
        span_count = len(spans)
        is_hallucinated = span_count > 0

        if is_hallucinated:
            verdict = "HALLUCINATED"
            conf_str = f" (max confidence: {max_conf:.2%})" if max_conf else ""
            message = (
                f"Detected {span_count} hallucinated span(s) not supported by reference context{conf_str}."
            )
        else:
            verdict = "CLEAN"
            message = "Answer is fully supported by the provided reference context."

        summary = VerificationSummary(
            is_hallucinated=is_hallucinated,
            span_count=span_count,
            max_confidence=max_conf,
            verdict=verdict,
            message=message,
        )

        return spans, summary, execution_time_ms


# Global singleton instance for application use
detector_service = DetectorService()

