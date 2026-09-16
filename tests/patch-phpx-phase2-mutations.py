#!/usr/bin/env python3
from pathlib import Path
import re

path = Path('PHP/phpx')
text = path.read_text()


def replace_section(start: str, end: str, body: str) -> None:
    global text
    pattern = re.escape(start) + r'.*?' + re.escape(end)
    replacement = start + '\n' + body.rstrip() + '\n\n' + end
    text2, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'failed replacing section: {start!r}')
    text = text2


helpers_marker = '################################################################################\n# PHP Version Validation\n################################################################################'
helpers = r'''atomic_write_file() {
  local target="$1" mode="${2:-0644}"
  local dir tmp
  dir="$(dirname -- "$target")"
  mkdir -p -- "$dir" || return 1
  tmp="$(mktemp "${dir}/.phpx.tmp.XXXXXX")" || return 1
  if ! cat >"$tmp"; then
    rm -f -- "$tmp"
    return 1
  fi
  chmod "$mode" "$tmp" || { rm -f -- "$tmp"; return 1; }
  mv -f -- "$tmp" "$target"
}

bounded_curl() {
  curl --fail --location --silent --show-error --retry 3 \
    --connect-timeout 10 --max-time 120 "$@"
}

verify_sha384() {
  local file="$1" expected="$2" actual
  [[ "$expected" =~ ^[A-Fa-f0-9]{96}$ ]] || return 1
  if command -v sha384sum >/dev/null 2>&1; then
    actual="$(sha384sum -- "$file" | awk '{print $1}')"
  elif command -v openssl >/dev/null 2>&1; then
    actual="$(openssl dgst -sha384 "$file" | awk '{print $NF}')"
  elif command -v php >/dev/null 2>&1; then
    actual="$(php -r 'echo hash_file("sha384", $argv[1]);' "$file")"
  else
    return 1
  fi
  [[ "${actual,,}" == "${expected,,}" ]]
}

validate_extension_name() {
  [[ "${1:-}" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]
}

validate_github_extension_spec() {
  [[ "${1:-}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(@[A-Za-z0-9._/-]+)?$ ]]
}
'''
if helpers_marker not in text:
    raise SystemExit('PHP validation marker not found')
text = text.replace(helpers_marker, helpers + '\n' + helpers_marker, 1)

replace_section(
    '################################################################################\n# Add Sury Repo if Needed (Ubuntu/Debian)\n################################################################################',
    '################################################################################\n# Get PHP Version\n################################################################################',
    r'''add_sury_repo_if_needed() {
  require_root_for "phpx sury" || return 1
  [[ "$(detect_package_manager)" == "apt" ]] || {
    echo -e "${RED}phpx sury is supported only by the APT backend.${NC}" >&2
    return 3
  }
  [[ -r /etc/os-release ]] || { echo -e "${RED}Cannot read /etc/os-release.${NC}" >&2; return 1; }

  # /etc/os-release is a root-owned system contract, not user configuration.
  # shellcheck disable=SC1091
  . /etc/os-release
  local detected_os="${ID,,}" detected_like="${ID_LIKE:-}" codename
  detected_like="${detected_like,,}"
  codename="${VERSION_CODENAME:-${UBUNTU_CODENAME:-}}"
  [[ "$codename" =~ ^[a-z0-9][a-z0-9.-]*$ ]] || {
    echo -e "${RED}Unable to determine a safe distribution codename.${NC}" >&2
    return 1
  }

  package_install ca-certificates curl >/dev/null || return 1

  if [[ "$detected_os" == ubuntu || "$detected_like" == *ubuntu* ]]; then
    command -v add-apt-repository >/dev/null 2>&1 || package_install software-properties-common >/dev/null || return 1
    if ! grep -RqsE '^[[:space:]]*deb .*ondrej/php' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null; then
      echo -e "${YELLOW}Adding Ondřej PHP PPA for ${codename}.${NC}"
      timeout 120 add-apt-repository -y ppa:ondrej/php 2>&1 | show_last_lines || return 1
      unset _PHPX_APT_UPDATED
      apt_update_once || return 1
    fi
  elif [[ "$detected_os" == debian || "$detected_like" == *debian* ]]; then
    bounded_curl --head "https://packages.sury.org/php/dists/${codename}/Release" >/dev/null || {
      echo -e "${RED}Sury does not publish PHP metadata for '${codename}'.${NC}" >&2
      return 4
    }

    if ! grep -RqsE '^[[:space:]]*deb .*packages\.sury\.org/php' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null; then
      local tmp_dir keyring_pkg source_line
      tmp_dir="$(mktemp -d)" || return 1
      trap 'rm -rf -- "$tmp_dir"' RETURN
      keyring_pkg="$tmp_dir/debsuryorg-archive-keyring.deb"
      bounded_curl 'https://packages.sury.org/debsuryorg-archive-keyring.deb' --output "$keyring_pkg" || return 1
      [[ "$(dpkg-deb -f "$keyring_pkg" Package 2>/dev/null || true)" == debsuryorg-archive-keyring ]] || {
        echo -e "${RED}Downloaded Sury keyring package identity check failed.${NC}" >&2
        return 1
      }
      dpkg -i -- "$keyring_pkg" 2>&1 | show_last_lines || return 1
      source_line="deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ ${codename} main"
      printf '%s\n' "$source_line" | atomic_write_file /etc/apt/sources.list.d/php.list 0644 || return 1
      unset _PHPX_APT_UPDATED
      apt_update_once || return 1
    fi
  else
    echo -e "${RED}Unsupported distribution for phpx sury: ${detected_os}.${NC}" >&2
    return 3
  fi

  log_action INFO "PHP package repository is configured for ${detected_os} (${codename})."
}''')

