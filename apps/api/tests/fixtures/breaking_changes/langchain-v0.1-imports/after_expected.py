from langchain_core.prompts import PromptTemplate


def build_prompt(template_str: str) -> PromptTemplate:
    return PromptTemplate.from_template(template_str)
