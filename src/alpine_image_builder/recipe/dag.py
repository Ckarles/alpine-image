"""Recipe dependency DAG computation.

Pure Python helpers (no Temporal code) for discovering and resolving
cross-recipe dependency graphs. Orchestrating workflows import these
to compute execution order before scheduling activities.
"""

from graphlib import CycleError, TopologicalSorter

from .discovery import LoadedRecipe


def compute_recipe_dag(recipes: dict[str, LoadedRecipe]) -> dict[str, set[str]]:
    """Return a dependency map: recipe_name -> set of recipe names it depends on.

    Dependencies are derived from ``Recipe.requires`` artifacts.
    If recipe A declares ``requires=[RequiredArtifact(recipe="B", ...)]``,
    the result contains ``{"A": {"B"}}``.
    """
    dag: dict[str, set[str]] = {}
    for name, loaded in recipes.items():
        deps = {req.recipe for req in loaded.recipe.requires}
        dag[name] = deps
    return dag


def topological_levels(dag: dict[str, set[str]]) -> list[set[str]]:
    """Return the DAG as a list of levels.

    Each level is a set of recipes that can be executed in parallel.
    All dependencies of a recipe must appear in earlier levels.

    Uses ``graphlib.TopologicalSorter`` (Python 3.9+ stdlib) instead of
    a hand-rolled Kahn's algorithm.

    Raises:
        ValueError: If the DAG contains a cycle.
    """
    ts = TopologicalSorter(dag)
    try:
        ts.prepare()
    except CycleError as exc:
        raise ValueError("Recipe dependency DAG contains a cycle") from exc

    levels: list[set[str]] = []
    while ts.is_active():
        level = set(ts.get_ready())
        levels.append(level)
        ts.done(*level)

    return levels
