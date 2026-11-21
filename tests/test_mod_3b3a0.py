from wc1 import path, t4spec


def test_t3_files_match():
    t4spec.assert_t3_matches(path('src/mod_3b3a0'), ['vid_reset_layers.c'])
