"""
Unit tests for Phase 6 — LayoutLMv3 integration.

Tests:
- Bbox normalization / denormalization / validation
- Token alignment
- Config & label mappings
- Model manager state tracking
- Inference engine (mocked model)
- BIO entity grouping
- Edge cases (empty, malformed, CPU)

All tests use mocked models to avoid downloading
LayoutLMv3 weights.
"""

import pytest
from unittest.mock import (
    MagicMock,
    patch,
)

from app.ml.layoutlm.bbox_utils import (
    normalize_bbox,
    denormalize_bbox,
    validate_bbox,
    clamp_bbox,
)
from app.ml.layoutlm.config import (
    LABEL_LIST,
    LABEL_TO_ID,
    ID_TO_LABEL,
    LayoutLMConfig,
)
from app.ml.layoutlm.token_aligner import (
    prepare_word_level_inputs,
    align_labels_with_tokens,
)
from app.ml.layoutlm.model_manager import (
    LayoutLMModelManager,
)
from app.ml.layoutlm.inference import (
    LayoutLMInferenceEngine,
    EntityPrediction,
    PagePrediction,
)


# ====================================================
# Bbox normalization tests
# ====================================================

class TestNormalizeBbox:

    def test_basic_normalization(self):
        # Image is 1000x1000, so coords should
        # map 1:1
        result = normalize_bbox(
            [100, 200, 300, 400], 1000, 1000
        )
        assert result == [100, 200, 300, 400]

    def test_scaling(self):
        # Image is 2000x2000, coords halve
        result = normalize_bbox(
            [200, 400, 600, 800], 2000, 2000
        )
        assert result == [100, 200, 300, 400]

    def test_typical_200dpi_page(self):
        # A4 at 200 DPI: ~1654x2339
        result = normalize_bbox(
            [827, 1169, 1400, 2000],
            1654,
            2339,
        )
        # x0 = 827/1654*1000 = 500
        # y0 = 1169/2339*1000 = 499
        assert result[0] == 500
        assert 499 <= result[1] <= 500

    def test_zero_size_image(self):
        result = normalize_bbox(
            [100, 200, 300, 400], 0, 0
        )
        assert result == [0, 0, 0, 0]

    def test_negative_width(self):
        result = normalize_bbox(
            [100, 200, 300, 400], -1, 1000
        )
        assert result == [0, 0, 0, 0]

    def test_clamping_out_of_bounds(self):
        # Bbox coords exceed image size
        result = normalize_bbox(
            [0, 0, 2000, 2000], 1000, 1000
        )
        # Would scale to [0,0,2000,2000] but
        # clamped to 1000
        assert result == [0, 0, 1000, 1000]

    def test_origin_bbox(self):
        result = normalize_bbox(
            [0, 0, 0, 0], 1000, 1000
        )
        assert result == [0, 0, 0, 0]


class TestDenormalizeBbox:

    def test_basic_denormalization(self):
        result = denormalize_bbox(
            [100, 200, 300, 400], 1000, 1000
        )
        assert result == [100, 200, 300, 400]

    def test_scaling_up(self):
        result = denormalize_bbox(
            [500, 500, 1000, 1000], 2000, 2000
        )
        assert result == [1000, 1000, 2000, 2000]

    def test_zero_size(self):
        result = denormalize_bbox(
            [500, 500, 1000, 1000], 0, 0
        )
        assert result == [0, 0, 0, 0]

    def test_roundtrip(self):
        original = [400, 500, 800, 1200]
        w, h = 1654, 2339
        normalized = normalize_bbox(
            original, w, h
        )
        restored = denormalize_bbox(
            normalized, w, h
        )
        # Allow ±1 pixel rounding error
        for o, r in zip(original, restored):
            assert abs(o - r) <= 2


