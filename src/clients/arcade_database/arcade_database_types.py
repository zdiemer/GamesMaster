from __future__ import annotations
from typing import Any, Dict, Optional


class QueryMameResponse:
    index: int
    url: str
    game_name: str
    title: str
    clone_of: Optional[str]
    manufacturer: str
    url_image_ingame: str
    url_image_title: str
    url_image_marquee: str
    url_image_cabinet: str
    url_image_flyer: str
    url_icon: str
    genre: str
    players: int
    year: int
    status: str
    history: str
    history_copyright_long: str
    history_copyright_short: str
    youtube_video_id: str
    url_video_shortplay: str
    url_video_shortplay_hd: str
    emulator_id: int
    emulator_name: str
    languages: str
    rate: int
    short_title: str
    n_players: str
    input_controls: str
    input_buttons: int
    buttons_colors: str
    series: str
    screen_orientation: str
    screen_resolution: str

    def __init__(
        self,
        index: int,
        url: str,
        game_name: str,
        title: str,
        clone_of: Optional[str],
        manufacturer: str,
        url_image_ingame: str,
        url_image_title: str,
        url_image_marquee: str,
        url_image_cabinet: str,
        url_image_flyer: str,
        url_icon: str,
        genre: str,
        players: int,
        year: Optional[int],
        status: str,
        history: str,
        history_copyright_long: str,
        history_copyright_short: str,
        youtube_video_id: str,
        url_video_shortplay: str,
        url_video_shortplay_hd: str,
        emulator_id: int,
        emulator_name: str,
        languages: str,
        rate: int,
        short_title: str,
        n_players: str,
        input_controls: str,
        input_buttons: int,
        buttons_colors: str,
        series: str,
        screen_orientation: str,
        screen_resolution: str,
    ):
        self.index = index
        self.url = url
        self.game_name = game_name
        self.title = title
        self.clone_of = clone_of
        self.manufacturer = manufacturer
        self.url_image_ingame = url_image_ingame
        self.url_image_title = url_image_title
        self.url_image_marquee = url_image_marquee
        self.url_image_cabinet = url_image_cabinet
        self.url_image_flyer = url_image_flyer
        self.url_icon = url_icon
        self.genre = genre
        self.players = players
        self.year = year
        self.status = status
        self.history = history
        self.history_copyright_long = history_copyright_long
        self.history_copyright_short = history_copyright_short
        self.youtube_video_id = youtube_video_id
        self.url_video_shortplay = url_video_shortplay
        self.url_video_shortplay_hd = url_video_shortplay_hd
        self.emulator_id = emulator_id
        self.emulator_name = emulator_name
        self.languages = languages
        self.rate = rate
        self.short_title = short_title
        self.n_players = n_players
        self.input_controls = input_controls
        self.input_buttons = input_buttons
        self.buttons_colors = buttons_colors
        self.series = series
        self.screen_orientation = screen_orientation
        self.screen_resolution = screen_resolution

    @staticmethod
    def from_json(_json: Dict[str, Any]) -> QueryMameResponse:
        return QueryMameResponse(
            index=_json["index"],
            url=_json["url"],
            game_name=_json["game_name"],
            title=_json["title"],
            clone_of=_json["cloneof"] or None,
            manufacturer=_json["manufacturer"],
            url_image_ingame=_json["url_image_ingame"],
            url_image_title=_json["url_image_title"],
            url_image_marquee=_json["url_image_marquee"],
            url_image_cabinet=_json["url_image_cabinet"],
            url_image_flyer=_json["url_image_flyer"],
            url_icon=_json["url_icon"],
            genre=_json["genre"],
            players=_json["players"],
            year=QueryMameResponse.try_get_year(_json["year"]),
            status=_json["status"],
            history=_json["history"],
            history_copyright_long=_json["history_copyright_long"],
            history_copyright_short=_json["history_copyright_short"],
            youtube_video_id=_json["youtube_video_id"],
            url_video_shortplay=_json["url_video_shortplay"],
            url_video_shortplay_hd=_json["url_video_shortplay_hd"],
            emulator_id=_json["emulator_id"],
            emulator_name=_json["emulator_name"],
            languages=_json["languages"],
            rate=_json["rate"],
            short_title=_json["short_title"],
            n_players=_json["nplayers"],
            input_controls=_json["input_controls"],
            input_buttons=_json["input_buttons"],
            buttons_colors=_json["buttons_colors"],
            series=_json["serie"],
            screen_orientation=_json["screen_orientation"],
            screen_resolution=_json["screen_resolution"],
        )

    @staticmethod
    def try_get_year(year: str) -> Optional[int]:
        try:
            return int(year)
        except ValueError:
            return None
