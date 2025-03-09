from condor.server_manager import (
    OnlineStatus,
    ServerStatus,
    parse_players_list_box_items,
    parse_server_status_list_box_items,
)


def test_parse_server_status_list_box_items():
    items = ["Status: joining enabled", "Time: 10:07:49", "Stop join in: 00:01:59"]

    status = ServerStatus()
    parse_server_status_list_box_items(status, items)

    assert status.online_status == OnlineStatus.JOINING_ENABLED
    assert status.time == "10:07:49"
    assert status.stop_join_in == "00:01:59"


def test_parse_players_list_box_items():
    items = ["M. NAUD", "M. T"]

    status = ServerStatus()
    parse_players_list_box_items(status, items)

    assert len(status.players) == 2
    assert status.players[0] == "M. NAUD"
