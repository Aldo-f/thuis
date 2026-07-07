import pytest
from src.thuis.main import canonical_slug, is_season_url, fetch_season_episodes, _get_list_id, _guess_episode_urls, _is_not_found
from unittest.mock import patch, MagicMock

def test_canonical_slug():
    assert canonical_slug("F.C. De Kampioenen") == "f-c--de-kampioenen"
    assert canonical_slug("Hello World!") == "hello-world"
    assert canonical_slug("  ---Test---  ") == "test"
    assert canonical_slug("A&B") == "a-and-b"

def test_is_season_url():
    assert is_season_url("https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/") == True
    assert is_season_url("https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2") == True
    assert is_season_url("https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/?seizoen=seizoen-2") == True
    assert is_season_url("https://www.vrt.be/vrtmax/a/show/123/") == False
    assert is_season_url("https://www.vrt.be/vrtmax/a/show/123") == False

@patch('src.thuis.main._get_list_id')
@patch('src.thuis.main._execute_graphql_query')
def test_fetch_season_episodes_graphql_success(mock_execute, mock_get_list_id):
    # Mock the GraphQL responses with the new cursor-based format
    mock_get_list_id.return_value = "listid123"
    mock_execute.side_effect = [
        # First page
        {
            'data': {
                'list': {
                    'paginatedItems': {
                        'edges': [
                            {'node': {
                                '__typename': 'EpisodeTile',
                                'title': 'Episode 1',
                                'action': {'__typename': 'LinkAction', 'link': '/vrtmax/a-z/fc-de-kampioenen/2/episode-1/'}
                            }},
                            {'node': {
                                '__typename': 'EpisodeTile',
                                'title': 'Episode 2',
                                'action': {'__typename': 'LinkAction', 'link': '/vrtmax/a-z/fc-de-kampioenen/2/episode-2/'}
                            }},
                        ],
                        'pageInfo': {'endCursor': 'cursor1', 'hasNextPage': False}
                    }
                }
            }
        },
    ]
    episodes = fetch_season_episodes("https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/")
    assert episodes == [
        "https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/episode-1/",
        "https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/episode-2/"
    ]

@patch('src.thuis.main._get_list_id')
def test_fetch_season_episodes_graphql_fallback(mock_get_list_id):
    # GraphQL returns no listId, so fallback to guessing
    mock_get_list_id.return_value = None
    with patch('src.thuis.main._guess_episode_urls') as mock_guess:
        mock_guess.return_value = ["http://example.com/ep1"]
        episodes = fetch_season_episodes("https://www.vrt.be/vrtmax/a-z/fc-de-kampioenen/2/")
        assert episodes == ["http://example.com/ep1"]
        mock_guess.assert_called_once_with("fc-de-kampioenen", 2, None)

@patch('src.thuis.main.urllib.request.urlopen')
def test_guess_episode_urls(mock_urlopen):
    # Mock the urlopen to return a successful response for episode 1 and 2, then fail for 3
    def side_effect(request, *args, **kwargs):
        url = request.full_url
        from urllib.error import HTTPError
        
        def _make_resp(status: int):
            resp = MagicMock()
            resp.status = status
            # __enter__ must return self for context manager protocol
            resp.__enter__.return_value = resp
            return resp
        
        if '-s1a1' in url or '/1a1' in url:
            return _make_resp(200)
        elif '-s1a2' in url or '/1a2' in url:
            return _make_resp(200)
        else:
            # Simulate HTTP 404 after episode 2
            raise HTTPError(url, 404, "Not Found", {}, None)
    mock_urlopen.side_effect = side_effect

    episodes = _guess_episode_urls("test-show", 1, None)
    # With max_episodes=None and break-on-first-match, only the -s{season}a{episode} pattern
    # (checked first) is returned per episode
    assert episodes == [
        "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s1a1/",
        "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s1a2/",
    ]

def test_guess_episode_urls_max_episodes():
    """max_episodes limit is respected during HEAD-guess fallback."""
    with patch('src.thuis.main.urllib.request.urlopen') as mock_urlopen:
        def side_effect(request, *args, **kwargs):
            url = request.full_url
            from urllib.error import HTTPError
            resp = MagicMock()
            resp.status = 200
            resp.__enter__.return_value = resp
            if '-s1a1' in url:
                return resp
            elif '-s1a2' in url:
                return resp
            elif '-s1a3' in url:
                return resp
            else:
                raise HTTPError(url, 404, "Not Found", {}, None)
        mock_urlopen.side_effect = side_effect

        episodes = _guess_episode_urls("test-show", 1, max_episodes=2)
        assert len(episodes) == 2
        assert episodes == [
            "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s1a1/",
            "https://www.vrt.be/vrtmax/a-z/test-show/1/test-show-s1a2/",
        ]

def test_get_list_id_failure():
    with patch('src.thuis.main._execute_graphql_query') as mock_exec:
        mock_exec.return_value = None
        result = _get_list_id("some-show", 1)
        assert result is None


def test_get_list_id_by_title():
    """_get_list_id matches tiles by title containing season number."""
    with patch('src.thuis.main._execute_graphql_query') as mock_exec:
        mock_exec.return_value = {
            'data': {
                'page': {
                    'components': [
                        {'__typename': 'ContainerNavigation', 'items': [
                            {'components': [
                                {'__typename': 'PaginatedTileList', 'listId': 'trailer-id', 'title': 'Trailer'},
                                {'__typename': 'PaginatedTileList', 'listId': 's1-id', 'title': 'Seizoen 1'},
                                {'__typename': 'PaginatedTileList', 'listId': 'seizoen2-id', 'title': 'Seizoen 2 (30 afleveringen)'},
                            ]}
                        ]}
                    ]
                }
            }
        }
        # Season 2 should match by title, not by position
        result = _get_list_id("some-show", 2)
        assert result == 'seizoen2-id'
        # Season 1 should also work
        result = _get_list_id("some-show", 1)
        assert result == 's1-id'


def test_is_not_found_http_error():
    """_is_not_found returns True for HTTP status >= 400."""
    assert _is_not_found(404, "") is True
    assert _is_not_found(500, "") is True
    assert _is_not_found(403, "") is True
    assert _is_not_found(200, "") is False
    assert _is_not_found(301, "") is False


def test_is_not_found_soft_stop():
    """_is_not_found returns True when body contains the soft-stop phrase."""
    assert _is_not_found(200, "Deze pagina lijkt verloren") is True
    assert _is_not_found(200, "Deze pagina lijkt verloren. Kijk verder op VRT MAX.") is True
    assert _is_not_found(200, "Gewone pagina inhoud") is False
    assert _is_not_found(302, "Deze pagina lijkt verloren") is True  # status check first

if __name__ == '__main__':
    pytest.main()