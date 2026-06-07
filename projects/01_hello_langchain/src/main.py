"""
main.py — Hello LangChain
Minimal working example: load an LLM via Ollama and run a simple Q&A chain.
"""

import sys
from pathlib import Path

# Workaround: Add repository root to sys.path (Python 3.14 .pth compatibility issue)
# This ensures the common package can be imported regardless of .pth file loading
# Path: src/main.py -> src -> 01_hello_langchain -> projects -> repo_root
_repo_root = Path(__file__).parent.parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from dotenv import load_dotenv  # noqa: E402
from langchain_core.prompts import PromptTemplate  # noqa: E402
from langchain_core.output_parsers import StrOutputParser  # noqa: E402

from common.llm_factory import get_llm  # noqa: E402
from common.utils import get_logger  # noqa: E402

load_dotenv()

logger = get_logger(__name__)


def main():
    logger.info("Initialising LLM...")
    llm = get_llm()

    prompt = PromptTemplate.from_template(
        "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
    )

    chain = prompt | llm | StrOutputParser()

    question = "What is LangChain and why is it useful for building AI agents?"
    logger.info(f"Question: {question}")

    response = chain.invoke({"question": question})

    print("\n--- Response ---")
    print(response)
    print("----------------\n")


if __name__ == "__main__":
    main()