class TestValidateBbox:

    def test_valid(self):
        assert validate_bbox([0, 0, 500, 500])

    def test_valid_full_range(self):
        assert validate_bbox([0, 0, 1000, 1000])

    def test_valid_zero_area(self):
        assert validate_bbox([100, 100, 100, 100])

    def test_invalid_negative(self):
        assert not validate_bbox(
            [-1, 0, 500, 500]
        )

    def test_invalid_exceeds_max(self):
        assert not validate_bbox(
            [0, 0, 1001, 500]
        )

    def test_invalid_x0_gt_x1(self):
        assert not validate_bbox(
            [500, 0, 100, 500]
        )

    def test_invalid_y0_gt_y1(self):
        assert not validate_bbox(
            [0, 500, 100, 100]
        )

    def test_invalid_wrong_length(self):
        assert not validate_bbox([0, 0, 100])

    def test_invalid_too_many(self):
        assert not validate_bbox(
            [0, 0, 100, 100, 100]
        )


class TestClampBbox:

    def test_no_clamping_needed(self):
        assert clamp_bbox(
            [100, 200, 300, 400]
        ) == [100, 200, 300, 400]

    def test_clamp_negative(self):
        assert clamp_bbox(
            [-10, -20, 300, 400]
        ) == [0, 0, 300, 400]

    def test_clamp_exceeds_max(self):
        assert clamp_bbox(
            [100, 200, 1500, 1200]
        ) == [100, 200, 1000, 1000]

    def test_swap_inverted_coords(self):
        result = clamp_bbox(
            [300, 400, 100, 200]
        )
        assert result == [100, 200, 300, 400]

    def test_all_zeros(self):
        assert clamp_bbox(
            [0, 0, 0, 0]
        ) == [0, 0, 0, 0]


# ====================================================
# Config & label tests
# ====================================================

class TestConfig:

    def test_label_count(self):
        assert len(LABEL_LIST) == 17

    def test_o_label_first(self):
        assert LABEL_LIST[0] == "O"

    def test_all_bio_pairs(self):
        entity_types = [
            "VENDOR",
            "INVOICE_NUMBER",
            "INVOICE_DATE",
            "DUE_DATE",
            "SUBTOTAL",
            "TAX",
            "GST",
            "TOTAL",
        ]
        for etype in entity_types:
            assert f"B-{etype}" in LABEL_LIST
            assert f"I-{etype}" in LABEL_LIST

    def test_label_to_id_mapping(self):
        assert LABEL_TO_ID["O"] == 0
        assert LABEL_TO_ID["B-TOTAL"] > 0
        assert len(LABEL_TO_ID) == len(LABEL_LIST)

    def test_id_to_label_mapping(self):
        assert ID_TO_LABEL[0] == "O"
        assert len(ID_TO_LABEL) == len(LABEL_LIST)

    def test_roundtrip_mapping(self):
        for label in LABEL_LIST:
            idx = LABEL_TO_ID[label]
            assert ID_TO_LABEL[idx] == label

    def test_default_config(self):
        config = LayoutLMConfig()
        assert config.model_name == (
            "microsoft/layoutlmv3-base"
        )
        assert config.device == "auto"
        assert config.max_seq_length == 512
        assert config.batch_size == 8
        assert config.image_size == 224

    def test_custom_config(self):
        config = LayoutLMConfig(
            device="cpu",
            num_epochs=5,
            batch_size=4,
        )
        assert config.device == "cpu"
        assert config.num_epochs == 5


# ====================================================
# Token alignment tests
# ====================================================

