from rebuttal.throughput_data import mixture_counts, clip_response


def test_mixture_proportions():
    assert mixture_counts(2000) == (256, 1744)


def test_clip_keeps_prompt_and_response_mask():
    row = dict(input_ids=[1, 2, 3, 4, 5], prompt_token_ids=[1, 2],
               completion_token_ids=[3, 4, 5], response_start=2,
               loss_mask=[False, False, True, True, True])
    clipped, record = clip_response(row, 4)
    assert clipped['input_ids'] == [1, 2, 3, 4]
    assert clipped['loss_mask'] == [False, False, True, True]
    assert row['completion_token_ids'] == [3, 4, 5]
    assert record == dict(original_tokens=5, kept_tokens=4, removed_answer_tokens=1)


def test_clip_rejects_lost_prompt():
    import pytest
    with pytest.raises(ValueError):
        clip_response(dict(prompt_token_ids=[1, 2], completion_token_ids=[3],
                           input_ids=[1, 2, 3], response_start=2,
                           loss_mask=[False, False, True]), 2)
