class HltbResult:
    playtime_main_seconds: int
    playtime_main_plus_seconds: int
    playtime_100_percent_seconds: int
    playtime_all_seconds: int
    playtime_main_count: int
    playtime_main_plus_count: int
    playtime_100_percent_count: int
    playtime_all_count: int

    def __init__(
        self,
        playtime_main_seconds: int,
        playtime_main_plus_seconds: int,
        playtime_100_percent_seconds: int,
        playtime_all_seconds: int,
        playtime_main_count: int,
        playtime_main_plus_count: int,
        playtime_100_percent_count: int,
        playtime_all_count: int,
    ):
        self.playtime_main_seconds = playtime_main_seconds
        self.playtime_main_plus_seconds = playtime_main_plus_seconds
        self.playtime_100_percent_seconds = playtime_100_percent_seconds
        self.playtime_all_seconds = playtime_all_seconds
        self.playtime_main_count = playtime_main_count
        self.playtime_main_plus_count = playtime_main_plus_count
        self.playtime_100_percent_count = playtime_100_percent_count
        self.playtime_all_count = playtime_all_count