replace_section(
    '################################################################################\n# Install PHP Version\n################################################################################',
    '################################################################################\n# Configure Web Server\n################################################################################',
    r'''install_php_version() {
  require_root_for "install PHP" || return 1
  local version="$1"
  validate_php_version "$version"
  [[ "$(detect_package_manager)" == apt ]] || {
    echo -e "${RED}Versioned PHP installation is currently implemented only for the APT backend.${NC}" >&2
    return 3
  }

  local packages_to_install=() package
  for package in "php$version" "php$version-cli" "php$version-fpm"; do
    package_installed "$package" || packages_to_install+=("$package")
  done
  ((${#packages_to_install[@]})) || {
    echo -e "${GREEN}All core packages for PHP $version are already installed.${NC}"
    return 0
  }

  echo -e "${YELLOW}Installing PHP $version packages: ${packages_to_install[*]}${NC}"
  package_install "${packages_to_install[@]}" 2>&1 | show_last_lines || return 1
  log_action INFO "Installed PHP $version packages: ${packages_to_install[*]}."
}''')

# APT-specific extension management must advertise its backend instead of guessing distro package names.
text = text.replace(
    'install_php_extensions() {\n  require_sudo\n',
    'install_php_extensions() {\n  require_root_for "install PHP extensions" || return 1\n  [[ "$(detect_package_manager)" == apt ]] || { echo -e "${RED}Versioned PHP extension packages currently require the APT backend.${NC}" >&2; return 3; }\n',
    1,
)
text = text.replace('  if ! dpkg -l | grep -q "^ii  php$version "; then', '  if ! package_installed "php$version"; then', 1)
text = text.replace('  apt_update_once\n  if ! apt install -y "${extensions_to_install[@]}" 2>&1 | show_last_lines; then', '  if ! package_install "${extensions_to_install[@]}" 2>&1 | show_last_lines; then', 1)

