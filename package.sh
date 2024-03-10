#!/bin/bash
# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

set -euxo pipefail

readonly NC='\033[0m'
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'

readonly addon_name=ajt_cropro
readonly manifest=manifest.json
readonly root_dir=$(git rev-parse --show-toplevel)
readonly branch=$(git branch --show-current)
readonly zip_name=${addon_name}_${branch}.ankiaddon
readonly target=${1:-ankiweb} # ankiweb or github
export root_dir branch

check_installed() {
	for exe in git zip zipmerge; do
		if ! command -v "$exe" >/dev/null; then
			echo -e "${RED}Missing dependency:${NC} $exe"
			exit 1
		fi
	done
}

git_archive() {
	run_archive() {
		git archive "$branch" --format=zip --output "$zip_name" "$@"
	}

	if [[ $target != ankiweb && $target != aw ]]; then
		# https://addon-docs.ankiweb.net/sharing.html#sharing-outside-ankiweb
		# If you wish to distribute .ankiaddon files outside of AnkiWeb,
		# your add-on folder needs to contain a ‘manifest.json’ file.
		echo "Creating $manifest"
		cat <<-EOF >"$manifest"
			{
			  "package": "CroPro",
			  "name": "Cross Profile Search and Import",
			  "mod": $(date -u '+%s')
			}
		EOF
		run_archive --add-file="$manifest"
	else
		run_archive
	fi
}

main() {
	check_installed

	cd -- "$root_dir" || exit 1
	rm -v -- ./*.ankiaddon 2>/dev/null || true

	git_archive

	# shellcheck disable=SC2016
	git submodule foreach 'git archive HEAD --prefix="${sm_path}/" --format=zip --output "${root_dir}/${sm_path}_${sha1}.zip"'

	zipmerge ./"$zip_name" ./*.zip
	rm -v -- ./*.zip ./"$manifest" 2>/dev/null || true
	echo -e "${GREEN}Done.${NC}"
}

main "$@"
