"""Tests for the bidirectional matching engine."""

from __future__ import annotations

import os

import pytest

from src.models import Profile, Project, MatchResult, load_profiles, load_projects
from src.matcher import (
    _calculate_score,
    match_profile_to_projects,
    match_project_to_profiles,
    bidirectional_match,
)

# --- Fixture paths ---
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
PROFILES_PATH = os.path.join(FIXTURES_DIR, "profiles.json")
PROJECTS_PATH = os.path.join(FIXTURES_DIR, "projects.json")


# ---------------------------------------------------------------------------
# _calculate_score tests
# ---------------------------------------------------------------------------

def test_calculate_score_perfect_match():
    """All skills match between profile and project."""
    score, matched = _calculate_score(
        profile_skills={"python", "fastapi"},
        profile_years=5,
        project_skills={"python", "fastapi"},
        project_min_years=3,
    )
    assert score == 1.0
    assert set(matched) == {"fastapi", "python"}


def test_calculate_score_partial_match():
    """Some skills match, some don't."""
    score, matched = _calculate_score(
        profile_skills={"python", "docker"},
        profile_years=5,
        project_skills={"python", "fastapi", "postgresql"},
        project_min_years=3,
    )
    # 1 out of 3 matches → score ≈ 0.333...
    assert score == 1.0 / 3.0
    assert matched == ["python"]


def test_calculate_score_no_match():
    """Zero skills in common → score 0."""
    score, matched = _calculate_score(
        profile_skills={"java", "spring"},
        profile_years=5,
        project_skills={"python", "fastapi"},
        project_min_years=3,
    )
    assert score == 0.0
    assert matched == []


def test_calculate_score_insufficient_experience():
    """Years < min → score 0, regardless of skill match."""
    score, matched = _calculate_score(
        profile_skills={"python", "fastapi", "postgresql"},
        profile_years=2,
        project_skills={"python", "fastapi", "postgresql"},
        project_min_years=5,
    )
    assert score == 0.0
    assert matched == []


def test_calculate_score_empty_project_skills():
    """Empty required_skills → score 0."""
    score, matched = _calculate_score(
        profile_skills={"python", "fastapi"},
        profile_years=5,
        project_skills=set(),
        project_min_years=3,
    )
    assert score == 0.0
    assert matched == []


# ---------------------------------------------------------------------------
# match_profile_to_projects tests
# ---------------------------------------------------------------------------

def test_match_profile_to_projects():
    """One profile against multiple projects, check ranking."""
    profile = Profile(
        id="p1",
        name="Alice",
        skills=["python", "fastapi", "postgresql", "docker"],
        experience_years=5,
    )
    projects = [
        Project(
            id="j1",
            name="Backend API",
            required_skills=["python", "fastapi", "postgresql"],
            min_experience_years=3,
        ),
        Project(
            id="j2",
            name="React Dashboard",
            required_skills=["react", "typescript"],
            min_experience_years=2,
        ),
        Project(
            id="j3",
            name="ML Pipeline",
            required_skills=["python", "tensorflow"],
            min_experience_years=4,
        ),
        Project(
            id="j4",
            name="Senior Role",
            required_skills=["python", "fastapi", "postgresql"],
            min_experience_years=8,  # too high for Alice
        ),
    ]

    results = match_profile_to_projects(profile, projects)

    # Should have results for j1 and j3 only (j2 has no skill match, j4 too senior)
    assert len(results) == 2

    # j1 should be first (3/3 = 1.0)
    assert results[0].target_id == "j1"
    assert results[0].score == 1.0
    assert set(results[0].matched_skills) == {"fastapi", "postgresql", "python"}

    # j3 should be second (1/2 = 0.5)
    assert results[1].target_id == "j3"
    assert results[1].score == 0.5
    assert results[1].matched_skills == ["python"]

    # Verify source metadata
    for r in results:
        assert r.source_id == "p1"
        assert r.source_name == "Alice"


def test_match_profile_to_projects_empty_projects():
    """Empty project list returns empty results."""
    profile = Profile(
        id="p1", name="Alice", skills=["python"], experience_years=5
    )
    results = match_profile_to_projects(profile, [])
    assert results == []


# ---------------------------------------------------------------------------
# match_project_to_profiles tests
# ---------------------------------------------------------------------------

def test_match_project_to_profiles_empty_profiles():
    """Empty profiles list returns empty results."""
    project = Project(
        id="j1", name="Backend", required_skills=["python"], min_experience_years=3
    )
    results = match_project_to_profiles(project, [])
    assert results == []