replace_section(
    '################################################################################\n# Install Composer\n################################################################################',
    '################################################################################\n# Install PECL Packages\n################################################################################',
    r'''install_composer() {
  require_root_for "install Composer" || return 1
  local do_update=0
  while (($#)); do
    case "$1" in
    --update) do_update=1 ;;
    --no-update) do_update=0 ;;
    *) echo -e "${RED}Unknown Composer option: $1${NC}" >&2; return 2 ;;
    esac
    shift
  done

  command -v php >/dev/null 2>&1 || { echo -e "${RED}PHP is required to install Composer.${NC}" >&2; return 1; }
  if ! command -v curl >/dev/null 2>&1; then
    package_install curl >/dev/null || { echo -e "${RED}curl is required to install Composer.${NC}" >&2; return 1; }
  fi

  if command -v composer >/dev/null 2>&1; then
    echo -e "${GREEN}Composer is already installed: $(composer --version 2>/dev/null | head -n1)${NC}"
    if ((do_update)); then
      composer self-update --stable --no-interaction || return 1
    else
      echo "Use 'phpx install composer --update' to explicitly update the installed Composer binary."
    fi
    return 0
  fi

  local tmp_dir installer signature
  tmp_dir="$(mktemp -d)" || return 1
  trap 'rm -rf -- "$tmp_dir"' RETURN
  installer="$tmp_dir/composer-setup.php"
  bounded_curl 'https://getcomposer.org/installer' --output "$installer" || return 1
  signature="$(bounded_curl 'https://composer.github.io/installer.sig')" || return 1
  verify_sha384 "$installer" "$signature" || {
    echo -e "${RED}Composer installer SHA-384 verification failed.${NC}" >&2
    return 1
  }

  php "$installer" --quiet --install-dir="$tmp_dir" --filename=composer || return 1
  php "$tmp_dir/composer" --version >/dev/null 2>&1 || return 1
  install -m 0755 -- "$tmp_dir/composer" /usr/local/bin/composer || return 1
  echo -e "${GREEN}Composer installed with verified upstream installer.${NC}"
  log_action INFO 'Composer installed after SHA-384 installer verification.'
}''')

replace_section(
    '################################################################################\n# Install PECL Packages\n################################################################################',
    '################################################################################\n# Serve (PHP Built-In Server)\n################################################################################',
    r'''install_pecl_package() {
  require_root_for "install PECL extensions" || return 1
  (($#)) || { echo -e "${RED}No PECL packages specified.${NC}" >&2; return 2; }
  [[ "$(detect_package_manager)" == apt ]] || {
    echo -e "${RED}Automatic PECL build dependency installation currently requires the APT backend.${NC}" >&2
    return 3
  }

  local package_list=() token p failures=0
  for token in "$@"; do
    IFS=',' read -r -a parts <<<"$token"
    for p in "${parts[@]}"; do
      p="${p//[[:space:]]/}"
      [[ -z "$p" ]] && continue
      validate_extension_name "$p" || { echo -e "${RED}Invalid PECL package name: $p${NC}" >&2; return 2; }
      package_list+=("$p")
    done
  done

  command -v pecl >/dev/null 2>&1 || package_install php-pear php-dev 2>&1 | show_last_lines || return 1
  command -v pecl >/dev/null 2>&1 || { echo -e "${RED}PECL is unavailable after dependency installation.${NC}" >&2; return 1; }

  for p in "${package_list[@]}"; do
    if pecl list 2>/dev/null | awk 'NR>3 {print $1}' | grep -Fxq "$p"; then
      echo -e "${GREEN}$p is already installed.${NC}"
      continue
    fi
    printf '\n' | pecl install "$p" || { failures=$((failures + 1)); continue; }
    echo -e "${GREEN}$p installed successfully.${NC}"
  done
  ((failures == 0))
}''')

