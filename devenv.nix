{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";
  env.SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.gh
    pkgs.cacert
    pkgs.python3Packages.pandas
    pkgs.python3Packages.numpy
    pkgs.python3Packages.matplotlib
    pkgs.python3Packages.scikit-learn
    pkgs.python3Packages.requests
  ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages.python = {
    enable = true;
    poetry = {
      enable = false;
    };
  };

  cachix.pull = [ "football-prediction" ];
  cachix.push = "football-prediction";

  # https://devenv.sh/processes/
  # processes.dev.exec = "${lib.getExe pkgs.watchexec} -n -- ls -la";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  # https://devenv.sh/basics/
  enterShell = ''
    hello         # Run scripts directly
    git --version # Use packages
    export PYTHONPATH="$DEVENV_ROOT/src''${PYTHONPATH:+:$PYTHONPATH}"
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
  containers."shell" = {
    name = "football-prediction-env";
    registry = "docker://ghcr.io/jarosmat/";
    defaultCopyArgs = [
      "--dest-creds"
      "${ACTOR}:${GH_TOKEN}"
    ];
  };
}
