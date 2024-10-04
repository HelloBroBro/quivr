import os
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from megaparse.config import MegaparseConfig
from sqlmodel import SQLModel

from quivr_core.base_config import QuivrBaseConfig
from quivr_core.processor.splitter import SplitterConfig
from quivr_core.prompts import CustomPromptsModel


class BrainConfig(QuivrBaseConfig):
    brain_id: UUID | None = None
    name: str

    @property
    def id(self) -> UUID | None:
        return self.brain_id


class DefaultRerankers(str, Enum):
    COHERE = "cohere"
    JINA = "jina"

    @property
    def default_model(self) -> str:
        # Mapping of suppliers to their default models
        return {
            self.COHERE: "rerank-multilingual-v3.0",
            self.JINA: "jina-reranker-v2-base-multilingual",
        }[self]


class DefaultModelSuppliers(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    META = "meta"
    MISTRAL = "mistral"
    GROQ = "groq"


class LLMConfig(QuivrBaseConfig):
    context: int | None = None
    tokenizer_hub: str | None = None


class LLMModelConfig:
    _model_defaults: Dict[DefaultModelSuppliers, Dict[str, LLMConfig]] = {
        DefaultModelSuppliers.OPENAI: {
            "gpt-4o": LLMConfig(context=128000, tokenizer_hub="Xenova/gpt-4o"),
            "gpt-4o-mini": LLMConfig(context=128000, tokenizer_hub="Xenova/gpt-4o"),
            "gpt-4-turbo": LLMConfig(context=128000, tokenizer_hub="Xenova/gpt-4"),
            "gpt-4": LLMConfig(context=8192, tokenizer_hub="Xenova/gpt-4"),
            "gpt-3.5-turbo": LLMConfig(
                context=16385, tokenizer_hub="Xenova/gpt-3.5-turbo"
            ),
            "text-embedding-3-large": LLMConfig(
                context=8191, tokenizer_hub="Xenova/text-embedding-ada-002"
            ),
            "text-embedding-3-small": LLMConfig(
                context=8191, tokenizer_hub="Xenova/text-embedding-ada-002"
            ),
            "text-embedding-ada-002": LLMConfig(
                context=8191, tokenizer_hub="Xenova/text-embedding-ada-002"
            ),
        },
        DefaultModelSuppliers.ANTHROPIC: {
            "claude-3-5-sonnet": LLMConfig(
                context=200000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
            "claude-3-opus": LLMConfig(
                context=200000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
            "claude-3-sonnet": LLMConfig(
                context=200000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
            "claude-3-haiku": LLMConfig(
                context=200000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
            "claude-2-1": LLMConfig(
                context=200000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
            "claude-2-0": LLMConfig(
                context=100000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
            "claude-instant-1-2": LLMConfig(
                context=100000, tokenizer_hub="Xenova/claude-tokenizer"
            ),
        },
        DefaultModelSuppliers.META: {
            "llama-3.1": LLMConfig(
                context=128000, tokenizer_hub="Xenova/Meta-Llama-3.1-Tokenizer"
            ),
            "llama-3": LLMConfig(
                context=8192, tokenizer_hub="Xenova/llama3-tokenizer-new"
            ),
            "llama-2": LLMConfig(context=4096, tokenizer_hub="Xenova/llama2-tokenizer"),
            "code-llama": LLMConfig(
                context=16384, tokenizer_hub="Xenova/llama-code-tokenizer"
            ),
        },
        DefaultModelSuppliers.GROQ: {
            "llama-3.1": LLMConfig(
                context=128000, tokenizer_hub="Xenova/Meta-Llama-3.1-Tokenizer"
            ),
            "llama-3": LLMConfig(
                context=8192, tokenizer_hub="Xenova/llama3-tokenizer-new"
            ),
            "llama-2": LLMConfig(context=4096, tokenizer_hub="Xenova/llama2-tokenizer"),
            "code-llama": LLMConfig(
                context=16384, tokenizer_hub="Xenova/llama-code-tokenizer"
            ),
        },
        DefaultModelSuppliers.MISTRAL: {
            "mistral-large": LLMConfig(
                context=128000, tokenizer_hub="Xenova/mistral-tokenizer-v3"
            ),
            "mistral-small": LLMConfig(
                context=128000, tokenizer_hub="Xenova/mistral-tokenizer-v3"
            ),
            "mistral-nemo": LLMConfig(
                context=128000, tokenizer_hub="Xenova/Mistral-Nemo-Instruct-Tokenizer"
            ),
            "codestral": LLMConfig(
                context=32000, tokenizer_hub="Xenova/mistral-tokenizer-v3"
            ),
        },
    }

    @classmethod
    def get_supplier_by_model_name(cls, model: str) -> DefaultModelSuppliers | None:
        # Iterate over the suppliers and their models
        for supplier, models in cls._model_defaults.items():
            # Check if the model name or a base part of the model name is in the supplier's models
            for base_model_name in models:
                if model.startswith(base_model_name):
                    return supplier
        # Return None if no supplier matches the model name
        return None

    @classmethod
    def get_llm_model_config(
        cls, supplier: DefaultModelSuppliers, model_name: str
    ) -> Optional[LLMConfig]:
        """Retrieve the LLMConfig (context and tokenizer_hub) for a given supplier and model."""
        supplier_defaults = cls._model_defaults.get(supplier)
        if not supplier_defaults:
            return None

        # Use startswith logic for matching model names
        for key, config in supplier_defaults.items():
            if model_name.startswith(key):
                return config

        return None


class LLMEndpointConfig(QuivrBaseConfig):
    supplier: DefaultModelSuppliers = DefaultModelSuppliers.OPENAI
    model: str = "gpt-3.5-turbo-0125"
    context_length: int | None = None
    tokenizer_hub: str | None = None
    llm_base_url: str | None = None
    env_variable_name: str = f"{supplier.upper()}_API_KEY"
    llm_api_key: str | None = None
    max_input_tokens: int = 2000
    max_output_tokens: int = 2000
    temperature: float = 0.7
    streaming: bool = True
    prompt: CustomPromptsModel | None = None

    _FALLBACK_TOKENIZER = "cl100k_base"

    @property
    def fallback_tokenizer(self) -> str:
        return self._FALLBACK_TOKENIZER

    def __init__(self, **data):
        super().__init__(**data)
        self.set_llm_model_config()
        self.set_api_key()

    def set_api_key(self, force_reset: bool = False):
        # Check if the corresponding API key environment variable is set
        if not self.llm_api_key or force_reset:
            self.llm_api_key = os.getenv(self.env_variable_name)

        if not self.llm_api_key:
            raise ValueError(
                f"The API key for supplier '{self.supplier}' is not set. "
                f"Please set the environment variable: {self.env_variable_name}"
            )

    def set_llm_model_config(self):
        # Automatically set context_length and tokenizer_hub based on the supplier and model
        llm_model_config = LLMModelConfig.get_llm_model_config(
            self.supplier, self.model
        )
        if llm_model_config:
            self.context_length = llm_model_config.context
            self.tokenizer_hub = llm_model_config.tokenizer_hub

    def set_llm_model(self, model: str):
        supplier = LLMModelConfig.get_supplier_by_model_name(model)
        if supplier is None:
            raise ValueError(
                f"Cannot find the corresponding supplier for model {model}"
            )
        self.supplier = supplier
        self.model = model

        self.set_llm_model_config()
        self.set_api_key(force_reset=True)

    def set_from_sqlmodel(self, sqlmodel: SQLModel, mapping: Dict[str, str]):
        """
        Set attributes in LLMEndpointConfig from Model attributes using a field mapping.

        :param model_instance: An instance of the Model class.
        :param mapping: A dictionary that maps Model fields to LLMEndpointConfig fields.
                        Example: {"max_input": "max_input_tokens", "env_variable_name": "env_variable_name"}
        """
        for model_field, llm_field in mapping.items():
            if hasattr(sqlmodel, model_field) and hasattr(self, llm_field):
                setattr(self, llm_field, getattr(sqlmodel, model_field))
            else:
                raise AttributeError(
                    f"Invalid mapping: {model_field} or {llm_field} does not exist."
                )


# Cannot use Pydantic v2 field_validator because of conflicts with pydantic v1 still in use in LangChain
class RerankerConfig(QuivrBaseConfig):
    supplier: DefaultRerankers | None = None
    model: str | None = None
    top_n: int = 5
    api_key: str | None = None

    def __init__(self, **data):
        super().__init__(**data)  # Call Pydantic's BaseModel init
        self.validate_model()  # Automatically call external validation

    def validate_model(self):
        # If model is not provided, get default model based on supplier
        if self.model is None and self.supplier is not None:
            self.model = self.supplier.default_model

        # Check if the corresponding API key environment variable is set
        if self.supplier:
            api_key_var = f"{self.supplier.upper()}_API_KEY"
            self.api_key = os.getenv(api_key_var)

            if self.api_key is None:
                raise ValueError(
                    f"The API key for supplier '{self.supplier}' is not set. "
                    f"Please set the environment variable: {api_key_var}"
                )


class NodeConfig(QuivrBaseConfig):
    name: str
    # config: QuivrBaseConfig  # This can be any config like RerankerConfig or LLMEndpointConfig
    edges: List[str]  # List of names of other nodes this node links to


class WorkflowConfig(QuivrBaseConfig):
    name: str
    nodes: List[NodeConfig]


class RetrievalConfig(QuivrBaseConfig):
    reranker_config: RerankerConfig = RerankerConfig()
    llm_config: LLMEndpointConfig = LLMEndpointConfig()
    max_history: int = 10
    max_files: int = 20
    prompt: str | None = None
    workflow_config: WorkflowConfig | None = None


class ParserConfig(QuivrBaseConfig):
    splitter_config: SplitterConfig = SplitterConfig()
    megaparse_config: MegaparseConfig = MegaparseConfig()


class IngestionConfig(QuivrBaseConfig):
    parser_config: ParserConfig = ParserConfig()


class AssistantConfig(QuivrBaseConfig):
    retrieval_config: RetrievalConfig = RetrievalConfig()
    ingestion_config: IngestionConfig = IngestionConfig()