# Replace the native extension installer with validated specs, private temp state,
# owned-INI semantics, atomic writes and rollback of a pre-existing module binary.
replace_section(
    '# Source/PECL/GitHub extension installer (native, no phpbrew)',
    '# FPM command suite',
    r'''phpx_ext_src() {
  require_root_for "phpx ext-src" || return 1
  [[ "$(detect_package_manager)" == apt ]] || { echo -e "${RED}phpx ext-src currently requires the APT backend.${NC}" >&2; return 3; }

  local action="${1:-}"; shift || true
  local version="" enable=1
  while (($#)); do
    case "$1" in
    --php=*) version="${1#*=}"; shift ;;
    --php) shift; version="${1:-}"; shift || true ;;
    --no-enable) enable=0; shift ;;
    *) break ;;
    esac
  done
  [[ -n "$version" ]] || version="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;' 2>/dev/null || true)"
  validate_php_version "$version"
  local ext="${1:-}"
  [[ -n "$ext" ]] || { echo -e "${RED}Usage: phpx ext-src <install|uninstall> <pecl-name|github:org/repo[@ref]> [--php X.Y] [--no-enable]${NC}" >&2; return 2; }
  [[ "$action" == install || "$action" == uninstall || "$action" == remove ]] || { echo -e "${RED}Unknown action: $action${NC}" >&2; return 2; }

  install_php_version "$version" || return 1
  package_install git build-essential autoconf pkg-config "php${version}-dev" php-pear 2>&1 | show_last_lines || return 1

  local phpbin phpconfig phpize ext_dir mods_avail name ini_file
  phpbin="$(find_php_binary "$version")" || return 1
  phpconfig="$(command -v "php-config${version}" 2>/dev/null || true)"
  phpize="$(command -v "phpize${version}" 2>/dev/null || true)"
  [[ -n "$phpconfig" && -n "$phpize" ]] || { echo -e "${RED}phpize/php-config for PHP $version are required.${NC}" >&2; return 1; }
  ext_dir="$($phpconfig --extension-dir 2>/dev/null)"
  mods_avail="/etc/php/${version}/mods-available"

  if [[ "$ext" == github:* ]]; then
    local spec="${ext#github:}" ref=""
    validate_github_extension_spec "$spec" || { echo -e "${RED}Invalid GitHub extension spec.${NC}" >&2; return 2; }
    if [[ "$spec" == *@* ]]; then ref="${spec##*@}"; spec="${spec%%@*}"; fi
    name="${spec##*/}"
  else
    validate_extension_name "$ext" || { echo -e "${RED}Invalid extension name: $ext${NC}" >&2; return 2; }
    name="${ext%%-*}"
  fi
  ini_file="${mods_avail}/${name}.ini"

  if [[ "$action" != install ]]; then
    phpdismod -v "$version" "$name" >/dev/null 2>&1 || true
    if [[ -f "$ini_file" ]] && grep -Fq '; generated by phpx ext-src' "$ini_file"; then rm -f -- "$ini_file"; fi
    echo -e "${GREEN}Disabled $name; only phpx-owned INI metadata was removed.${NC}"
    return 0
  fi

  local tmp_dir backup_so="" installed_so="${ext_dir}/${name}.so"
  tmp_dir="$(mktemp -d)" || return 1
  trap 'rm -rf -- "$tmp_dir"' RETURN
  if [[ -f "$installed_so" ]]; then backup_so="$tmp_dir/original.so"; cp -a -- "$installed_so" "$backup_so"; fi

  if [[ "$ext" == github:* ]]; then
    local clone_dir="$tmp_dir/src" repo_url="https://github.com/${spec}.git"
    if [[ -n "$ref" ]]; then
      git clone --depth 1 --branch "$ref" -- "$repo_url" "$clone_dir" 2>&1 | show_last_lines || return 1
    else
      git clone --depth 1 -- "$repo_url" "$clone_dir" 2>&1 | show_last_lines || return 1
    fi
    (cd "$clone_dir" && "$phpize" >/dev/null && ./configure --with-php-config="$phpconfig" >/dev/null && make -j"$(nproc 2>/dev/null || echo 2)" >/dev/null && make install >/dev/null) || {
      [[ -n "$backup_so" ]] && cp -a -- "$backup_so" "$installed_so"
      return 1
    }
  else
    printf '\n' | "$phpbin" "$(command -v pecl)" install "$ext" 2>&1 | show_last_lines || return 1
    local matched
    matched="$(find "$ext_dir" -maxdepth 1 -type f -name "${name}*.so" -print -quit 2>/dev/null || true)"
    [[ -n "$matched" ]] && installed_so="$matched"
  fi

  if ((enable)); then
    mkdir -p -- "$mods_avail" || return 1
    if ! printf '; generated by phpx ext-src\nextension=%s\n' "$(basename -- "$installed_so")" | atomic_write_file "$ini_file" 0644; then
      [[ -n "$backup_so" ]] && cp -a -- "$backup_so" "${ext_dir}/${name}.so"
      return 1
    fi
    phpenmod -v "$version" "$name" >/dev/null 2>&1 || {
      rm -f -- "$ini_file"
      [[ -n "$backup_so" ]] && cp -a -- "$backup_so" "${ext_dir}/${name}.so"
      return 1
    }
    service_is_active "php${version}-fpm" && service_action reload "php${version}-fpm" >/dev/null 2>&1 || true
  fi
  echo -e "${GREEN}Installed extension $name for PHP $version.${NC}"
}''')

