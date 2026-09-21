from typing import Dict, List, Tuple, Optional, Any, Set
from rapidfuzz import fuzz, process
from backend.app.config import settings
from backend.app.schemas import MatchedMovie, SearchAlternative
from backend.app.utils.preprocessing import (
    normalize_string_basic,
    extract_year_and_clean,
    unfold_article,
    remove_diacritics,
)

class FuzzyTitleMatcher:
    def __init__(self):
        # alias_to_movie_ids: maps alias string -> list of movieIds
        self.alias_to_movie_ids: Dict[str, List[int]] = {}
        # movie_id_to_aliases: maps movieId -> list of aliases
        self.movie_id_to_aliases: Dict[int, List[str]] = {}
        # movie_metadata: maps movieId -> metadata dict
        self.movie_metadata: Dict[int, Dict[str, Any]] = {}
        # List of unique alias strings for RapidFuzz
        self.alias_list: List[str] = []

    def build_index(self, movies_meta: Dict[int, Dict[str, Any]], title_aliases: Dict[int, Set[str]]):
        """Builds search structures from training time generated metadata and aliases."""
        self.movie_metadata = movies_meta
        self.alias_to_movie_ids = {}
        self.movie_id_to_aliases = {}

        for movie_id, aliases in title_aliases.items():
            alias_list = list(aliases)
            self.movie_id_to_aliases[movie_id] = alias_list
            for alias in alias_list:
                if alias not in self.alias_to_movie_ids:
                    self.alias_to_movie_ids[alias] = []
                self.alias_to_movie_ids[alias].append(movie_id)

        self.alias_list = list(self.alias_to_movie_ids.keys())

    def match_query(self, query: str, top_k: int = 5) -> MatchedMovie:
        query_str = query.strip()
        if not query_str:
            return MatchedMovie(query=query, match_status="no_match")

        # 1. Direct integer ID lookup
        if query_str.isdigit():
            mid = int(query_str)
            if mid in self.movie_metadata:
                meta = self.movie_metadata[mid]
                return MatchedMovie(
                    query=query,
                    movieId=mid,
                    title=meta["title"],
                    confidence_score=100.0,
                    match_status="auto_accept",
                    alternatives=[],
                )

        # 2. Normalize user query into normalized variants
        clean_q, q_year = extract_year_and_clean(query_str)
        q_norm_base = normalize_string_basic(clean_q)
        q_unfolded = unfold_article(clean_q)
        query_variants = set()
        for u in q_unfolded:
            n = normalize_string_basic(u)
            if n:
                query_variants.add(n)
                query_variants.add(n.replace(" ", "").replace("'", ""))
        if q_norm_base:
            query_variants.add(q_norm_base)
            query_variants.add(q_norm_base.replace(" ", "").replace("'", ""))

        if q_year:
            year_str = str(q_year)
            for qv in list(query_variants):
                query_variants.add(f"{qv} {year_str}")

        # 3. Fast exact match check first
        exact_matched_mids = None
        for qv in query_variants:
            if qv in self.alias_to_movie_ids:
                exact_matched_mids = self.alias_to_movie_ids[qv]
                break

        if exact_matched_mids:
            if len(exact_matched_mids) == 1:
                best_exact_mid = exact_matched_mids[0]
                meta = self.movie_metadata[best_exact_mid]
                alts = self._get_alternatives_for_mid(best_exact_mid, query_str, limit=top_k)
                return MatchedMovie(
                    query=query,
                    movieId=best_exact_mid,
                    title=meta["title"],
                    confidence_score=100.0,
                    match_status="auto_accept",
                    alternatives=alts,
                )
            else:
                # Ambiguous exact match across multiple films
                sorted_candidates = sorted(
                    exact_matched_mids,
                    key=lambda mid: (
                        self.movie_metadata.get(mid, {}).get("rating_count", 0),
                        self.movie_metadata.get(mid, {}).get("weighted_rating", 0.0),
                    ),
                    reverse=True,
                )
                best_exact_mid = sorted_candidates[0]
                meta = self.movie_metadata[best_exact_mid]
                alts = [
                    SearchAlternative(
                        movieId=alt_mid,
                        title=self.movie_metadata[alt_mid]["title"],
                        score=90.0,
                    )
                    for alt_mid in sorted_candidates[1:]
                    if alt_mid in self.movie_metadata
                ]
                remaining_limit = top_k - len(alts)
                if remaining_limit > 0:
                    other_alts = self._get_alternatives_for_mid(
                        best_exact_mid,
                        query_str,
                        limit=remaining_limit,
                        exclude_mids=set(exact_matched_mids),
                    )
                    alts.extend(other_alts)

                return MatchedMovie(
                    query=query,
                    movieId=best_exact_mid,
                    title=meta["title"],
                    confidence_score=92.0,
                    match_status="auto_accept",
                    alternatives=alts[:top_k],
                )

        # 4. RapidFuzz fuzzy search across all aliases
        movie_scores: Dict[int, float] = {}

        for qv in query_variants:
            if len(qv) < 2:
                continue
            # Extract top matching aliases using RapidFuzz
            matches = process.extract(
                qv,
                self.alias_list,
                scorer=fuzz.WRatio,
                limit=30,
                score_cutoff=settings.FUZZY_MEDIUM_THRESHOLD - 10.0,
            )
            for matched_alias, score, _ in matches:
                # Year penalty/boost if year specified
                final_score = float(score)
                if q_year and str(q_year) in matched_alias:
                    final_score = min(100.0, final_score + 5.0)

                for mid in self.alias_to_movie_ids[matched_alias]:
                    if mid not in movie_scores or final_score > movie_scores[mid]:
                        movie_scores[mid] = final_score

        if not movie_scores:
            return MatchedMovie(query=query, match_status="no_match")

        # Sort candidate movies by score descending
        sorted_mids = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)
        best_mid, best_score = sorted_mids[0]
        meta = self.movie_metadata[best_mid]

        # Determine confidence status
        if best_score >= settings.FUZZY_HIGH_THRESHOLD:
            status = "auto_accept"
        elif best_score >= settings.FUZZY_MEDIUM_THRESHOLD:
            status = "did_you_mean"
        else:
            status = "no_match"

        alternatives = [
            SearchAlternative(
                movieId=mid,
                title=self.movie_metadata[mid]["title"],
                score=round(score, 1),
            )
            for mid, score in sorted_mids[1: top_k + 1]
        ]

        return MatchedMovie(
            query=query,
            movieId=best_mid if status != "no_match" else None,
            title=meta["title"] if status != "no_match" else None,
            confidence_score=round(best_score, 1),
            match_status=status,
            alternatives=alternatives,
        )

    def search_autocomplete(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns autocomplete candidates for search input."""
        res = self.match_query(query, top_k=limit)
        results = []
        if res.movieId and res.match_status != "no_match":
            meta = self.movie_metadata[res.movieId]
            results.append({
                "movieId": res.movieId,
                "title": meta["title"],
                "genres": meta["genres"],
                "year": meta.get("year"),
                "confidence_score": res.confidence_score,
                "match_status": res.match_status,
            })

        for alt in res.alternatives:
            if len(results) >= limit:
                break
            meta = self.movie_metadata[alt.movieId]
            results.append({
                "movieId": alt.movieId,
                "title": meta["title"],
                "genres": meta["genres"],
                "year": meta.get("year"),
                "confidence_score": alt.score,
                "match_status": "did_you_mean",
            })

        return results

    def _get_alternatives_for_mid(
        self, main_mid: int, query: str, limit: int = 5, exclude_mids: Optional[Set[int]] = None
    ) -> List[SearchAlternative]:
        # Return top fuzzy candidates excluding main_mid and optional exclude_mids
        q_norm = normalize_string_basic(query)
        matches = process.extract(
            q_norm,
            self.alias_list,
            scorer=fuzz.WRatio,
            limit=20,
        )
        alts = []
        seen_mids = {main_mid}
        if exclude_mids:
            seen_mids.update(exclude_mids)
        for matched_alias, score, _ in matches:
            for mid in self.alias_to_movie_ids[matched_alias]:
                if mid not in seen_mids and mid in self.movie_metadata:
                    seen_mids.add(mid)
                    alts.append(SearchAlternative(
                        movieId=mid,
                        title=self.movie_metadata[mid]["title"],
                        score=round(float(score), 1),
                    ))
                    if len(alts) >= limit:
                        return alts
        return alts
