from __future__ import annotations

from dataclasses import dataclass

from transformers import AutoTokenizer, PreTrainedTokenizerBase


DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class TokenCounter:
    """
    Thin wrapper around a HuggingFace tokenizer to count tokens.

    Uses the MiniLM tokenizer specified in the project spec by default.
    """

    model_name: str = DEFAULT_MODEL_NAME
    tokenizer: PreTrainedTokenizerBase | None = None

    def __post_init__(self) -> None:
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in the given text.

        The count includes special tokens added by the tokenizer.
        """
        if not text:
            return 0
        encoded = self.tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
            return_attention_mask=False,
            return_token_type_ids=False,
        )
        return len(encoded["input_ids"])


__all__ = ["TokenCounter", "DEFAULT_MODEL_NAME"]

