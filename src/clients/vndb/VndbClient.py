from typing import Any, Dict, List, Optional
from clients import ClientBase, DatePart, RateLimit
from config import Config
from excel_game import ExcelGame, ExcelGenre
from game_match import GameMatch
from match_validator import MatchValidator


class VndbClient(ClientBase):
    BASE_URL: str = "https://api.vndb.org/kana"

    def __init__(
        self,
        validator: Optional[MatchValidator] = None,
        config: Optional[Config] = None,
    ):
        validator = validator or MatchValidator()
        config = config or Config.create()
        super().__init__(
            validator, config, RateLimit(200, per=DatePart.MINUTE, per_multipler=5)
        )

    async def schema(self) -> Dict[str, Any]:
        return await self.get(
            f"{self.BASE_URL}/schema", headers={"Content-Type": "application/json"}
        )

    async def vn(self, title: str) -> Any:
        return await self.post(
            f"{self.BASE_URL}/vn",
            json_body={
                "filters": ["search", "=", title],
                "fields": "id, title, alttitle, titles{lang, title, latin, official, main}, aliases, olang, devstatus, released, languages, platforms, image{id, url, dims, sexual, violence, votecount, thumbnail, thumbnail_dims}, length, length_minutes, length_votes, description, average, rating, votecount, screenshots{id, url, dims, sexual, violence, votecount, thumbnail, thumbnail_dims, release.id}, relations{relation, relation_official, id}, tags{rating, spoiler, lie, id}, developers{id, name}, editions{eid, lang, name, official}, staff{eid, role, note, id}, va{note, staff.id, character.id}, extlinks{url, label, name, id}",
            },
            headers={"Content-Type": "application/json"},
        )

    def should_skip(self, game: ExcelGame) -> bool:
        return game.genre not in (ExcelGenre.VISUAL_NOVEL, ExcelGenre.ADVENTURE)

    async def get_results(self, game: ExcelGame) -> List[Any]:
        response = await self.vn(game.title)
        return response.get("results") or []

    async def result_to_match(
        self, game: ExcelGame, result: Any, is_fallback: bool = False
    ) -> GameMatch | None:
        titles = set([result["title"]])

        if (alt_title := result["alttitle"]) is not None:
            titles.add(alt_title)

        for title in result["titles"]:
            titles.add(title["title"])

            if (latin := title.get("latin")) is not None:
                titles.add(latin)

        titles = titles.union(result.get("aliases") or set([]))

        match = self.validator.validate(
            game, list(titles), platforms=result["platforms"]
        )

        if match.likely_match:
            return GameMatch(
                result["title"],
                f"https://vndb.org/{result['id']}",
                result["id"],
                result,
                match,
            )

        return None
