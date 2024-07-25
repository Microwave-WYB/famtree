"""Core models for the family tree graph."""

from collections import defaultdict
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Marriage(BaseModel):
    """Node representing a marriage in the graph."""

    children: list[UUID] = Field(default_factory=list)


class Gender(StrEnum):
    """Enum for genders."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Person(BaseModel):
    """Model for a person node in the graph."""

    name: str
    gender: Gender
    birth_year: int
    death_year: int | None = None


type _Node = Person | Marriage


class EdgeType(StrEnum):
    """Enum for the type of the edge."""

    MARRIAGE = "MARRIAGE"
    PARENT_CHILD = "PARENT_CHILD"


class Edge(BaseModel):
    """Model for an edge in the graph."""

    source: UUID
    target: UUID

    def __hash__(self) -> int:
        return hash((self.source, self.target))


class FamilyTree(BaseModel):
    """Model for the family tree graph."""

    people: dict[UUID, Person] = Field(default_factory=dict)
    marriages: dict[UUID, Marriage] = Field(default_factory=dict)
    edges: set[Edge] = Field(default_factory=set)

    def __getitem__(self, node_id: UUID) -> Marriage | Person:
        """Get a node by its ID."""
        return self.nodes[node_id]

    @property
    def nodes(self) -> dict[UUID, _Node]:
        """Get all the nodes in the graph."""
        return {**self.people, **self.marriages}

    @property
    def connected(self) -> bool:
        """Check if the graph is connected."""
        if not self.nodes:
            return True

        adjacency_list = defaultdict(set)
        for edge in self.edges:
            adjacency_list[edge.source].add(edge.target)
            adjacency_list[edge.target].add(edge.source)

        for node_id, node in self.nodes.items():
            if isinstance(node, Marriage):
                for child in node.children:
                    adjacency_list[node_id].add(child)
                    adjacency_list[child].add(node_id)

        visited = set()
        start_node_id = next(iter(self.nodes))  # This is already a UUID

        def dfs(node_id):
            visited.add(node_id)
            for neighbor in adjacency_list[node_id]:
                if neighbor not in visited:
                    dfs(neighbor)

        dfs(start_node_id)
        return len(visited) == len(self.nodes)

    def sort(self) -> None:
        """Sort the nodes in the graph."""
        # Sort people by gender (male first) and then by birth year (oldest first)
        sorted_people = sorted(
            self.people.items(),
            key=lambda item: (
                item[1].gender != Gender.MALE,  # Male first
                item[1].gender != Gender.FEMALE,  # Female second
                item[1].birth_year,  # Then by birth year
                item[1].name,  # Finally by name for consistent ordering
            ),
        )

        # Create a new ordered dictionary with the sorted people
        self.people = dict(sorted_people)

    def create_person(
        self,
        name: str,
        gender: Gender,
        birth_year: int,
        death_year: int | None = None,
    ) -> Person:
        """Create a new person node in the graph."""
        # check if person with the same info already exists
        for person in self.people.values():
            if (
                person.name == name
                and person.gender == gender
                and person.birth_year == birth_year
                and person.death_year == death_year
            ):
                return person
        person = Person(
            name=name,
            gender=gender,
            birth_year=birth_year,
            death_year=death_year,
        )
        self.people[uuid4()] = person
        return person

    def update_person(
        self,
        name: str,
        gender: Gender | None,
        birth_year: int | None,
        death_year: int | None = None,
        person_id: UUID | None = None,
    ) -> Person:
        """
        Update a person node in the graph.
        """
        if person_id:
            person = self.people[person_id]
            person.gender = gender or person.gender
            person.birth_year = birth_year or person.birth_year
            person.death_year = death_year or person.death_year
            return person
        matches: list[Person] = [person for person in self.people.values() if person.name == name]
        if not matches:
            raise ValueError("Person not found")
        if len(matches) > 1:
            raise ValueError("Multiple people found, please provide the person ID")
        person = matches[0]
        person.gender = gender or person.gender
        person.birth_year = birth_year or person.birth_year
        person.death_year = death_year or person.death_year
        return person

    def create_marriage(
        self, spouse1_id: UUID, spouse2_id: UUID, children: list[UUID] | None = None
    ) -> Marriage:
        """Create a new marriage node in the graph."""
        marriage = Marriage(children=children or [])
        marriage_id = uuid4()
        self.marriages[marriage_id] = marriage
        self.edges.add(Edge(source=spouse1_id, target=marriage_id))
        self.edges.add(Edge(source=spouse2_id, target=marriage_id))
        return marriage

    def update_marriage(
        self, spouse1_id: UUID, spouse2_id: UUID, children: list[UUID] | None = None
    ) -> Marriage | None:
        """Update a marriage node in the graph."""
        for marriage in self.marriages.values():
            spouse1_marriages = [
                edge.target
                for edge in self.edges
                if edge.source == spouse1_id and edge.target in self.marriages
            ]
            spouse2_marriages = [
                edge.target
                for edge in self.edges
                if edge.source == spouse2_id and edge.target in self.marriages
            ]
            matched_marriage = next(
                (marriage for marriage_id in spouse1_marriages if marriage_id in spouse2_marriages),
                None,
            )
            if matched_marriage:
                matched_marriage.children = children or []
                return matched_marriage
            return None

    def delete_node(self, node_id: UUID) -> None:
        """Delete a node from the graph."""
        if node_id in self.people:
            del self.people[node_id]
        elif node_id in self.marriages:
            del self.marriages[node_id]
        else:
            raise ValueError("Node not found")

        self.edges = {edge for edge in self.edges if node_id not in (edge.source, edge.target)}
        for marriage in self.marriages.values():
            marriage.children = [child for child in marriage.children if child != node_id]

    def merge(self, other: "FamilyTree") -> None:
        """Merge another family tree into this one."""
        for person_id, person in other.people.items():
            self.people[person_id] = person

        for marriage_id, marriage in other.marriages.items():
            self.marriages[marriage_id] = marriage

        self.edges.update(other.edges)
