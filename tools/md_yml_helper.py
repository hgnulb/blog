from pathlib import Path
from typing import Any, Union

from dateutil.parser import ParserError, parse
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PlainScalarString

from utils import setup_colored_logger, unique_question_level

setup_colored_logger()

DEFAULT_FIELD_ORDER = [
    "layout",
    "title",
    "slug",
    "question_id",
    "frequency",
    "permalink",
    "categories",
    "tags",
    "difficulty",
    "top",
    "solved",
    "published",
    "date",
]


class MarkdownYamlHandler:
    def __init__(self, file_path: Union[str, Path]) -> None:
        self.file_path = Path(file_path)
        self.yaml = YAML()
        self.yaml.preserve_quotes = False
        self.yaml.default_flow_style = False
        self.yaml.indent(mapping=4, sequence=4, offset=2)
        self.yaml.width = 4096
        self.yaml_data, self.body_lines = self._load_yaml()

    def _load_yaml(self) -> tuple[dict[str, Any], list[str]]:
        if not self.file_path.exists():
            raise FileNotFoundError(f"file '{self.file_path}' not found")

        lines = self.file_path.read_text(encoding="utf-8").splitlines(keepends=True)

        if not lines or lines[0].strip() != "---":
            raise ValueError("yaml front matter not found")

        yaml_lines = []
        index = 1
        while index < len(lines):
            if lines[index].strip() == "---":
                break
            yaml_lines.append(lines[index])
            index += 1

        body_lines = lines[index + 1 :]
        yaml_data = self.yaml.load("".join(yaml_lines)) or {}
        return yaml_data, body_lines

    @staticmethod
    def _clean_items(items: list[str]) -> list[str]:
        return [item.strip() for item in items if item.strip()]

    def get(self, key: str) -> Any:
        return self.yaml_data.get(key)

    def set(self, key: str, value: Any) -> None:
        self.yaml_data[key] = value

    def setnx(self, key: str, value: Any) -> None:
        if key not in self.yaml_data:
            self.yaml_data[key] = value

    def exists(self, key: str) -> bool:
        return key in self.yaml_data

    def append(self, key: str, items: list[str]) -> None:
        items = self._clean_items(items)
        if not items:
            return

        if key not in self.yaml_data:
            self.yaml_data[key] = items
        elif isinstance(self.yaml_data[key], list):
            existing = set(self.yaml_data[key])
            self.yaml_data[key].extend(item for item in items if item not in existing)
        else:
            raise TypeError(f"'{key}' is not a list")

    def remove(self, key: str, items: list[str]) -> None:
        items = self._clean_items(items)
        if not items or key not in self.yaml_data:
            return

        if isinstance(self.yaml_data[key], list):
            self.yaml_data[key] = [
                item for item in self.yaml_data[key] if item not in items
            ]

    def del_key(self, key: str) -> None:
        if key in self.yaml_data:
            del self.yaml_data[key]

    def save(self) -> None:
        self._format_and_sort()

        with self.file_path.open("w", encoding="utf-8") as file:
            file.write("---\n")
            self.yaml.dump(self._clean_quotes(self.yaml_data), file)
            file.write("---\n")
            file.writelines(self.body_lines)

    def _clean_quotes(self, data: Any) -> Any:
        if isinstance(data, str):
            cleaned = data.strip()
            if cleaned.isdigit():
                return int(cleaned)
            try:
                return float(cleaned)
            except ValueError:
                pass
            if cleaned.lower() in ["true", "false"]:
                return cleaned.lower() == "true"
            try:
                return parse(cleaned)
            except (ParserError, ValueError, OverflowError):
                pass
            return PlainScalarString(cleaned)
        if isinstance(data, list):
            return [self._clean_quotes(item) for item in data]
        if isinstance(data, dict):
            return {key: self._clean_quotes(value) for key, value in data.items()}
        if data is None:
            return None
        return data

    def _format_and_sort(self) -> None:
        formatted = {}
        self.yaml_data = {
            key: value
            for key, value in self.yaml_data.items()
            if value not in [None, "", [], {}]
        }
        for key, value in self.yaml_data.items():
            if isinstance(value, list):
                formatted[key] = sorted(
                    set(self._clean_items(unique_question_level(value)))
                )
            else:
                formatted[key] = value

        sorted_data = {
            key: formatted[key] for key in DEFAULT_FIELD_ORDER if key in formatted
        }
        sorted_data.update(
            {key: value for key, value in formatted.items() if key not in sorted_data}
        )
        self.yaml_data = sorted_data
