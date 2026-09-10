""" The logging setup for the scraper scripts """
import logging
from datetime import datetime
from rich.logging import RichHandler
from rich.text import Text
from rich.style import Style

# Disable warning about f-strings in logging
# pylint: disable=W1203

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class CustomRichHandler(RichHandler):
    LEVEL_COLORS = {
        "DEBUG": "cyan",
        "INFO": "white",
        "WARNING": "yellow",
        "ERROR": "red",
    }

    def get_level_text(self, record) -> Text:
        """Get the level name from the record."""
        level_name = f"[{record.levelname}]"
        level_style = self.LEVEL_COLORS.get(record.levelname, "white")
        level_text = Text.styled(level_name.ljust(9), Style(color=level_style))
        return level_text
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def setup_logging(log_level):
    """
    Set up logging with the specified log level.
    
    Args:
        log_level (str): Desired logging level ('DEBUG', 'INFO', 'WARN')
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    def timeFormatter(dt: datetime) -> Text:
        strtime = dt.strftime("%H:%M:%S")
        return Text(strtime, Style(color="bright_green", dim=False))

    # Configure RichHandler
    handler = CustomRichHandler(
        rich_tracebacks=True,  # Optional: Enhances traceback rendering
        show_time=True,
        omit_repeated_times=False,
        show_level=True,
        log_time_format=timeFormatter,
        markup=True,           # Enable [color] tags in messages
    )

    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter(
        fmt="%(message)s",
    ))
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    logger.handlers.clear()
    logger.addHandler(handler)

    # Set a higher logging level for urllib3
    logger = logging.getLogger('urllib3')
    logger.setLevel(logging.WARNING)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def print_name(name: str) -> str:
    return f"[dim]{name}[/]"
# ------------------------------------------------------------------------------
