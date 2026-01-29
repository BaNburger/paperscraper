"""Jinja2 prompt templates for scoring dimensions."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Set up Jinja2 environment with prompts directory
PROMPTS_DIR = Path(__file__).parent
jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_prompt(template_name: str, **kwargs) -> str:
    """
    Render a prompt template with given variables.

    Args:
        template_name: Name of the template file (e.g., "novelty.jinja2")
        **kwargs: Variables to pass to the template

    Returns:
        Rendered prompt string
    """
    template = jinja_env.get_template(template_name)
    return template.render(**kwargs)