replace_section(
    '################################################################################\n# Config Generator\n################################################################################',
    '################################################################################\n# Trap for Interrupts\n################################################################################',
    r'''generate_php_config() {
  local environment="${1,,}" version="$2"
  [[ "$environment" == production || "$environment" == development ]] || { echo "Invalid environment: $environment" >&2; return 2; }
  validate_php_version "$version"

  local total_mem max_children start_servers min_spare max_spare
  total_mem="$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')"
  [[ "$total_mem" =~ ^[0-9]+$ ]] || total_mem=1024
  max_children=$((total_mem / 40)); ((max_children < 5)) && max_children=5; ((max_children > 512)) && max_children=512
  start_servers=$((max_children / 5)); ((start_servers < 1)) && start_servers=1
  min_spare=$((max_children / 6)); ((min_spare < 1)) && min_spare=1
  max_spare=$((max_children / 3)); ((max_spare < 1)) && max_spare=1

  local fpm_path="./fpm.${environment}.conf" ini_path="./php.${environment}.ini"
  local fpm_tmp ini_tmp
  fpm_tmp="$(mktemp ./.phpx-fpm.XXXXXX)" || return 1
  ini_tmp="$(mktemp ./.phpx-ini.XXXXXX)" || { rm -f -- "$fpm_tmp"; return 1; }
  trap 'rm -f -- "$fpm_tmp" "$ini_tmp"' RETURN

  cat >"$fpm_tmp" <<EOF
; Auto-generated PHP-FPM pool config for $environment
[www]
pm = dynamic
pm.max_children = $max_children
pm.start_servers = $start_servers
pm.min_spare_servers = $min_spare
pm.max_spare_servers = $max_spare
pm.max_requests = 500
catch_workers_output = yes
access.log = /var/log/php${version}-fpm.${environment}.access.log
slowlog = /var/log/php${version}-fpm.${environment}.slow.log
request_slowlog_timeout = $([[ "$environment" == production ]] && echo 3s || echo 2s)
EOF

  local validate_ts revalidate jit_mode jit_buffer opcache_mem accel exec_time upload
  if [[ "$environment" == production ]]; then
    validate_ts=0; revalidate=0; jit_mode=tracing; jit_buffer=256M; opcache_mem=256; accel=20000; exec_time=30; upload=100M
  else
    validate_ts=1; revalidate=1; jit_mode=function; jit_buffer=128M; opcache_mem=128; accel=8000; exec_time=90; upload=200M
  fi
  cat >"$ini_tmp" <<EOF
; Auto-generated php.ini for $environment
memory_limit = 512M
max_execution_time = $exec_time
max_input_time = $exec_time
post_max_size = $upload
upload_max_filesize = $upload
error_reporting = E_ALL
display_errors = $([[ "$environment" == production ]] && echo Off || echo On)
log_errors = On
error_log = /var/log/php_errors.${environment}.log
realpath_cache_size = 512K
realpath_cache_ttl = 600
[opcache]
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=$opcache_mem
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=$accel
opcache.validate_timestamps=$validate_ts
opcache.revalidate_freq=$revalidate
opcache.save_comments=1
opcache.jit_buffer_size=$jit_buffer
opcache.jit=$jit_mode
EOF

  grep -Fqx '[www]' "$fpm_tmp" && grep -Eq '^pm\.max_children = [0-9]+$' "$fpm_tmp" || return 1
  local phpbin
  phpbin="$(find_php_binary "$version" 2>/dev/null || find_php_binary 2>/dev/null || true)"
  if [[ -n "$phpbin" ]]; then "$phpbin" -c "$ini_tmp" -r 'exit(0);' >/dev/null 2>&1 || return 1; fi

  chmod 0644 "$fpm_tmp" "$ini_tmp" || return 1
  mv -f -- "$fpm_tmp" "$fpm_path" || return 1
  mv -f -- "$ini_tmp" "$ini_path" || return 1
  echo "PHP config generated for $environment ($version):"
  echo " - FPM: $fpm_path"
  echo " - INI: $ini_path"
}''')

# Composer options must reach the installer function.
text = text.replace('  composer)\n    install_composer\n    ;;', '  composer)\n    shift\n    install_composer "$@"\n    ;;', 1)

# Library mode allows unit-level safety tests without executing dispatch.
main_marker = '################################################################################\n# Main Script Execution\n################################################################################\n'
if 'PHPX_LIBRARY_MODE' not in text[text.find(main_marker):text.find(main_marker)+500]:
    text = text.replace(main_marker, main_marker + 'if [[ "${PHPX_LIBRARY_MODE:-0}" == "1" ]]; then\n  return 0 2>/dev/null || exit 0\nfi\n\n', 1)

path.write_text(text)
