from followspec.launch_health import failures


def test_launch_refusal_is_not_silently_treated_as_queued():
 events=[dict(event='launch_failed',name='D50-E1',t='2026-10-09T02:00',stderr='missing run tag'),dict(event='finished',name='D50-E2',t='2026-10-09T02:01',exit='1'),dict(event='finished',name='D50-E3',t='2026-10-09T02:02',exit='0'),dict(event='launched',name='D50-E4',t='2026-10-09T02:00'),dict(event='launch_failed',name='old',t='2026-10-08T01:00')]
 assert [r['name'] for r in failures(events,'2026-10-09T01:50')]==['D50-E1','D50-E2']
