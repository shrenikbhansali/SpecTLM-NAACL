import pytest
from ops.track_i_watch import validate_slots


def test_partition_check_rejects_unsafe_gpu_even_with_node_filter():
    validate_slots('heck-srv3:0,heck-srv4:7,heck-srv2:0,heck-srv2:3')
    with pytest.raises(ValueError):validate_slots('heck-srv4:0,heck-srv2:4')
    with pytest.raises(ValueError):validate_slots('heck-srv5:0,heck-srv2:0')