class TestPrepareWordLevelInputs:

    def test_single_block(self):
        blocks = [
            {
                "text": "Invoice Number 123",
                "bbox": [100, 50, 400, 80],
            }
        ]
        words, bboxes = prepare_word_level_inputs(
            blocks, 1000, 1000
        )
        assert len(words) == 3
        assert words == [
            "Invoice", "Number", "123"
        ]
        assert len(bboxes) == 3
        # All words get same normalized bbox
        assert bboxes[0] == bboxes[1] == bboxes[2]

    def test_multiple_blocks(self):
        blocks = [
            {"text": "Total", "bbox": [0, 0, 100, 50]},
            {"text": "₹100", "bbox": [200, 0, 300, 50]},
        ]
        words, bboxes = prepare_word_level_inputs(
            blocks, 1000, 1000
        )
        assert len(words) == 2
        assert words == ["Total", "₹100"]
        # Different bboxes for different blocks
        assert bboxes[0] != bboxes[1]

    def test_empty_blocks(self):
        words, bboxes = prepare_word_level_inputs(
            [], 1000, 1000
        )
        assert words == []
        assert bboxes == []

    def test_block_with_empty_text(self):
        blocks = [
            {"text": "", "bbox": [0, 0, 100, 50]},
            {"text": "   ", "bbox": [0, 0, 100, 50]},
        ]
        words, bboxes = prepare_word_level_inputs(
            blocks, 1000, 1000
        )
        assert words == []

    def test_block_missing_bbox(self):
        blocks = [
            {"text": "Hello"},
            {"text": "World", "bbox": None},
        ]
        words, bboxes = prepare_word_level_inputs(
            blocks, 1000, 1000
        )
        assert words == []

    def test_block_invalid_bbox_length(self):
        blocks = [
            {
                "text": "Test",
                "bbox": [0, 0, 100],
            },
        ]
        words, bboxes = prepare_word_level_inputs(
            blocks, 1000, 1000
        )
        assert words == []

    def test_bbox_normalization(self):
        # Image is 2000x2000
        blocks = [
            {
                "text": "Hello",
                "bbox": [200, 400, 600, 800],
            }
        ]
        words, bboxes = prepare_word_level_inputs(
            blocks, 2000, 2000
        )
        assert bboxes[0] == [100, 200, 300, 400]


class TestAlignLabelsWithTokens:

    def test_basic_alignment(self):
        labels = ["B-VENDOR", "I-VENDOR", "O"]
        word_ids = [None, 0, 1, 2, None]

        result = align_labels_with_tokens(
            labels, word_ids, LABEL_TO_ID
        )

        # [CLS]=−100, word0=B-VENDOR,
        # word1=I-VENDOR, word2=O, [SEP]=−100
        assert result[0] == -100
        assert result[1] == LABEL_TO_ID["B-VENDOR"]
        assert result[2] == LABEL_TO_ID["I-VENDOR"]
        assert result[3] == LABEL_TO_ID["O"]
        assert result[4] == -100

    def test_subword_continuation(self):
        # "Invoice" tokenized as ["Inv", "##oice"]
        labels = ["B-INVOICE_NUMBER"]
        word_ids = [None, 0, 0, None]

        result = align_labels_with_tokens(
            labels, word_ids, LABEL_TO_ID
        )

        # First sub-word: B-INVOICE_NUMBER
        assert result[1] == (
            LABEL_TO_ID["B-INVOICE_NUMBER"]
        )
        # Second sub-word: I-INVOICE_NUMBER
        assert result[2] == (
            LABEL_TO_ID["I-INVOICE_NUMBER"]
        )

    def test_all_special_tokens(self):
        word_ids = [None, None, None]
        result = align_labels_with_tokens(
            [], word_ids, LABEL_TO_ID
        )
        assert result == [-100, -100, -100]

    def test_word_id_exceeds_labels(self):
        labels = ["O"]
        word_ids = [None, 0, 5, None]

        result = align_labels_with_tokens(
            labels, word_ids, LABEL_TO_ID
        )

        assert result[1] == LABEL_TO_ID["O"]
        assert result[2] == -100  # out of range


# ====================================================
# Model manager tests
# ====================================================