def test_match_project_to_profiles():
    """One project against multiple profiles."""
    project = Project(
        id="j1",
        name="Backend API",
        required_skills=["python", "fastapi", "postgresql"],
        min_experience_years=3,
    )
    profiles = [
        Profile(
            id="p1", name="Alice",
            skills=["python", "fastapi", "postgresql", "docker"],
            experience_years=5,
        ),
        Profile(
            id="p2", name="Bob",
            skills=["react", "typescript"],
            experience_years=4,  # no skill match
        ),
        Profile(
            id="p3", name="Carol",
            skills=["python", "fastapi", "postgresql"],
            experience_years=1,  # insufficient experience
        ),
        Profile(
            id="p4", name="Dan",
            skills=["python", "django"],
            experience_years=4,  # partial skill match (1/3)
        ),
    ]

    results = match_project_to_profiles(project, profiles)

    # p1 (3/3 = 1.0) and p4 (1/3 ≈ 0.333)
    assert len(results) == 2

    # p1 should be first
    assert results[0].target_id == "p1"
    assert results[0].score == 1.0
    assert set(results[0].matched_skills) == {"fastapi", "postgresql", "python"}

    # p4 should be second
    assert results[1].target_id == "p4"
    assert results[1].score == pytest.approx(1.0 / 3.0)
    assert results[1].matched_skills == ["python"]

    # Verify source metadata
    for r in results:
        assert r.source_id == "j1"
        assert r.source_name == "Backend API"


# ---------------------------------------------------------------------------
# bidirectional_match tests
# ---------------------------------------------------------------------------

def test_bidirectional_match():
    """Full matching with fixture data, verify both directions exist."""
    profiles = load_profiles(PROFILES_PATH)
    projects = load_projects(PROJECTS_PATH)

    result = bidirectional_match(profiles, projects)

    assert "profile_matches" in result
    assert "project_matches" in result

    profile_matches = result["profile_matches"]
    project_matches = result["project_matches"]

    # Every profile should have an entry
    assert set(profile_matches.keys()) == {"p1", "p2", "p3", "p4", "p5"}

    # Every project should have an entry (fixture uses prjN IDs)
    assert set(project_matches.keys()) == {"prj1", "prj2", "prj3", "prj4", "prj5"}

    # p1 (田中太郎: Python/AWS/Docker/PostgreSQL, 5y) should match prj3 (3/3 = 1.0)
    p1_matches = profile_matches["p1"]
    assert any(r.target_id == "prj3" and r.score == 1.0 for r in p1_matches)
    assert any(r.target_id == "prj1" and r.score == pytest.approx(2.0 / 3.0) for r in p1_matches)

    # p4 (山田優子: React/TypeScript/Node.js/MongoDB, 3y) → prj2 (3/3 = 1.0)
    p4_matches = profile_matches["p4"]
    assert any(r.target_id == "prj2" and r.score == 1.0 for r in p4_matches)

    # p5 (伊藤健太: Go/gRPC/Kubernetes/Terraform, 6y) → prj4 (3/3 = 1.0)
    p5_matches = profile_matches["p5"]
    assert any(r.target_id == "prj4" and r.score == 1.0 for r in p5_matches)

    # j1 should match p1 (2/3) and p3 (2/3)
    j1_targets = {r.target_id for r in project_matches["prj1"]}
    assert "p1" in j1_targets
    assert "p3" in j1_targets

    # Results in each list should be sorted by score descending
    for pid, matches in profile_matches.items():
        scores = [m.score for m in matches]
        assert scores == sorted(scores, reverse=True), f"profile {pid} not sorted"

    for jid, matches in project_matches.items():
        scores = [m.score for m in matches]
        assert scores == sorted(scores, reverse=True), f"project {jid} not sorted"


def test_bidirectional_match_excludes_zero_scores():
    """Verify score=0 results are excluded from output."""
    profiles = load_profiles(PROFILES_PATH)
    projects = load_projects(PROJECTS_PATH)

    result = bidirectional_match(profiles, projects)

    for pid, matches in result["profile_matches"].items():
        for m in matches:
            assert m.score > 0, (
                f"profile {pid} → {m.target_id} has score {m.score}, expected > 0"
            )

    for jid, matches in result["project_matches"].items():
        for m in matches:
            assert m.score > 0, (
                f"project {jid} → {m.target_id} has score {m.score}, expected > 0"
            )
