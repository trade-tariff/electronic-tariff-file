{
  outputs =
    _:
    let
      pkgs = import (builtins.fetchTree {
        type = "github";
        owner = "NixOS";
        repo = "nixpkgs";
        rev = "55bfb4d7437bd4e09ab7cba58a43bd68eb310044";
        narHash = "sha256-jBYGPi4udQ9uo4KQp9m2J0546nJVQitG15gvZSaVVAs=";
      }) { system = "x86_64-linux"; };
      reviewHookTools = import (builtins.fetchTree {
        type = "github";
        owner = "NixOS";
        repo = "nixpkgs";
        rev = "0d534853a55b5d02a4ababa1d71921ce8f0aee4c";
        narHash = "sha256-IDtwLhWMKvydW9GrB6ETwhij+vma0hYHln8pR/rTd+U=";
      }) { system = "x86_64-linux"; };
      reviewSecretTools = import (builtins.fetchTree {
        type = "github";
        owner = "NixOS";
        repo = "nixpkgs";
        rev = "dd613136ee91f67e5dba3f3f41ac99ae89c5406b";
        narHash = "sha256-RVQQZy38O3Zb8yoRJhuFgWo/iDIDj0hEdRTVfhOtzRk=";
      }) { system = "x86_64-linux"; };
      hook = id: entry: types: {
        inherit id entry types;
        name = id;
        language = "system";
      };
      reviewPreCommitConfig = pkgs.writeText "review-pre-commit.json" (
        builtins.toJSON {
          repos = [
            {
              repo = "local";
              hooks = [
                (
                  (hook "trailing-whitespace"
                    "${reviewHookTools.python3Packages.pre-commit-hooks}/bin/trailing-whitespace-fixer"
                    [
                      "text"
                    ]
                  )
                  // {
                    stages = [
                      "pre-commit"
                      "pre-push"
                      "manual"
                    ];
                  }
                )
                (
                  (hook "end-of-file-fixer"
                    "${reviewHookTools.python3Packages.pre-commit-hooks}/bin/end-of-file-fixer"
                    [
                      "text"
                    ]
                  )
                  // {
                    stages = [
                      "pre-commit"
                      "pre-push"
                      "manual"
                    ];
                  }
                )
                (hook "check-yaml" "${reviewHookTools.python3Packages.pre-commit-hooks}/bin/check-yaml" [
                  "yaml"
                ])
                {
                  id = "trufflehog";
                  name = "TruffleHog";
                  language = "system";
                  entry = "${reviewSecretTools.trufflehog}/bin/trufflehog git file://. --since-commit HEAD --results=verified --fail";
                  pass_filenames = false;
                }
                (
                  (hook "actionlint-docker" "${reviewHookTools.actionlint}/bin/actionlint" [ "yaml" ])
                  // {
                    files = "^\\.github/workflows/";
                  }
                )
              ];
            }
          ];
        }
      );
      reviewEnvironment = ''
        if [ "''${REVIEW_SANDBOX:-}" != 1 ] || [ "$PWD" != /workspace ]; then exit 64; fi
        export TMPDIR=/workspace/.review/tmp VIRTUAL_ENV=/workspace/.review/venv PRE_COMMIT_HOME=/workspace/.review/pre-commit
        export PATH="$VIRTUAL_ENV/bin:$PATH" PIP_CONFIG_FILE=/dev/null PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
        export AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null
        export LD_LIBRARY_PATH="${
          pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
          ]
        }"
        mkdir -p "$TMPDIR"
      '';
    in
    {
      devShells.x86_64-linux.review = pkgs.mkShell {
        shellHook = "";
        packages = [
          pkgs.gitMinimal
          (pkgs.python312.withPackages (ps: [
            ps.pip
            ps.virtualenv
          ]))
          pkgs.pre-commit
          reviewHookTools.python3Packages.pre-commit-hooks
          reviewSecretTools.trufflehog
          reviewHookTools.actionlint
          pkgs.postgresql
        ];
        nativeBuildInputs = [
          (pkgs.writeShellApplication {
            name = "review-bootstrap";
            text = reviewEnvironment + ''
              if [ ! -s /deps/python-inputs/locked-requirements.txt ]; then echo 'Blocked: verified wheels for the declared requirements are unavailable.' >&2; exit 78; fi
              (cd /deps/python-inputs; sha256sum -c checksums)
              python -m virtualenv --no-download "$VIRTUAL_ENV"
              "$VIRTUAL_ENV/bin/python" -m pip install --no-index --find-links=/deps/python-inputs/wheels --require-hashes -r /deps/python-inputs/locked-requirements.txt
              "$VIRTUAL_ENV/bin/python" -m pip check
              pip-compile --no-index --find-links=/deps/python-inputs/wheels --generate-hashes --output-file="$TMPDIR/requirements.txt" requirements.in
              pip-compile --no-index --find-links=/deps/python-inputs/wheels --generate-hashes --output-file="$TMPDIR/requirements_dev.txt" requirements_dev.in
              pip-sync --pip-args='--no-index --find-links=/deps/python-inputs/wheels --require-hashes' "$TMPDIR/requirements.txt" "$TMPDIR/requirements_dev.txt"
            '';
          })
          (pkgs.writeShellApplication {
            name = "review-check";
            text = reviewEnvironment + ''
              status=0
              pre-commit run --all-files --config ${reviewPreCommitConfig} || status=$?
              mapfile -d "" -t files < <(git ls-files -z '*.py')
              python -m compileall -q "''${files[@]}" || status=$?
              if [ "$status" -ne 0 ]; then exit "$status"; fi
              echo 'Blocked: generator integration needs an approved tariff dataset, database configuration and authorised publication/notification destinations. No dump is restored and the generator is not invoked.' >&2
              exit 78
            '';
          })
        ];
        TZDIR = "${pkgs.tzdata.outPath}/share/zoneinfo";
        SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
      };
    };
}
