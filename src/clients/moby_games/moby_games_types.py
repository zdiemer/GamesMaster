from typing import List, NamedTuple


class GenreCategory:
    name: str
    id: int

    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Genre:
    category: GenreCategory
    id: int
    description: str
    name: str

    def __init__(
        self, category: GenreCategory, id: int, name: str, description: str = None
    ):
        self.category = category
        self.id = id
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Group:
    description: str
    id: int
    name: str

    def __init__(self, description: str, id: int, name: str):
        self.description = description
        self.id = id
        self.name = name

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Platform:
    id: int
    name: str

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class AlternateTitle:
    description: str
    title: str

    def __init__(self, description: str, title: str):
        self.description = description
        self.title = title

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class GamePlatform(NamedTuple):
    platform: Platform
    first_release_date: str

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Cover:
    height: int
    image_url: str
    platforms: List[str]
    thumbnail_image_url: str
    width: int

    def __init__(
        self,
        height: int,
        image_url: str,
        platforms: List[str],
        thumbnail_image_url: str,
        width: int,
    ):
        self.height = height
        self.image_url = image_url
        self.platforms = platforms
        self.thumbnail_image_url = thumbnail_image_url
        self.width = width

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Screenshot:
    caption: str
    height: int
    image_url: str
    thumbnail_image_url: str
    width: str

    def __init__(
        self,
        caption: str,
        height: int,
        image_url: str,
        thumbnail_image_url: str,
        width: int,
    ):
        self.caption = caption
        self.height = height
        self.image_url = image_url
        self.thumbnail_image_url = thumbnail_image_url
        self.width = width

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()


class Game:
    alternate_titles: List[AlternateTitle]
    description: str
    id: int
    genres: List[Genre]
    moby_score: float
    moby_url: str
    num_votes: int
    official_url: str
    platforms: List[GamePlatform]
    sample_cover: Cover
    sample_screenshots: List[Screenshot]
    title: str

    def __init__(
        self,
        alternate_titles: List[AlternateTitle],
        description: str,
        id: int,
        genres: List[Genre],
        moby_score: float,
        moby_url: str,
        num_votes: int,
        official_url: str,
        platforms: GamePlatform,
        sample_cover: Cover,
        sample_screenshots: List[Screenshot],
        title: str,
    ):
        self.alternate_titles = alternate_titles
        self.description = description
        self.id = id
        self.genres = genres
        self.moby_score = moby_score
        self.moby_url = moby_url
        self.num_votes = num_votes
        self.official_url = official_url
        self.platforms = platforms
        self.sample_cover = sample_cover
        self.sample_screenshots = sample_screenshots
        self.title = title

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
