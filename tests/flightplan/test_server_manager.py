from condor.server_manager import OnlineStatus, parse_server_status_list_box_items


def test_parse_server_status_list_box_items():
    items = ["Status: joining enabled", "Time: 10:07:49", "Stop join in: 00:01:59"]

    status = parse_server_status_list_box_items(items)

    assert status.online_status == OnlineStatus.JOINING_ENABLED
    assert status.time == "10:07:49"
    assert status.stop_join_in == "00:01:59"
