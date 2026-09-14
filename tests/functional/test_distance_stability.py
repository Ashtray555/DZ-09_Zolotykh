def test_distance_readings_are_stable(device_driver):
    device_driver.backend.distance = 42

    readings = [device_driver.read_distance() for _ in range(20)]

    assert len(readings) == 20
    assert max(readings) - min(readings) <= 2
    assert all(1 <= value <= 400 for value in readings)
