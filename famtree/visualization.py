"""Visualize a family tree using Graphviz."""

from pathlib import Path

import graphviz
from pydantic import TypeAdapter

from famtree.core import FamilyTree, Gender


def create_family_tree_graph(data_source: Path | FamilyTree | str) -> graphviz.Digraph:
    """Visualize a family tree and return the image as bytes."""
    if isinstance(data_source, FamilyTree):
        family_tree = data_source
    elif isinstance(data_source, str):
        family_tree = TypeAdapter(FamilyTree).validate_json(data_source)
    else:
        if not data_source.is_file():
            raise FileNotFoundError(f"File not found: {data_source}")
        if data_source.suffix != ".json":
            raise ValueError(f"Unsupported file format: {data_source}")
        family_tree = TypeAdapter(FamilyTree).validate_json(data_source.read_text("utf-8"))

    dot = graphviz.Digraph(comment="Family Tree")

    dot.attr(rankdir="TB", splines="line")
    dot.attr(
        "node",
        shape="box",
        style="filled",
        fontname="Noto Serif CJK SC",
        fontsize="12",
        width="1.2",
    )

    for person_id, person in family_tree.people.items():
        label = f"{person.name}\n{person.birth_year}"
        if person.death_year:
            label += f" - {person.death_year}"

        fillcolor = {
            Gender.MALE: "lightblue",
            Gender.FEMALE: "pink",
            Gender.OTHER: "lightgreen",
        }.get(person.gender, "white")

        dot.node(
            str(person_id),
            label,
            shape="box",
            style="filled",
            fillcolor=fillcolor,
        )

    for marriage_id, marriage in family_tree.marriages.items():
        dot.node(str(marriage_id), "", shape="point", width="0.1", height="0.1")

        for child_id in marriage.children:
            dot.edge(str(marriage_id), str(child_id))

    for edge in family_tree.edges:
        dot.edge(str(edge.source), str(edge.target), dir="none")

    return dot
