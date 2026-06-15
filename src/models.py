"""Data models and I/O helpers for the bidirectional matching system."""

import json
from dataclasses import dataclass, field
from typing import List


@dataclass
class Profile:
    """A person/candidate with skills and experience."""
    id: str
    name: str
    skills: List[str]
    experience_years: int


@dataclass
class Project:
    """A job/gig with required skills and minimum experience."""
    id: str
    name: str
    required_skills: List[str]
    min_experience_years: int


@dataclass
class MatchResult:
    """A match between a source and a target with a score and overlapping skills."""
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    score: float
    matched_skills: List[str]


def load_profiles(path: str) -> List[Profile]:
    """Read a JSON file of profiles and return a list of Profile objects."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Profile(**entry) for entry in data]


def load_projects(path: str) -> List[Project]:
    """Read a JSON file of projects and return a list of Project objects."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Project(**entry) for entry in data]


def save_results(results: dict, path: str) -> None:
    """Write a results dictionary as JSON to the given path."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
