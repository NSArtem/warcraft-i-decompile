import os

import pytest

from wc1 import path, t4spec


pytestmark = pytest.mark.skipif(not (os.path.exists(path('original','install','war.exe')) and os.environ.get('WATCOM')), reason='needs original/ and $WATCOM')


def test_t3_matches():
    t4spec.assert_t3_matches(path('src/mod_20c30'), ['order_create_building_and_target.c', 'ui_activate_spell.c', 'ui_issue_town_square_order.c', 'ui_start_building_placement.c', 'ui_start_research.c', 'ui_start_training.c'])