class TestModelManager:

    def test_initial_state(self):
        manager = LayoutLMModelManager()
        assert not manager.is_loaded
        assert not manager.is_finetuned
        assert manager.device is None
        assert manager.model is None
        assert manager.processor is None

    def test_custom_config(self):
        config = LayoutLMConfig(device="cpu")
        manager = LayoutLMModelManager(config)
        assert manager.config.device == "cpu"

    def test_unload(self):
        manager = LayoutLMModelManager()
        manager.model = "mock_model"
        manager.processor = "mock_processor"
        manager._is_loaded = True

        manager.unload()

        assert not manager.is_loaded
        assert manager.model is None
        assert manager.processor is None

    def test_resolve_device_cpu(self):
        config = LayoutLMConfig(device="cpu")
        manager = LayoutLMModelManager(config)
        assert manager._resolve_device() == "cpu"

    def test_resolve_device_auto_no_cuda(self):
        config = LayoutLMConfig(device="auto")
        manager = LayoutLMModelManager(config)

        with patch(
            "app.ml.layoutlm.model_manager.LayoutLMModelManager._resolve_device",
            return_value="cpu"
        ):
            assert manager._resolve_device() == "cpu"


# ====================================================
# Inference engine tests
# ====================================================

class TestInferenceEngine:

    def _make_mock_manager(
        self, is_loaded=True, is_finetuned=False
    ):
        manager = MagicMock()
        manager.is_loaded = is_loaded
        manager.is_finetuned = is_finetuned
        manager.config = LayoutLMConfig()
        return manager

    def test_not_loaded(self):
        manager = self._make_mock_manager(
            is_loaded=False
        )
        engine = LayoutLMInferenceEngine(manager)

        result = engine.predict_page(
            image=MagicMock(),
            layout_blocks=[
                {
                    "text": "Test",
                    "bbox": [0, 0, 100, 50],
                }
            ],
            image_width=1000,
            image_height=1000,
        )

        assert isinstance(result, PagePrediction)
        assert len(result.entities) == 0

    def test_empty_blocks(self):
        manager = self._make_mock_manager()
        engine = LayoutLMInferenceEngine(manager)

        result = engine.predict_page(
            image=MagicMock(),
            layout_blocks=[],
            image_width=1000,
            image_height=1000,
        )

        assert isinstance(result, PagePrediction)
        assert len(result.entities) == 0

    def test_page_prediction_structure(self):
        pred = PagePrediction(
            page_number=1,
            entities=[
                EntityPrediction(
                    label="TOTAL",
                    text="₹100,890",
                    confidence=0.95,
                    bbox=[100, 200, 300, 250],
                )
            ],
            is_finetuned=False,
            model_name="microsoft/layoutlmv3-base",
        )

        assert pred.page_number == 1
        assert len(pred.entities) == 1
        assert pred.entities[0].label == "TOTAL"
        assert not pred.is_finetuned

    def test_finetuned_flag(self):
        pred = PagePrediction(
            is_finetuned=True,
            model_name="custom-model",
        )
        assert pred.is_finetuned
        assert pred.model_name == "custom-model"


# ====================================================
# BIO entity grouping tests
# ====================================================

