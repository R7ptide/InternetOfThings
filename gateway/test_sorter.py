import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sorter  # noqa: E402

ROOT = sorter.ROOT


class Fake:
    def __init__(self):
        self.now = 0.0
        self.sent = []
        self.seq = sorter.Sequencer(lambda t, p: self.sent.append((t, p)), clock=lambda: self.now, log=lambda m: None)

    def msg(self, topic, **payload):
        self.seq.on_message(f"{ROOT}/{topic}", json.dumps(payload))

    def item(self, item_id=1):
        self.msg("line/item", item_id=item_id, event="detected")

    def color(self, color, confidence=0.9):
        self.msg("color/classification", color=color, confidence=confidence)

    def advance(self, seconds):
        self.now += seconds
        self.seq.tick()

    def actions(self):
        return [p for t, p in self.sent if t.endswith("/line/cmd")]

    def clear(self):
        self.sent.clear()


def test_happy_path():
    f = Fake()
    f.item(7)
    assert f.seq.state == sorter.COLLECTING
    assert f.actions() == [{"action": "belt", "state": "stop"}]
    f.clear()
    for _ in range(sorter.MIN_SAMPLES):
        f.color("red", 0.95)
    assert f.seq.state == sorter.DIVERTING
    run, divert = f.actions()
    assert run["action"] == "belt" and run["state"] == "run"
    assert divert == {"action": "divert", "item_id": 7, "bin": "red", "delay_ms": sorter.TRAVEL_DELAY_MS}
    f.msg("line/bin", item_id=7, bin="red", count=1)
    assert f.seq.state == sorter.IDLE


def test_vote_beats_one_bad_reading():
    f = Fake()
    f.item()
    f.clear()
    f.color("green", 0.9)
    f.color("blue", 0.7)
    f.color("green", 0.95)
    assert f.actions()[-1]["bin"] == "green"


def test_low_confidence_goes_to_unknown():
    f = Fake()
    f.item()
    f.clear()
    for _ in range(sorter.MIN_SAMPLES):
        f.color("blue", 0.4)
    assert f.actions()[-1]["bin"] == "unknown"


def test_disagreement_goes_to_unknown():
    f = Fake()
    f.item()
    f.clear()
    f.color("red", 0.9)
    f.color("green", 0.9)
    f.color("blue", 0.9)  # each wins 1/3 of the weight
    assert f.actions()[-1]["bin"] == "unknown"


def test_timeout_without_samples_goes_to_unknown():
    f = Fake()
    f.item()
    f.clear()
    f.advance(sorter.COLOR_TIMEOUT_S - 0.1)
    assert f.actions() == []  # not yet
    f.advance(0.2)
    assert f.actions()[-1] == {"action": "divert", "item_id": 1, "bin": "unknown",
                               "delay_ms": sorter.TRAVEL_DELAY_MS}
    assert f.seq.state == sorter.DIVERTING


def test_timeout_with_some_samples_still_decides():
    f = Fake()
    f.item()
    f.clear()
    f.color("blue", 0.9)
    f.color("blue", 0.9)  # fewer than MIN_SAMPLES
    f.advance(sorter.COLOR_TIMEOUT_S + 0.1)
    assert f.actions()[-1]["bin"] == "blue"


def test_no_confirmation_returns_to_idle():
    f = Fake()
    f.item()
    for _ in range(sorter.MIN_SAMPLES):
        f.color("red")
    f.advance(sorter.TRAVEL_DELAY_MS / 1000 + sorter.DIVERT_MARGIN_S + 0.1)
    assert f.seq.state == sorter.IDLE


def test_stale_color_and_busy_item_are_ignored():
    f = Fake()
    f.color("red")  # idle: nobody is waiting
    assert f.sent == [] and f.seq.state == sorter.IDLE
    f.item(1)
    f.clear()
    f.item(2)  # still collecting item 1
    assert f.sent == [] and f.seq.item_id == 1


def test_confirmation_for_another_item_does_not_release():
    f = Fake()
    f.item(5)
    for _ in range(sorter.MIN_SAMPLES):
        f.color("red")
    f.msg("line/bin", item_id=4, bin="red", count=1)
    assert f.seq.state == sorter.DIVERTING


def test_bad_json_is_ignored():
    f = Fake()
    f.seq.on_message(f"{ROOT}/line/item", "not json")
    assert f.seq.state == sorter.IDLE


if __name__ == "__main__":
    tests = [(n, fn) for n, fn in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print("ok  ", name)
    print(f"{len(tests)} tests passed")
