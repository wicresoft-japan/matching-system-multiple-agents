"""Bidirectional matching engine for profiles and projects."""

from __future__ import annotations

from src.models import Profile, Project, MatchResult


def _calculate_score(
    profile_skills: set,
    profile_years: int,
    project_skills: set,
    project_min_years: int,
) -> tuple[float, list]:
    """Calculate match score between a profile and a project.

    Score = |profile_skills ∩ project_skills| / |project_skills|

    Returns (score, matched_skills_list).
    If profile_years < project_min_years → score = 0.
    If project_skills is empty → score = 0.
    """
    if not project_skills:
        return (0.0, [])

    if profile_years < project_min_years:
        return (0.0, [])

    matched = profile_skills & project_skills
    if not matched:
        return (0.0, [])

    score = len(matched) / len(project_skills)
    return (score, sorted(matched))


def match_profile_to_projects(
    profile: Profile, projects: list[Project]
) -> list[MatchResult]:
    """Match one profile against all projects.

    Returns list of MatchResult sorted by score descending.
    Excludes results with score = 0.
    source = profile, target = project
    """
    profile_skills = set(s.lower() for s in profile.skills)
    results: list[MatchResult] = []

    for project in projects:
        project_skills = set(s.lower() for s in project.required_skills)
        score, matched = _calculate_score(
            profile_skills, profile.experience_years,
            project_skills, project.min_experience_years,
        )
        if score > 0:
            results.append(
                MatchResult(
                    source_id=profile.id,
                    source_name=profile.name,
                    target_id=project.id,
                    target_name=project.name,
                    score=score,
                    matched_skills=matched,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def match_project_to_profiles(
    project: Project, profiles: list[Profile]
) -> list[MatchResult]:
    """Match one project against all profiles.

    Returns list of MatchResult sorted by score descending.
    Excludes results with score = 0.
    source = project, target = profile
    """
    project_skills = set(s.lower() for s in project.required_skills)
    results: list[MatchResult] = []

    for profile in profiles:
        profile_skills = set(s.lower() for s in profile.skills)
        score, matched = _calculate_score(
            profile_skills, profile.experience_years,
            project_skills, project.min_experience_years,
        )
        if score > 0:
            results.append(
                MatchResult(
                    source_id=project.id,
                    source_name=project.name,
                    target_id=profile.id,
                    target_name=profile.name,
                    score=score,
                    matched_skills=matched,
                )
            )

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def bidirectional_match(
    profiles: list[Profile], projects: list[Project]
) -> dict:
    """Run full bidirectional matching.

    Returns dict with:
    {
        "profile_matches": {profile_id: [MatchResult, ...]},
        "project_matches": {project_id: [MatchResult, ...]}
    }
    """
    profile_matches: dict[str, list[MatchResult]] = {}
    for profile in profiles:
        profile_matches[profile.id] = match_profile_to_projects(profile, projects)

    project_matches: dict[str, list[MatchResult]] = {}
    for project in projects:
        project_matches[project.id] = match_project_to_profiles(project, profiles)

    return {
        "profile_matches": profile_matches,
        "project_matches": project_matches,
    }
