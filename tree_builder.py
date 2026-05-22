"""
tree_builder.py — Построение иерархического дерева сайта.

Вход: словарь {parent_url: [child_url1, child_url2, ...]}
Выход: список строк с отступами (|-- для вложенности)
"""

from urllib.parse import urlparse


def _find_roots(links_dict: dict[str, list[str]]) -> list[str]:
    """
    Определяет корневые узлы — URL, которые нигде не встречаются как child.

    Args:
        links_dict: словарь parent → [children]

    Returns:
        список корневых URL
    """
    all_children: set[str] = set()
    for children in links_dict.values():
        all_children.update(children)

    roots = [url for url in links_dict if url not in all_children]

    # Если корней нет, используем самый короткий URL (обычно главная)
    if not roots and links_dict:
        roots = [min(links_dict.keys(), key=lambda u: len(u))]

    return roots


def _build_tree_lines(
    node: str,
    links_dict: dict[str, list[str]],
    prefix: str = "",
    visited: set[str] | None = None,
    is_last: bool = True,
) -> list[str]:
    """
    Рекурсивно строит строки дерева с отступами.

    Формат:
        https://it-kirov.info/
        |-- https://it-kirov.info/services
        |   |-- https://it-kirov.info/services/outsourcing
        |   |-- https://it-kirov.info/services/repair
        |-- https://it-kirov.info/contacts

    Args:
        node: текущий URL
        links_dict: словарь связей
        prefix: префикс отступа
        visited: set посещённых узлов (защита от циклов)
        is_last: последний ли на этом уровне?

    Returns:
        список строк дерева
    """
    if visited is None:
        visited = set()

    lines: list[str] = []

    # Выбираем символ для текущего узла
    if prefix == "":
        # Корень
        lines.append(node)
    elif is_last:
        lines.append(f"{prefix}└── {node}")
    else:
        lines.append(f"{prefix}├── {node}")

    # Защита от циклов
    if node in visited:
        return lines
    visited.add(node)

    # Рекурсия по детям
    children = links_dict.get(node, [])
    if children:
        # Фильтруем: оставляем только уникальные, не посещённые
        unique_children = []
        for child in children:
            if child not in visited:
                if child not in unique_children:
                    unique_children.append(child)

        for i, child in enumerate(unique_children):
            child_is_last = i == len(unique_children) - 1

            # Префикс для детей
            if prefix == "":
                child_prefix = "    " if child_is_last else "│   "
            else:
                if is_last:
                    child_prefix = prefix + "    "
                else:
                    child_prefix = prefix + "│   "

            child_lines = _build_tree_lines(
                child, links_dict,
                prefix=child_prefix,
                visited=visited,
                is_last=child_is_last,
            )
            lines.extend(child_lines)

    return lines


def build_tree(links_dict: dict[str, list[str]]) -> list[str]:
    """
    Строит визуализацию дерева сайта.

    Args:
        links_dict: словарь parent → [children]

    Returns:
        список строк с иерархическими отступами
    """
    roots = _find_roots(links_dict)

    tree_lines: list[str] = []
    for i, root in enumerate(roots):
        is_last_root = i == len(roots) - 1
        root_lines = _build_tree_lines(
            root, links_dict,
            prefix="",
            is_last=True,
        )
        tree_lines.extend(root_lines)

    return tree_lines


def build_tree_flat(links_dict: dict[str, list[str]]) -> list[str]:
    """
    Строит плоский список URL в иерархическом порядке (обход в глубину).

    Args:
        links_dict: словарь parent → [children]

    Returns:
        список URL в порядке обхода дерева
    """
    roots = _find_roots(links_dict)

    flat: list[str] = []

    def dfs(node: str, visited: set[str]) -> None:
        if node in visited:
            return
        visited.add(node)
        flat.append(node)
        for child in links_dict.get(node, []):
            dfs(child, visited)

    visited: set[str] = set()
    for root in roots:
        dfs(root, visited)

    return flat
