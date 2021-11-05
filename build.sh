#!/usr/bin/env bash
# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

readonly addon_name=ajt_cropro
readonly manifest=manifest.json
readonly root_dir=$(git rev-parse --show-toplevel)
readonly branch=${1:-$(git branch --show-current)}
readonly zip_name=${addon_name}_${branch}.ankiaddon
export root_dir branch

ask_target() {
	local target
	read -r target
	echo "$target"
}

git_archive() {
	echo -n "Enter target [ankiweb/else]: "
	if [[ $(ask_target) != 'ankiweb' ]]; then
		# https://addon-docs.ankiweb.net/sharing.html#sharing-outside-ankiweb
		# If you wish to distribute .ankiaddon files outside of AnkiWeb,
		# your add-on folder needs to contain a ‘manifest.json’ file.
		echo "Creating $manifest"
		{
			echo '{'
			echo -e '\t"package": "CroPro",'
			echo -e '\t"name": "Cross Profile Search and Import",'
			echo -e "\t\"mod\": $(date -u '+%s')"
			echo '}'
		} >"$manifest"
		git archive "$branch" --format=zip --output "$zip_name" --add-file="$manifest"
	else
		git archive "$branch" --format=zip --output "$zip_name"
	fi
}

cd -- "$root_dir" || exit 1
rm -- ./"$zip_name"

git_archive

# shellcheck disable=SC2016
git submodule foreach 'git archive HEAD --prefix=$path/ --format=zip --output "$root_dir/${path}_${branch}.zip"'

zipmerge ./"$zip_name" ./*.zip
rm -- ./*.zip ./"$manifest"
