{
  description = "Game decomp environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          ghidra
          gdb

          python3
          sqlite

          cmake
          ninja
          gcc
          clang
          binutils

          git
          file
          xxd
          p7zip
        ];

        shellHook = ''
          echo "Decomp environment ready"
        '';
      };
    };
}