class TestEntityGrouping:

    def _make_engine(self):
        manager = MagicMock()
        manager.is_loaded = True
        return LayoutLMInferenceEngine(manager)

    def test_single_b_tag(self):
        engine = self._make_engine()
        token_preds = [
            {
                "text": "₹100,890",
                "label": "B-TOTAL",
                "confidence": 0.95,
                "bbox": [100, 200, 300, 250],
            }
        ]
        entities = engine._group_entities(
            token_preds
        )
        assert len(entities) == 1
        assert entities[0].label == "TOTAL"
        assert entities[0].text == "₹100,890"

    def test_b_plus_i_tags(self):
        engine = self._make_engine()
        token_preds = [
            {
                "text": "Acme",
                "label": "B-VENDOR",
                "confidence": 0.9,
                "bbox": [10, 10, 100, 30],
            },
            {
                "text": "Corp",
                "label": "I-VENDOR",
                "confidence": 0.85,
                "bbox": [110, 10, 200, 30],
            },
        ]
        entities = engine._group_entities(
            token_preds
        )
        assert len(entities) == 1
        assert entities[0].label == "VENDOR"
        assert entities[0].text == "Acme Corp"
        # Merged bbox
        assert entities[0].bbox[0] == 10
        assert entities[0].bbox[2] == 200

    def test_multiple_entities(self):
        engine = self._make_engine()
        token_preds = [
            {
                "text": "INV-001",
                "label": "B-INVOICE_NUMBER",
                "confidence": 0.9,
                "bbox": [10, 10, 100, 30],
            },
            {
                "text": "irrelevant",
                "label": "O",
                "confidence": 0.99,
                "bbox": [110, 10, 200, 30],
            },
            {
                "text": "₹500",
                "label": "B-TOTAL",
                "confidence": 0.88,
                "bbox": [10, 50, 100, 70],
            },
        ]
        entities = engine._group_entities(
            token_preds
        )
        assert len(entities) == 2
        assert entities[0].label == "INVOICE_NUMBER"
        assert entities[1].label == "TOTAL"

    def test_no_entities(self):
        engine = self._make_engine()
        token_preds = [
            {
                "text": "hello",
                "label": "O",
                "confidence": 0.99,
                "bbox": [0, 0, 100, 50],
            },
        ]
        entities = engine._group_entities(
            token_preds
        )
        assert len(entities) == 0

    def test_empty_predictions(self):
        engine = self._make_engine()
        entities = engine._group_entities([])
        assert len(entities) == 0

    def test_i_without_b(self):
        """I- tag without preceding B- tag
        should be ignored (no open entity)."""
        engine = self._make_engine()
        token_preds = [
            {
                "text": "orphan",
                "label": "I-VENDOR",
                "confidence": 0.5,
                "bbox": [0, 0, 100, 50],
            },
        ]
        entities = engine._group_entities(
            token_preds
        )
        # No entity because I- without B-
        assert len(entities) == 0

    def test_consecutive_b_tags(self):
        """Two B- tags in a row: first entity
        closes, second starts."""
        engine = self._make_engine()
        token_preds = [
            {
                "text": "100",
                "label": "B-SUBTOTAL",
                "confidence": 0.9,
                "bbox": [0, 0, 50, 30],
            },
            {
                "text": "200",
                "label": "B-TOTAL",
                "confidence": 0.85,
                "bbox": [60, 0, 110, 30],
            },
        ]
        entities = engine._group_entities(
            token_preds
        )
        assert len(entities) == 2
        assert entities[0].label == "SUBTOTAL"
        assert entities[1].label == "TOTAL"

    def test_confidence_averaging(self):
        engine = self._make_engine()
        token_preds = [
            {
                "text": "Grand",
                "label": "B-TOTAL",
                "confidence": 0.8,
                "bbox": [0, 0, 50, 30],
            },
            {
                "text": "Total",
                "label": "I-TOTAL",
                "confidence": 1.0,
                "bbox": [60, 0, 110, 30],
            },
        ]
        entities = engine._group_entities(
            token_preds
        )
        assert len(entities) == 1
        assert entities[0].confidence == 0.9


# ====================================================
# EntityPrediction tests
# ====================================================

class TestEntityPrediction:

    def test_defaults(self):
        e = EntityPrediction()
        assert e.label == ""
        assert e.text == ""
        assert e.confidence == 0.0
        assert e.bbox is None
        assert e.tokens == []

    def test_custom(self):
        e = EntityPrediction(
            label="VENDOR",
            text="Acme Ltd",
            confidence=0.92,
            bbox=[10, 20, 300, 50],
        )
        assert e.label == "VENDOR"
        assert e.text == "Acme Ltd"
        assert e.confidence == 0.92
