from hermes_bridge.single_instance import SingleInstanceLock


def test_single_instance_lock_rejects_second_holder(tmp_path):
    lock_path = tmp_path / "hermes.lock"
    first = SingleInstanceLock(lock_path)
    second = SingleInstanceLock(lock_path)

    try:
        assert first.acquire() is True
        assert second.acquire() is False
    finally:
        first.release()
        second.release()


def test_single_instance_lock_can_reacquire_after_release(tmp_path):
    lock_path = tmp_path / "hermes.lock"
    first = SingleInstanceLock(lock_path)
    second = SingleInstanceLock(lock_path)

    assert first.acquire() is True
    first.release()

    try:
        assert second.acquire() is True
    finally:
        second.release()
