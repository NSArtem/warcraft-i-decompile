{
  description = "Warcraft: Orcs & Humans (DOS, CD v1.22h) decompilation and source reconstruction";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        # The Sybase Open Watcom Public License is flagged unfree in nixpkgs;
        # allow exactly that package and nothing else.
        config.allowUnfreePredicate = p: builtins.elem (nixpkgs.lib.getName p) [ "open-watcom-v2" "open-watcom-v2-unwrapped" ];
      };

      py = pkgs.python3.withPackages (ps: with ps; [
        capstone   # x86 disassembly
        unicorn    # function-level differential execution
        keystone-engine
        pillow     # image/graphics format work
        pytest
      ]);

      # Tools needed to go from CD_DIC.rar to the analysed/rebuilt executable.
      coreTools = with pkgs; [
        py
        unar        # RAR5 extraction of the disc dump
        lhasa       # the installer's .EXA files are lh5 archives
        open-watcom-v2  # rebuild toolchain (wcc386 / wasm / wlink, DOS/4G LE)
        nasm
        coreutils
        gnumake
        xxd
        file
        binutils
        sqlite
        git
      ];

      # Interactive analysis / runtime verification tools.
      analysisTools = with pkgs; [
        ghidra
        dosbox-x
        xvfb-run     # headless runs of the game for behavioural tests
        imagemagick  # screenshots of the virtual display
        radare2
        gdb
      ];
    in {
      devShells.${system} = {
        default = pkgs.mkShell {
          packages = coreTools ++ analysisTools;
          shellHook = ''
            export WC1_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
            export WATCOM="${pkgs.open-watcom-v2}"
            export PYTHONPATH="$WC1_ROOT/tools''${PYTHONPATH:+:$PYTHONPATH}"
            echo "warcraft-1-decompile environment ready (make help)"
          '';
        };
        # Headless subset used by CI-style checks (no Ghidra/DOSBox).
        ci = pkgs.mkShell {
          packages = coreTools;
          shellHook = ''
            export WC1_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
            export WATCOM="${pkgs.open-watcom-v2}"
            export PYTHONPATH="$WC1_ROOT/tools''${PYTHONPATH:+:$PYTHONPATH}"
          '';
        };
      };

      packages.${system} = {
        # Analysis Python on its own (no compiler build needed): nix shell .#pyenv
        pyenv = py;
        open-watcom = pkgs.open-watcom-v2;
      };

      formatter.${system} = pkgs.nixpkgs-fmt;
    };
}
