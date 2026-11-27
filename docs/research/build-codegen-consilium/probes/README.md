# Consilium technical probes

Sanitized copies of the narrow probes that materially affected consilium decisions.
Nothing here is a build product, a game binary or a credential.

Large disposable results (full JSON dumps, emulator traces, Wine prefixes) stayed in
the private runtime directory `/mnt/data/projects/warcraft-1-decompile-consilium/` and
are not committed; where that matters the entry names the external path.

Architect A ran its probes in disposable directories and reported the exact commands
and outputs inside its frozen responses; those commands are the durable record for A.
The frozen responses themselves are under `rounds/`.

## claude-2026-11-27

| file | bytes | sha256 |
|---|---|---|
| `b2_refs.py` | 992 | `e562c9dcf95b11d3dd528ace47b5aca221092f7be78fdf04e7529c462dae0374` |
| `c2.c` | 101 | `78c0fa61efe8380786281e0ca7aed9504eedeb99ec026fa29b57b101cfa4a6d7` |
| `e0-main.log` | 1099 | `1b75c3ec81a23f756f6261a20cf80ca04d3e79ae4367727b712d6ec1aa10753a` |
| `orig.py` | 197 | `0087fb589f0e250ded58fe7260588f20349d778431866e0ddff4206136b456a8` |
| `probe-b1-b2-groupb.patch` | 6853 | `1cd77e6c2251114233df93f3f9816251e197e89c36cc3d5cca13b4d987a56439` |
| `probe_gb.py` | 389 | `d0af83e22c9bf593f646d639109e8a8751562197ad5fb6d2c9ccb3bd92124581` |
| `probe_gb2.py` | 569 | `872e3c95f7004e108b02711826dabc8899ad5c2efb3a5575dc2805e6ed24e7ef` |
| `probe_q1.py` | 1577 | `21b2061d1c34ba4a123cbbd54bbd98d3b7c16f6a940ba27a914992c50d64bdb0` |
| `probe_q2.py` | 2033 | `019784fa997394f205ac4882ec7a3de6fd12bd83600eb3534ef3cf8f00f9e1a7` |
| `rel8_span.py` | 1766 | `b37e88d35c06b79677448b576739c2832d09e6255aca6eed4f3bb032a3988a5b` |
| `run.py` | 377 | `842967fae2cdc01762f40fcb5a5baa399feba19c0abf63375164b7d39d39059e` |
| `run2.py` | 540 | `e37e252ddd09d1e7ec695d198871ccf8c1fb97cba70336f341ade6a86451547c` |
| `run3.py` | 538 | `a309057b7855124609be8a7827d9d520cd8d872656bcf8e4eda3cc50d6d997da` |
| `xobj_rel8.py` | 1213 | `2ddcabf9a2a895c08eaa03161c689de93e581f794b7bf19e9b2f562bc9ffdd41` |
| `zgb.c` | 798 | `b60b525b21e5f3e74f19e22f826ae781a761693452420a15d0a0ce5ac5b24647` |

## gemini-2026-11-27

| file | bytes | sha256 |
|---|---|---|
| `r01_probes.py` | 9816 | `b4566fdfee06b807549b41d2110db10f5c1ad2c183727aa960b9159f1ba6026e` |
| `run_probe7.py` | 3027 | `5af8e58d69bb3adfced8ce3c1e24f6f1ec5d0fd061eca3d5f90a1b31c6af64ae` |
| `run_probe7b.py` | 2975 | `62a72bd5f61af0890dfa0787800691c638d3fabe899f2f7cf91faebac79498cf` |
| `run_probes.py` | 9900 | `af50e66e53824784afa522fba19529d0e1fac12942a1580294601c73d3fba2f9` |
| `run_probes2.py` | 8597 | `81c8f2170bc0fe2b747386f70d7fd8f734cf8e91607f4a33df9e4d39e0183a87` |

## gpt-2026-11-27

| file | bytes | sha256 |
|---|---|---|

