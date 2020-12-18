#!/bin/bash

readonly archive=cropro.ankiaddon
readonly manifest=manifest.json
readonly target=${*:-ankiweb}

rm -- $archive 2>/dev/null

if [[ $target != 'ankiweb' ]]; then
    # https://addon-docs.ankiweb.net/#/sharing?id=sharing-outside-ankiweb
    # If you wish to distribute .ankiaddon files outside of AnkiWeb,
    # your add-on folder needs to contain a ‘manifest.json’ file.
    {
        echo '{'
        echo -e '\t"package": "CroPro",'
        echo -e '\t"name": "Cross Profile Search and Import",'
        echo -e "\t\"mod\": $(date -u '+%s')"
        echo '}'
    } > $manifest
fi

zip -r $archive -- ./*.py ./*.json
rm -- $manifest 2>/dev/null
